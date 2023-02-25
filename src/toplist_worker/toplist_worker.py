import logging
import sys
from typing import Dict, NamedTuple, Optional, Set
from uuid import uuid1

from nifty_common.config import cfg
from nifty_common.constants import REDIS_TRENDING_KEY, REDIS_TRENDING_SIZE_KEY
from nifty_common.helpers import none_throws, timestamp_ms, trending_size
from nifty_common.types import Action, ActionType, Channel, TrendEvent
from nifty_common.worker import NiftyWorker, init_logger
from toplist import AbstractTopList, RedisTopList

init_logger()


# redis doesn't really have great datastructures for this
# time series would have been best, but it doesn't support
# dynamic labels or aggregations limits in order

# we can run multiples of these in parallel for reliability
# they will overwrite each other but we don't need it to be exact

class TopLink(NamedTuple):
    id: int
    short_url: str
    long_url: str


class ToplistWorker(NiftyWorker[Action]):

    def __init__(self):
        super().__init__()
        self._toplist: Optional[AbstractTopList] = None

    def toplist(self) -> AbstractTopList:
        return none_throws(
            self._toplist,
            "self._toplist is not set - did you start the worker?")

    def __set_size(self):
        newsize = cfg.getint('trending', 'size')
        with self.redis().pipeline() as pipe:
            pipe.watch(REDIS_TRENDING_SIZE_KEY)
            cursize = trending_size(pipe, throws=False)
            if newsize != cursize:
                pipe.multi()
                pipe.set(REDIS_TRENDING_SIZE_KEY, newsize).execute()

    def before_start(self):
        self.__set_size()

        def on_toplist_change(added: Set[str], removed: Set[str]):
            logging.debug(f"Added: {added}  Removed: {removed}")
            self.redis().publish(
                Channel.trending,
                TrendEvent(
                    uuid=str(uuid1()),
                    at=timestamp_ms(),
                    added=added,
                    removed=removed).json())

        self._toplist = RedisTopList(
            REDIS_TRENDING_KEY,
            cfg.getint('trending', 'interval_sec'),
            self.redis(),
            listener=on_toplist_change,
            ctor=str,
            bucket_len_sec=cfg.getint('trending', 'bucket_len_sec'))

    def unpack(self, msg: Dict[str, any]) -> Action:
        return Action.parse_raw(msg['data'])

    def filter(self, msg: Action) -> bool:
        return msg.type == ActionType.get

    def on_event(self, msg: Action):
        self.toplist().incr(msg.short_url, min(msg.at, timestamp_ms()))

    def on_yield(self):
        self.toplist().reap(timestamp_ms())


if __name__ == '__main__':
    ToplistWorker().run(
        src_channel=Channel.action,
        listen_interval=cfg.getint('trending', 'listen_interval_sec'))
