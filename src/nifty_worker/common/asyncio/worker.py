import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, TypeVar

from redis.asyncio.client import Redis

from nifty_common.asyncio import redis_helpers
from nifty_common.types import Channel, RedisType
from nifty_worker.common.asyncio import claim
from nifty_worker.common.worker import BaseNiftyWorker

T = TypeVar('T')


class NiftyWorker(BaseNiftyWorker[T], ABC):
    def __init__(self):
        super().__init__()
        self.__redis: Optional[Redis] = None

    async def before_start(self):
        ...

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
            self.__redis = redis_helpers.get_redis(RedisType.STD)
        return self.__redis

    async def __handle(self, channel: Channel, msg: Dict[str, any]):
        if not msg:
            await self.on_yield()
            return

        event = self.unpack(msg)
        if self.filter(event):
            logging.debug(event)
            claimed = await claim.claim(self.redis(), f"{self.__class__}:{event.uuid}", 60)
            if claimed:
                await self.on_event(channel, event)

    async def run(self, *, src_channel: Channel, listen_interval: Optional[int] = 5):
        await self.before_start()
        redis = redis_helpers.get_redis(RedisType.STD)  # STD does not have LRU memory limit
        async with redis.pubsub(ignore_subscribe_messages=True) as pubsub:
            await pubsub.subscribe(src_channel)
            self.running = True
            while self.running:
                msg = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=listen_interval)
                await self.__handle(src_channel, msg)
