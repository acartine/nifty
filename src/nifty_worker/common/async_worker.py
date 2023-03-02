import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, TypeVar

from redis.asyncio.client import Redis

from nifty_common.redis_helpers import get_redis_async
from nifty_common.types import Channel, RedisType
from .claim import async_claim
from .worker import BaseNiftyWorker

T = TypeVar('T')


class AsyncNiftyWorker(BaseNiftyWorker[T], ABC):
    def __init__(self):
        super().__init__()
        self.__redis: Optional[Redis] = None

    @abstractmethod
    async def on_event(self, channel: Channel, msg: T):
        ...

    @abstractmethod
    async def on_yield(self):
        """
        Called when listen interval expires
        Override this when you want to do clean up or scheduled tasks
        :return: None
        """
        ...

    def redis(self) -> Redis:
        if not self.__redis:
            self.__redis = get_redis_async(RedisType.STD)
        return self.__redis

    async def __handle(self, channel: Channel, msg: Dict[str, any]):
        logging.getLogger(__name__).debug('handle entered')
        if not msg:
            logging.getLogger(__name__).debug('entering yield')
            await self.on_yield()
            logging.getLogger(__name__).debug('exiting yield')
            return

        event = self.unpack(msg)
        if self.filter(event):
            logging.getLogger(__name__).debug(event)
            claimed = await async_claim(self.redis(), f"{self.__class__}:{event.uuid}", 60)
            if claimed:
                await self.on_event(channel, event)

    async def run(self, *, src_channel: Channel, listen_interval: Optional[int] = 5):
        logging.getLogger(__name__).debug('initializing')
        self.before_start()
        redis = get_redis_async(RedisType.STD)  # STD does not have LRU memory limit
        async with redis.pubsub(ignore_subscribe_messages=True) as pubsub:
            await pubsub.subscribe(src_channel)
            self.running = True
            while self.running:
                logging.getLogger(__name__).debug('entering get_message')
                msg = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=listen_interval)
                logging.getLogger(__name__).debug(f"exiting get_message with {msg}")
                await self.__handle(src_channel, msg)
