import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar

from redis.asyncio.client import Redis

from nifty_common.asyncio import redis_helpers
from nifty_common.types import Channel, RedisType
from nifty_worker.common.asyncio import claim
from nifty_worker.common.worker import BaseNiftyWorker, T_Worker



class NiftyWorker(BaseNiftyWorker[T_Worker], ABC):
    def __init__(self):
        super().__init__()
        self.__redis: Optional[Redis] = None

    async def before_start(self):
        ...

    @abstractmethod
    async def on_event(self, channel: Channel, msg: T_Worker):
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

    async def __handle(self, channel: Channel, msg: Dict[str, Any]):
        if not msg:
            await self.on_yield()
            return

        event = self.unpack(msg)
        if self.filter(event):
            logging.debug(event)
            claimed = await claim.claim(self.redis(), f"{self.__class__}:{event.uuid}", 60)
            if claimed:
                await self.on_event(channel, event)

    async def run(self, *, src_channel: Channel, listen_interval: Optional[int] = None):
        await self.before_start()
        redis = redis_helpers.get_redis(RedisType.STD)  # STD does not have LRU memory limit
        async with redis.pubsub(ignore_subscribe_messages=True) as pubsub:
            await pubsub.subscribe(src_channel)
            self.running = True
            while self.running:
                msg = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=listen_interval if listen_interval else 5)
                await self.__handle(src_channel, msg)
