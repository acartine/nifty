import functools
import logging
import time
from typing import Callable, Optional, ParamSpec, TypeVar

from redis.client import Redis
from redis.asyncio.client import Redis as AsyncRedis

from nifty_common.config import cfg
from nifty_common.constants import REDIS_TRENDING_SIZE_KEY

T = TypeVar('T')


def get_redis() -> Redis:
    return Redis(host=cfg['redis']['host'], username=cfg['redis']['user'],
                 password=cfg['redis']['pwd'])


def get_redis_async() -> AsyncRedis:
    return AsyncRedis(host=cfg['redis']['host'], username=cfg['redis']['user'],
                      password=cfg['redis']['pwd'])


def timestamp_ms() -> int:
    return int(time.time() * 1000)


Param = ParamSpec("Param")
RetType = TypeVar("RetType")
OriginalFunc = Callable[Param, RetType]


def retry(max_tries: int,
          stack_id: Optional[str] = __name__,
          first_delay: Optional[float] = .1) -> OriginalFunc:

    def decorator(func: OriginalFunc) -> OriginalFunc:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> RetType:
            for attempt in range(max_tries):
                # linear for now, keep it simple
                delay = attempt * first_delay
                if delay > 0:
                    time.sleep(delay)
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.getLogger(stack_id).debug(e)
                    if attempt >= max_tries - 1:
                        logging.getLogger(stack_id).error(f"Exception limit '{max_tries}' exceeded")
                        raise e

        return wrapper

    return decorator


async def async_retry(max_tries: int,
          stack_id: Optional[str] = __name__,
          first_delay: Optional[float] = .1) -> OriginalFunc:
    def decorator(func: OriginalFunc) -> OriginalFunc:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> RetType:
            for attempt in range(max_tries):
                # linear for now, keep it simple
                delay = attempt * first_delay
                if delay > 0:
                    time.sleep(delay)
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.getLogger(stack_id).debug(e)
                    if attempt >= max_tries - 1:
                        logging.getLogger(stack_id).error(f"Exception limit '{max_tries}' exceeded")
                        raise e

        return wrapper

    return decorator


def opt_or(optional: Optional[T], fallback: T) -> T:
    return optional if optional is not None else fallback


def optint_or_none(optional: Optional[T]) -> Optional[int]:
    return int(optional) if optional is not None else None


def redis_int(redis: Redis, key: str, throws: Optional[bool] = True) -> int:
    raw = redis.get(key)
    return noneint_throws(raw, key) if throws else optint_or_none(raw)


def trending_size(redis: Redis, throws: Optional[bool] = True) -> int:
    return redis_int(redis, REDIS_TRENDING_SIZE_KEY, throws)


def none_throws(optional: Optional[T], msg: str) -> T:
    if optional is None:
        raise Exception(msg)
    return optional


def noneint_throws(optional: Optional[T], key: str) -> int:
    return none_throws(optint_or_none(optional), f"Unset value for {key}")
