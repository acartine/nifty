import logging
from abc import ABC, abstractmethod
from typing import Dict, Generic, Optional, TypeVar

from redis.client import Redis

from nifty_common.claim import claim
from nifty_common.helpers import get_redis, none_throws
from nifty_common.types import Meta

T = TypeVar('T', bound=Meta)


class NiftyWorker(Generic[T], ABC):
    """
    Consumes Redis Pubsub events and (optionally) publishes or
    stores transformations
    """
    def __init__(self):
        self.running = False
        self._redis: Optional[Redis] = None

    def before_start(self):
        """
        Called after Redis is opened and before the listening starts
        Override this if you need to initialize things
        :return: None
        """
        ...

    @abstractmethod
    def unpack(self, msg: Dict[str, any]) -> T:
        ...

    def filter(self, _msg: T) -> bool:
        return True

    @abstractmethod
    def on_event(self, msg: T):
        ...

    def on_yield(self):
        """
        Called when listen interval expires
        Override this when you want to do clean up or scheduled tasks
        :return: None
        """
        ...

    def redis(self) -> Redis:
        return none_throws(self._redis,
                           "self._redis not set = did you start the worker?")

    def handle(self, msg: Dict[str, any]):
        if not msg:
            self.on_yield()
            return
        
        event = self.unpack(msg)
        if self.filter(event):
            logging.getLogger(__name__).debug(event)
            if claim(self.redis(), f"{self.__class__}:{event.uuid}", 60):
                self.on_event(event)

    def run(self, *, src_channel: str, listen_interval: Optional[int] = 5):
        self._redis = get_redis()
        self.before_start()
        redis = get_redis()  # docs say to use diff reais for read, not sure this is true
        pubsub = redis.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(src_channel)
        self.running = True
        while self.running:
            self.handle(
                pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=listen_interval))
