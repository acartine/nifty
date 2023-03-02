import abc
import functools
import logging
import math
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, List, Optional, ParamSpec, Set, TypeVar, cast

from redis.client import Redis

from nifty_common.constants import REDIS_TRENDING_SIZE_KEY
from nifty_common.helpers import noneint_throws, retry

T = TypeVar('T')
Param = ParamSpec("Param")
RetType = TypeVar("RetType")
OriginalFunc = Callable[Param, RetType]

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
    def get(self, ts_ms: int) -> List[Entry[T]]:
        pass


class RedisTopList(AbstractTopList[T]):

    def __init__(self,
                 root_key: str,
                 max_age_sec: int,
                 redis: Redis,
                 ctor: Callable[[Any], T],
                 listener: Callable[[Set[T], Set[T]], None],
                 bucket_len_sec: Optional[int] = 1,
                 ):
        super().__init__(max_age_sec, bucket_len_sec)
        self.redis = redis
        self.ctor = ctor
        self.listener = listener
        self.cache = set()

        # SortedSet { key: link_id, score: hits }
        self.toplist_set = root_key

        # List { key: bucket_id, score: timestamp }
        self.buckets_list = root_key + ':buckets:list'

        # SortedSet :[timestamp] { key: link_id, score: -hits }
        self.bucket_set = root_key + ':bucket:set'

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
                oldest_sec_str: Optional[bytes] = \
                    cast(Optional[bytes], pipe.lindex(self.buckets_list, -1))
                if not oldest_sec_str:
                    return

                oldest_sec = int(oldest_sec_str)
                _logger.debug(f"ts={ts_ms} oldest_sec={oldest_sec}")
                if int(ts_ms / 1000) - oldest_sec < self.max_age:
                    return

                oldest_key = f"{self.bucket_set}:{oldest_sec}"

                pipe.watch(self.toplist_set, oldest_key, self.buckets_list)
                pipe.multi()
                pipe.zunionstore(self.toplist_set, [self.toplist_set, oldest_key]) \
                    .zremrangebyscore(self.toplist_set, -math.inf, 1) \
                    .delete(oldest_key) \
                    .rpop(self.buckets_list) \
                    .execute()

    def __bucket_key(self, name: int) -> str:
        return f"{self.bucket_set}:{name}"

    def __get(self) -> List[Entry[T]]:
        size = noneint_throws(self.redis.get(REDIS_TRENDING_SIZE_KEY),
                              REDIS_TRENDING_SIZE_KEY)
        foo = self.redis.zrange(self.toplist_set,
                                start=0,
                                end=size,
                                desc=True,
                                withscores=True,
                                score_cast_func=int)
        return [Entry(self.ctor(k), v) for k, v in foo]

    @staticmethod
    def _observe() -> OriginalFunc:
        def decorator(func: OriginalFunc) -> OriginalFunc:
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs) -> RetType:
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
    def incr(self, key: T, ts_ms: int):
        self.__reap(ts_ms)
        ts_secs = int(ts_ms / 1000)
        bucket_key = ts_secs - ts_secs % self.bucket_len_sec

        with self.redis.pipeline() as pipe:
            pipe.watch(self.buckets_list)
            latest: Optional[bytes] = \
                cast(Optional[bytes], pipe.lindex(self.buckets_list, 0))
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
                key_at_index = cast(Optional[bytes], pipe.lindex(self.buckets_list,
                                                                 expected_list_index))
                if not key_at_index or int(key_at_index) != bucket_key:
                    _logger.warning(f"can't increment key '{key}', expected "
                                    f"'{bucket_key}' but found {int(key_at_index)}")
                    return
        # DONE - bucket is tracked

        pipe.watch(self.bucket_set, self.__bucket_key(bucket_key),
                   self.toplist_set)
        pipe.multi()
        pipe.zincrby(self.__bucket_key(bucket_key), -1, key) \
            .zincrby(self.toplist_set, 1, key) \
            .execute()

    def get(self, ts_ms: int) -> List[Entry[T]]:
        self.reap(ts_ms=ts_ms)
        return self.__get()
