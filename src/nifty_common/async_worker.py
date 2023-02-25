import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from redis.asyncio.client import Redis

from nifty_common.claim import async_claim
from nifty_common.helpers import get_redis_async
from nifty_common.worker import BaseNiftyWorker, T


class AsyncNiftyWorker(BaseNiftyWorker[T], ABC):
    def __init__(self):
        super().__init__(self)

    @abstractmethod
    async def on_event(self, msg: T):
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
            self.__redis = get_redis_async()
        return self.__redis

    async def __handle(self, msg: Dict[str, any]):
        if not msg:
            await self.on_yield()
            return

        event = self.unpack(msg)
        if self.filter(event):
            logging.getLogger(__name__).debug(event)
            if await async_claim(self.redis(), f"{self.__class__}:{event.uuid}", 60):
                await self.on_event(event)

    def run(self, *, src_channel: str, listen_interval: Optional[int] = 5):
        self.before_start()
        redis = get_redis_async()  # docs say to use diff reais for read, not sure this is true
        async with redis.pubsub(ignore_subscribe_messages=True) as pubsub:
            await pubsub.subscribe(src_channel)
            self.running = True
            while self.running:
                await self.__handle(
                    await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=listen_interval))
