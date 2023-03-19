import functools
import logging
import time
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar

# do NOT import anything from our stack here!


def timestamp_ms(*, datetime_ts: Optional[datetime] = None) -> int:
    """
    Return current timestamp in milliseconds

    mainly just to make sure we're using the same timestamp everywhere

    param datetime_ts: if provided, use this datetime instead of current time
    return: timestamp in milliseconds
    """
    if datetime_ts is not None:
        ts = datetime_ts.timestamp()
    else:
        ts = time.time()
    return int(ts * 1000)


_T = TypeVar("_T")
_OrignalFunc = Callable[..., _T]


def retry(
    max_tries: int, stack_id: str, first_delay: float = 0.1
) -> Callable[[_OrignalFunc[_T]], _OrignalFunc[_T]]:
    """
    Create callable decorator to retry a function

    each delay is the previous delay * attempt number
    a delay of 0 means all retries will be immediate.  Not recommended.

    param max_tries: number of times to retry >= 1
    param stack_id: stack id to use for logging
    first_delay: delay in seconds before first retry >= 0
    """
    if max_tries < 1:
        raise ValueError("max_tries must be >= 1")

    if first_delay < 0:
        raise ValueError("first_delay must be >= 0")

    def decorator(func: _OrignalFunc[_T]) -> _OrignalFunc[_T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> _T:
            ex: Exception | None = None
            for attempt in range(max_tries):
                # linear for now, keep it simple
                delay = attempt * first_delay
                if delay > 0:
                    time.sleep(delay)
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt >= max_tries - 1:
                        ex = e
                        break
                    else:
                        logging.getLogger(stack_id).debug(e)

            logging.getLogger(stack_id).error(f"Exception limit '{max_tries}' exceeded")
            raise ex if ex else Exception(f"Exception limit '{max_tries}' exceeded")

        return wrapper

    return decorator


T = TypeVar("T")


def opt_or(optional: Optional[T], fallback: T) -> T:
    """
    Return optional if not None, otherwise fallback
    param optional: optional value
    param fallback: fallback value
    return: optional if not None, otherwise fallback
    """
    return optional if optional is not None else fallback


T_Intable = TypeVar("T_Intable", bound=str | float | bytes, covariant=True)


def optint_or_none(optional: Optional[T_Intable]) -> Optional[int]:
    """
    Return optional as int if not None, otherwise None
    param optional: optional value
    return: optional as int if not None, otherwise None
    """
    return int(optional) if optional is not None else None


def none_throws(optional: Optional[T], msg: str) -> T:
    """
    Return optional if not None, otherwise raise exception
    param optional: optional value
    param msg: exception message
    return: optional if not None, otherwise raise exception"""
    if optional is None:
        raise Exception(msg)
    return optional


def noneint_throws(optional: Optional[T_Intable], key: str) -> int:
    """
    Return optional as int if not None, otherwise raise exception
    param optional: optional value
    param key: key name for exception message
    return: optional as int if not None, otherwise raise exception
    """
    return none_throws(optint_or_none(optional), f"Unset value for {key}")
