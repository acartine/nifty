import asyncio
import functools
import logging
import time
from datetime import datetime
from typing import Awaitable, Callable, Optional, ParamSpec, TypeVar


def timestamp_ms(*, datetime_ts: Optional[datetime] = None) -> int:
    if datetime_ts is not None:
        ts = datetime_ts.timestamp()
    else:
        ts = time.time()
    return int(ts * 1000)


Param = ParamSpec("Param")
RetType = TypeVar("RetType")
OriginalFunc = Callable[Param, RetType]


def retry(max_tries: int,
          stack_id: str = __name__,
          first_delay: float = .1):
    """
    Create callable decorator to retry a function
    """
    def decorator(func: OriginalFunc) -> OriginalFunc:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
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


T = TypeVar('T')
def opt_or(optional: Optional[T], fallback: T) -> T:
    return optional if optional is not None else fallback

T_Intable = TypeVar('T_Intable', bound=str | float | bytes, covariant=True)
def optint_or_none(optional: Optional[T_Intable]) -> Optional[int]:
    return int(optional) if optional is not None else None

def none_throws(optional: Optional[T], msg: str) -> T:
    if optional is None:
        raise Exception(msg)
    return optional


def noneint_throws(optional: Optional[T_Intable], key: str) -> int:
    return none_throws(optint_or_none(optional), f"Unset value for {key}")
