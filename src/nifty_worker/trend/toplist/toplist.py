# fixes stubs like redis that use generics when the code does not
from __future__ import annotations

import abc
import functools
import logging
import math
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, List, Optional, Set, TypeVar, cast

from redis.client import Redis

from nifty_common.helpers import noneint_throws, retry
from nifty_common.types import Key

_EntryKey = TypeVar("_EntryKey", bound=str | int)
_OriginalRet = TypeVar("_OriginalRet")
_OriginalFunc = Callable[..., _OriginalRet]

_logger = logging.getLogger(__name__)


@dataclass
class Entry(Generic[_EntryKey]):
    key: _EntryKey
    count: int


class AbstractTopList(Generic[_EntryKey], abc.ABC):
    def __init__(self, max_age: int, bucket_len_sec: Optional[int] = None):
        self.max_age = max_age
        self.bucket_len_sec = bucket_len_sec if bucket_len_sec else 1

    @abstractmethod
    def incr(self, key: _EntryKey, ts_ms: int):
        pass

    @abstractmethod
    def reap(self, ts: int):
        pass


class RedisTopList(AbstractTopList[_EntryKey]):
    def __init__(
        self,
        root_key: str,
        max_age_sec: int,
        redis: Redis[str],
        ctor: Callable[[Any], _EntryKey],
        listener: Callable[[Set[_EntryKey], Set[_EntryKey]], None],
        bucket_len_sec: Optional[int] = 1,
    ):
        super().__init__(max_age_sec, bucket_len_sec)
        self.redis = redis
        self.ctor = ctor
        self.listener = listener
        self.cache: Set[_EntryKey] = set()

        # SortedSet { key: link_id, score: hits }
        self.toplist_set = root_key

        # List { key: bucket_id, score: timestamp }
        self.buckets_list = root_key + ":buckets:list"

        # SortedSet :[timestamp] { key: link_id, score: -hits }
        self.bucket_set = root_key + ":bucket:set"

    @retry(max_tries=3, stack_id=f"{__name__}:reap")
    def __reap(self, ts_ms: int):
        while True:
            with self.redis.pipeline() as pipe:
                pipe.watch(self.buckets_list)

                # the typing is wrong so we have to force cast to proper type.
                # the docs describe the correct behavior:
                # from the docs at https://redis.readthedocs.io/en/stable/advanced_features.html
                # ---
                # "after WATCHing, the pipeline is put into immediate execution
                # mode until we tell it to start buffering commands again."
                # ---
                oldest_sec_str: Optional[bytes] = cast(
                    Optional[bytes], pipe.lindex(self.buckets_list, -1)
                )
                if not oldest_sec_str:
                    return

                oldest_sec = int(oldest_sec_str)
                _logger.debug(f"ts={ts_ms} oldest_sec={oldest_sec}")
                if int(ts_ms / 1000) - oldest_sec < self.max_age:
                    return

                oldest_key = f"{self.bucket_set}:{oldest_sec}"

                pipe.watch(self.toplist_set, oldest_key, self.buckets_list)
                pipe.multi()
                pipe.zunionstore(
                    self.toplist_set, [self.toplist_set, oldest_key]
                ).zremrangebyscore(self.toplist_set, -math.inf, 1).delete(
                    oldest_key
                ).rpop(  # pyright: ignore [reportUnknownMemberType]
                    self.buckets_list
                ).execute()

    def __bucket_key(self, name: int) -> str:
        return f"{self.bucket_set}:{name}"

    def __get(self) -> List[Entry[_EntryKey]]:
        size = noneint_throws(
            self.redis.get(Key.trending_size), Key.trending_size.value
        )
        foo = self.redis.zrange(
            self.toplist_set,
            start=0,
            end=size,
            desc=True,
            withscores=True,
            score_cast_func=int,
        )
        return [Entry(self.ctor(k), v) for k, v in foo]

    @staticmethod
    def _observe() -> (
        Callable[[_OriginalFunc[_OriginalRet]], _OriginalFunc[_OriginalRet]]
    ):
        def decorator(func: _OriginalFunc[_OriginalRet]) -> _OriginalFunc[_OriginalRet]:
            @functools.wraps(func)
            def wrapper(self: RedisTopList[_EntryKey], *args: Any, **kwargs: Any):
                ret = func(self, *args, **kwargs)
                newcache = {item.key for item in self.__get()}
                added = newcache - self.cache
                removed = self.cache - newcache
                self.cache = newcache
                if added or removed:
                    self.listener(added, removed)
                return ret

            return wrapper

        return decorator

    @_observe()
    def reap(self, ts_ms: int):
        self.__reap(ts_ms)

    @_observe()
    @retry(max_tries=3, stack_id=f"{__name__}:incr")
    def incr(self, key: _EntryKey, ts_ms: int):
        self.__reap(ts_ms)
        ts_secs = int(ts_ms / 1000)
        bucket_key = ts_secs - ts_secs % self.bucket_len_sec

        with self.redis.pipeline() as pipe:
            pipe.watch(self.buckets_list)
            latest: Optional[bytes] = cast(
                Optional[bytes], pipe.lindex(self.buckets_list, 0)
            )
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
                expected_list_index = int(
                    (latest_bucket_key - bucket_key) / self.bucket_len_sec
                )
                key_at_index = cast(
                    Optional[bytes], pipe.lindex(self.buckets_list, expected_list_index)
                )
                if not key_at_index:
                    _logger.warning(
                        f"can't increment key '{key}', expected "
                        f"'{bucket_key}' but none found"
                    )
                    return
                elif int(key_at_index) != bucket_key:
                    _logger.warning(
                        f"can't increment key '{key}', expected "
                        f"'{bucket_key}' but found {int(key_at_index)}"
                    )
                    return
        # DONE - bucket is tracked

        pipe.watch(self.bucket_set, self.__bucket_key(bucket_key), self.toplist_set)
        pipe.multi()
        pipe.zincrby(self.__bucket_key(bucket_key), -1, key).zincrby(
            self.toplist_set, 1, key
        ).execute()
