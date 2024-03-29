# fixes stubs like redis that use generics when the code does not
from __future__ import annotations

import abc
import functools
import logging
import math
from abc import abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Generic,
    List,
    Optional,
    Set,
    TypeVar,
    cast,
)

from redis.asyncio.client import Redis

from nifty.common.asyncio import helpers
from nifty.common.helpers import noneint_throws
from nifty.common.types import Key

_EntryKey = TypeVar("_EntryKey", bound=str | int)
_OriginalRet = TypeVar("_OriginalRet")
_OriginalFunc = Callable[..., Coroutine[Any, Any, _OriginalRet]]


@dataclass
class Entry(Generic[_EntryKey]):
    key: _EntryKey
    count: int


class AbstractTopList(Generic[_EntryKey], abc.ABC):
    def __init__(self, max_age: int, bucket_len_sec: Optional[int] = 1):
        if bucket_len_sec is None:
            raise Exception("bucket_len_sec must be > 0")
        self.max_age = max_age
        self.bucket_len_sec = bucket_len_sec

    @abstractmethod
    async def incr(self, key: _EntryKey, ts_ms: int) -> None:
        pass

    @abstractmethod
    async def reap(self, ts: int) -> None:
        pass


class RedisTopList(AbstractTopList[_EntryKey]):
    def __init__(
        self,
        root_key: str,
        max_age_sec: int,
        redis: Redis[str],
        ctor: Callable[[Any], _EntryKey],
        listener: Callable[[Set[_EntryKey], Set[_EntryKey]], Awaitable[None]],
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

    @helpers.retry(max_tries=3, stack_id=f"{__name__}:reap")
    async def __reap(self, ts_ms: int):
        while True:
            async with self.redis.pipeline() as pipe:
                await pipe.watch(self.buckets_list)

                # the typing is wrong so we have to force cast to proper type.
                # the docs describe the correct behavior:
                # from the docs at https://redis.readthedocs.io/en/stable/advanced_features.html
                # ---
                # "after WATCHing, the pipeline is put into immediate execution
                # mode until we tell it to start buffering commands again."
                # ---
                oldest_sec_str: Optional[bytes] = cast(
                    Optional[bytes], await pipe.lindex(self.buckets_list, -1)
                )
                if not oldest_sec_str:
                    return

                oldest_sec = int(oldest_sec_str)
                if int(ts_ms / 1000) - oldest_sec < self.max_age:
                    return

                oldest_key = f"{self.bucket_set}:{oldest_sec}"

                await pipe.watch(self.toplist_set, oldest_key, self.buckets_list)
                pipe.multi()
                await (
                    pipe.zunionstore(self.toplist_set, [self.toplist_set, oldest_key])
                    .zremrangebyscore(self.toplist_set, -math.inf, 1)
                    .delete(oldest_key)
                    .rpop(self.buckets_list)
                    .execute()
                )

    def __bucket_key(self, name: int) -> str:
        return f"{self.bucket_set}:{name}"

    async def __get(self) -> List[Entry[_EntryKey]]:
        raw = await self.redis.get(Key.trending_size)
        size = noneint_throws(raw, Key.trending_size.value)
        foo = await self.redis.zrange(
            self.toplist_set,  # noqa
            start=0,
            end=size,
            desc=True,
            withscores=True,
            score_cast_func=int,
        )
        return [Entry(self.ctor(k), v) for k, v in foo]

    @staticmethod
    def __observe() -> (
        Callable[[_OriginalFunc[_OriginalRet]], _OriginalFunc[_OriginalRet]]
    ):
        def decorator(func: _OriginalFunc[_OriginalRet]) -> _OriginalFunc[_OriginalRet]:
            @functools.wraps(func)
            async def wrapper(
                self: RedisTopList[_EntryKey],
                *args: Any,
                **kwargs: Any,
            ):
                ret = await func(self, *args, **kwargs)
                newcache: Set[_EntryKey] = {item.key for item in await self.__get()}
                added: Set[_EntryKey] = newcache - self.cache
                removed: Set[_EntryKey] = self.cache - newcache
                self.cache = newcache
                if added or removed:
                    await self.listener(added, removed)
                return ret

            return wrapper

        return decorator

    @__observe()
    async def reap(self, ts: int) -> None:
        await self.__reap(ts)

    @__observe()
    @helpers.retry(max_tries=3, stack_id=f"{__name__}:incr")
    async def incr(self, key: _EntryKey, ts_ms: int):
        await self.__reap(ts_ms)
        ts_secs = int(ts_ms / 1000)
        bucket_key = ts_secs - ts_secs % self.bucket_len_sec

        async with self.redis.pipeline() as pipe:
            await pipe.watch(self.buckets_list)
            latest: Optional[bytes] = cast(
                Optional[bytes], await pipe.lindex(self.buckets_list, 0)
            )
            logging.debug(f"latest key = {latest}")
            latest_bucket_key = int(latest) if latest else None

            # if this is a newer bucket
            if not latest_bucket_key or latest_bucket_key < bucket_key:
                # add it to the set
                logging.debug(f"pushing bucket {bucket_key}")
                pipe.multi()
                # noinspection PyUnresolvedReferences
                await pipe.lpush(self.buckets_list, bucket_key).execute()

            # else see if this bucket is at the expected index
            else:
                logging.debug(f"matching bucket {bucket_key}")
                expected_list_index = int(
                    (latest_bucket_key - bucket_key) / self.bucket_len_sec
                )
                kai_raw = await pipe.lindex(self.buckets_list, expected_list_index)
                key_at_index = cast(Optional[bytes], kai_raw)
                if not key_at_index:
                    logging.warning(
                        f"can't increment key '{key}', expected "
                        f"'{bucket_key}' but none found"
                    )
                    return
                elif int(key_at_index) != bucket_key:
                    logging.warning(
                        f"can't increment key '{key}', expected "
                        f"'{bucket_key}' but found {int(key_at_index)}"
                    )
                    return
        # DONE - bucket is tracked

        await pipe.watch(
            self.bucket_set, self.__bucket_key(bucket_key), self.toplist_set
        )
        pipe.multi()
        # noinspection PyUnresolvedReferences
        await (
            pipe.zincrby(self.__bucket_key(bucket_key), -1, key)
            .zincrby(self.toplist_set, 1, key)
            .execute()
        )
