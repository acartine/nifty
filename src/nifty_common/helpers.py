import functools
import logging
import time
from typing import Callable, Optional, ParamSpec, TypeVar

from redis.client import Redis

from nifty_common.config import cfg

T = TypeVar('T')


def get_redis() -> Redis:
    return Redis(host=cfg['redis']['host'], username=cfg['redis']['user'],
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


def opt_or(optional: Optional[T], fallback: T) -> T:
    return optional if optional is not None else fallback
