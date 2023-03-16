import logging
from typing import Any, Dict, Optional, Set
from uuid import uuid1
from nifty.common import cfg, context

from nifty.common.helpers import none_throws, timestamp_ms
from nifty.common.asyncio import redis_helpers
from nifty.common.types import Action, ActionType, Channel, Key, TrendEvent
from .common.asyncio.worker import NiftyWorker
from .common.types import ClaimNamespace
from .toplist.asyncio.toplist import AbstractTopList, RedisTopList
from .common.asyncio import worker

# redis doesn't really have great datastructures for this
# time series would have been best, but it doesn't support
# dynamic labels or aggregations limits in order

# we can run multiples of these in parallel for reliability
# they will overwrite each other but we don't need it to be exact


class TrendWorker(NiftyWorker[Action]):
    def __init__(
        self, *, trend_size: int, toplist_interval_sec: int, toplist_bucket_len_sec: int
    ):
        super().__init__(ClaimNamespace.trend)
        self._toplist: Optional[AbstractTopList[int]] = None
        self.trend_size = trend_size
        self.toplist_interval_sec = toplist_interval_sec
        self.toplist_bucket_len_sec = toplist_bucket_len_sec

    def toplist(self) -> AbstractTopList[int]:
        return none_throws(
            self._toplist, "self._toplist is not set - did you start the worker?"
        )

    async def __set_size(self):
        newsize = self.trend_size
        async with self.redis().pipeline() as pipe:
            await pipe.watch(Key.trending_size)
            cursize = await redis_helpers.trending_size(pipe, throws=False)
            if newsize != cursize:
                pipe.multi()
                # noinspection PyUnresolvedReferences
                await pipe.set(Key.trending_size, newsize).execute()

    async def before_start(self):
        await self.__set_size()

        async def on_toplist_change(added: Set[int], removed: Set[int]):
            logging.debug(f"Added: {added}  Removed: {removed}")
            await self.redis().publish(
                Channel.trend,
                TrendEvent(
                    uuid=str(uuid1()), at=timestamp_ms(), added=added, removed=removed
                ).json(),
            )

        self._toplist = RedisTopList[int](
            Key.trending,
            self.toplist_interval_sec,
            self.redis(),
            listener=on_toplist_change,
            ctor=int,
            bucket_len_sec=self.toplist_bucket_len_sec,
        )

    def unpack(self, msg: Dict[str, Any]) -> Action:
        return Action.parse_raw(msg["data"])

    def filter(self, msg: Action) -> bool:
        return msg.type == ActionType.get

    async def on_event(self, channel: Channel, msg: Action):
        await self.toplist().incr(msg.link_id, min(msg.at, timestamp_ms()))

    async def on_yield(self):
        now = timestamp_ms()
        tl = self.toplist()
        await tl.reap(now)


TREND_CONFIG_KEY = "trend"

if __name__ == "__main__":
    cfg.init(**context.get().dict())
    worker.start(
        lambda: TrendWorker(
            trend_size=cfg.gint(TREND_CONFIG_KEY, "size"),
            toplist_interval_sec=cfg.gint(TREND_CONFIG_KEY, "toplist_interval_sec"),
            toplist_bucket_len_sec=cfg.gint(TREND_CONFIG_KEY, "toplist_bucket_len_sec"),
        ),
        src_channel=Channel.action,
    )
