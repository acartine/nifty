import abc
import logging
from abc import abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Generic, List, Optional, TypeVar, cast

from redis.client import Redis

from nifty_common.helpers import retry

T = TypeVar('T')
R = TypeVar('R')

_logger = logging.getLogger(__name__)


@dataclass
class Entry(Generic[T]):
    key: T
    count: int


class AbstractTopList(Generic[T], abc.ABC):

    def __init__(self,
                 max_age: int,
                 bucket_len_sec: Optional[int] = 1):
        self.max_age = max_age
        self.bucket_len_sec = bucket_len_sec

    @abstractmethod
    def incr(self, key: T, ts_ms: int):
        pass

    @abstractmethod
    def reap(self, ts: int):
        pass

    @abstractmethod
    def get(self, ts_ms: int, lim: Optional[int] = None) -> List[Entry[T]]:
        pass


class TopList(AbstractTopList[T]):

    def __init__(self, max_age: int, bucket_len_sec: Optional[int] = 1):
        super().__init__(max_age, bucket_len_sec)
        self.entries = {}
        self.ordered_entries = []
        self.buckets = OrderedDict()

    def reap(self, ts: int):
        ts_sec = int(ts / 1000)
        while len(self.buckets) > 0 and ts_sec - min(self.buckets) >= self.max_age:
            item = self.buckets.popitem(last=False)
            for key, count in item[1].items():
                self.__decr(key, count)

    def __sort(self):
        self.ordered_entries.sort(key=lambda e: e.count, reverse=True)

    def incr(self, key: T, ts_ms: int):
        self.reap(ts_ms)
        entry = self.entries.get(key)
        if not entry:
            entry = Entry(key, 0)
            self.entries[key] = entry
            self.ordered_entries.append(entry)
        entry.count += 1
        self.__sort()

        # put it in timebucket
        ts_secs = int(ts_ms / 1000)
        bucket_key = ts_secs - ts_secs % self.bucket_len_sec
        bucket = self.buckets.get(bucket_key)
        if not bucket:
            bucket = {}
            self.buckets[bucket_key] = bucket

        if key not in bucket:
            bucket[key] = 0

        bucket[key] += 1

    def __decr(self, key: T, count: Optional[int] = 1):
        entry = self.entries.get(key)
        entry.count -= count
        self.__sort()
        if entry.count <= 0:
            # we can do this because we know it will have the lowest count
            self.ordered_entries.pop()
            del self.entries[key]

    def get(self, ts_ms: int, lim: Optional[int] = None) -> List[Entry[T]]:
        self.reap(ts_ms)
        size = len(self.ordered_entries)
        local_lim = lim if lim and lim < size else size
        return [e for e in self.ordered_entries[:local_lim]]


class RedisTopList(AbstractTopList[T]):

    def __init__(self,
                 max_age: int,
                 redis: Redis,
                 ctor: Callable[[Any], T],
                 bucket_len_sec: Optional[int] = 1,
                 root_key: Optional[str] = 'nifty'):
        super().__init__(max_age, bucket_len_sec)
        self.redis = redis
        self.ctor = ctor
        self.toplink_prefix = root_key + ':toplink'
        # SortedSet { key: link_id, score: hits }
        self.toplist_set = self.toplink_prefix + ':set'

        # List { key: bucket_id, score: timestamp }
        self.buckets_list = self.toplink_prefix + ':buckets:list'

        # SortedSet :[timestamp] { key: link_id, score: -hits }
        self.bucket_set = self.toplink_prefix + ':bucket:set'

    @staticmethod
    def opt_str(opt_bytes: Optional[bytes]) -> Optional[str]:
        return str(opt_bytes) if opt_bytes is not None else None

    @retry(max_tries=3, stack_id=f"{__name__}:reap")
    def reap(self, ts: int):
        with self.redis.pipeline() as pipe:
            pipe.watch(self.buckets_list)

            # the typing is wrong so we have to force cast to proper type.
            # the docs describe the correct behavior:
            # from the docs at https://redis.readthedocs.io/en/stable/advanced_features.html
            # ---
            # "after WATCHing, the pipeline is put into immediate execution
            # mode until we tell it to start buffering commands again."
            # ---
            oldest_sec_str: Optional[str] = \
                self.opt_str(cast(Optional[bytes],
                                  pipe.lindex(self.buckets_list, -1)))
            if not oldest_sec_str:
                return

            if int(ts / 1000) - int(oldest_sec_str) < self.max_age:
                return

            oldest_key = f"{self.bucket_set}:{oldest_sec_str}"

            pipe.watch(self.toplist_set, oldest_key, self.buckets_list)
            pipe.multi()
            pipe.zunionstore(self.toplist_set, [self.toplist_set, oldest_key]) \
                .delete(oldest_key) \
                .rpop(self.buckets_list) \
                .execute()

    def __bucket_key(self, name: str) -> str:
        return f"{self.bucket_set}:{name}"

    @retry(max_tries=3, stack_id=f"{__name__}:incr")
    def incr(self, key: T, ts_ms: int):
        self.reap(ts_ms)

        # TODO msut add dedup logic, looking for guid
        # proposal, use a callback in __init__
        # provide a default callback

        ts_secs = int(ts_ms / 1000)
        bucket_key = ts_secs - ts_secs % self.bucket_len_sec

        with self.redis.pipeline() as pipe:
            pipe.watch(self.buckets_list)
            latest = self.opt_str(cast(Optional[bytes],
                                       pipe.lindex(self.buckets_list, 0)))
            _logger.debug(f"latest key = {latest}")
            latest_bucket_key = int(latest) if latest else None

            # if this is a newer bucket
            if not latest_bucket_key or latest_bucket_key < bucket_key:
                # add it to the set
                _logger.debug(f"pushing bucket {bucket_key}")
                pipe.multi()
                pipe.lpush(self.buckets_list, bucket_key)
                pipe.execute()

            # else see if this bucket is at the expected index
            else:
                _logger.debug(f"matching bucket {bucket_key}")
                expected_list_index = int((latest_bucket_key -
                                           bucket_key) / self.bucket_len_sec)
                key_at_index = cast(Optional[str], pipe.lindex(self.buckets_list,
                                                               expected_list_index))
                if not key_at_index or int(key_at_index) != bucket_key:
                    _logger.warning(f"can't increment key '{key}', expected "
                                    f"'{bucket_key}' but found {int(key_at_index)}")
                    return
            # DONE - bucket is tracked

            pipe.watch(self.bucket_set, self.__bucket_key(latest),
                       self.toplist_set)
            pipe.multi()
            pipe.zincrby(self.__bucket_key(latest), -1, key) \
                .zincrby(self.toplist_set, 1, key) \
                .execute()

    def get(self, ts_ms: int, lim: Optional[int] = 1) -> List[Entry[T]]:
        self.reap(ts_ms)
        return [Entry(self.ctor(k), v) for k, v in
                self.redis.zrange(self.toplist_set, 0, lim, True,
                                  score_cast_func=int)]
