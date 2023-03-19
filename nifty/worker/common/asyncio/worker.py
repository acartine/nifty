# fixes stubs like redis that use generics when the code does not
from __future__ import annotations
from asyncio import CancelledError

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
import aiorun
from redis.asyncio.client import Redis, PubSub
from nifty.common import log

from nifty.common.asyncio import redis_helpers
from nifty.common.types import Channel, RedisType
from nifty.worker.common.asyncio import claim
from nifty.worker.common.types import ClaimNamespace
from nifty.worker.common.worker import BaseNiftyWorker, T_Worker


class NiftyWorker(BaseNiftyWorker[T_Worker], ABC):
    def __init__(self, claim_namespace: ClaimNamespace):
        super().__init__()
        self.__redis: Optional[Redis[str]] = None
        self.__claim_namespace = claim_namespace

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

    def redis(self) -> Redis[str]:
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
            claimed = await claim.claim(
                self.redis(), self.__claim_namespace, event.uuid
            )
            if claimed:
                await self.on_event(channel, event)

    async def __listen(
        self, pubsub: PubSub, src_channel: Channel, listen_interval: float
    ):
        while True:
            logging.debug(f"Listening to {src_channel} for {listen_interval} seconds")
            msg: Dict[
                str, Any
            ] = await pubsub.get_message(  # pyright: ignore [reportUnknownMemberType]
                ignore_subscribe_messages=True,
                timeout=listen_interval if listen_interval else 5,
            )
            try:
                # TODO probably should do something smater here if we've already pulled the message
                await self.__handle(src_channel, msg)
            except CancelledError:
                logging.info("Cancelled")
                break

    async def run(
        self, *, src_channel: Channel, listen_interval: Optional[float] = 0.5
    ):
        try:
            if listen_interval is None or listen_interval <= 0:
                raise Exception("You must set listen_interval > 0")
            await self.before_start()
            redis = redis_helpers.get_redis(
                RedisType.STD
            )  # STD does not have LRU memory limit
            async with redis.pubsub(  # pyright: ignore [reportUnknownMemberType]
                ignore_subscribe_messages=True
            ) as pubsub:
                await pubsub.subscribe(  # pyright: ignore [reportUnknownMemberType]
                    src_channel
                )
                logging.debug(f"Subscribed to {src_channel}")
                await self.__listen(pubsub, src_channel, listen_interval)
        except CancelledError:
            logging.info("Cancelled")


def start(worker_ctor: Callable[[], NiftyWorker[T_Worker]], src_channel: Channel):
    """
    Starts the worker
    """
    log.init()
    aiorun.run(worker_ctor().run(src_channel=src_channel))
