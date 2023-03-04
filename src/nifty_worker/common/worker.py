import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from redis.client import Redis

from nifty_common.redis_helpers import get_redis
from nifty_common.types import Channel, Meta, RedisType
from .claim import claim

T_Worker = TypeVar('T_Worker', bound=Meta)


class BaseNiftyWorker(Generic[T_Worker], ABC):
    """
    Consumes Redis Pubsub events and (optionally) publishes or
    stores transformations
    """

    def __init__(self):
        self.running = False

    @abstractmethod
    def unpack(self, msg: Dict[str, Any]) -> T_Worker:
        ...

    def filter(self, _msg: T_Worker) -> bool:
        return True


class NiftyWorker(BaseNiftyWorker[T_Worker], ABC):
    def __init__(self):
        super().__init__()
        self.__redis: Optional[Redis] = None

    @abstractmethod
    def on_event(self, channel: Channel, msg: T_Worker):
        ...

    def before_start(self):
        ...

    def on_yield(self):
        """
        Called when listen interval expires
        Override this when you want to do clean up or scheduled tasks
        :return: None
        """
        ...

    def redis(self) -> Redis:
        if not self.__redis:
            self.__redis = get_redis(RedisType.STD)
        return self.__redis

    def __handle(self, channel: Channel, msg: Dict[str, Any]):
        if not msg:
            self.on_yield()
            return

        event = self.unpack(msg)
        if self.filter(event):
            logging.getLogger(__name__).debug(event)
            if claim(self.redis(), f"{self.__class__}:{event.uuid}", 60):
                self.on_event(channel, event)

    def run(self, *, src_channel: Channel, listen_interval: Optional[int]):
        self.before_start()
        redis = get_redis(RedisType.STD)  # docs say to use diff reais for read, not sure this is true
        pubsub = redis.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(src_channel)
        self.running = True
        while self.running:
            self.__handle(
                src_channel,

                # redis uses 'dict' instead of 'Dict' which is causing this error
                # suppressing pyright means we can avoid deprecated types in our api
                pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=listen_interval if listen_interval else 5)) # pyright: reportGeneralTypeIssues=false
