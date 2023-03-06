import asyncio
import functools
import logging
import time
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional, ParamSpec, TypeVar


def timestamp_ms(*, datetime_ts: Optional[datetime] = None) -> int:
    if datetime_ts is not None:
        ts = datetime_ts.timestamp()
    else:
        ts = time.time()
    return int(ts * 1000)


_T = TypeVar("_T")
_OrignalFunc = Callable[..., _T]


def retry(
    max_tries: int, stack_id: str = __name__, first_delay: float = 0.1
) -> Callable[[_OrignalFunc], _OrignalFunc]:
    """
    Create callable decorator to retry a function
    """

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
                    logging.getLogger(stack_id).debug(e)
                    if attempt >= max_tries - 1:
                        ex = e
                        break

            logging.getLogger(stack_id).error(f"Exception limit '{max_tries}' exceeded")
            raise ex if ex else Exception(f"Exception limit '{max_tries}' exceeded")

        return wrapper

    return decorator


T = TypeVar("T")


def opt_or(optional: Optional[T], fallback: T) -> T:
    return optional if optional is not None else fallback


T_Intable = TypeVar("T_Intable", bound=str | float | bytes, covariant=True)


def optint_or_none(optional: Optional[T_Intable]) -> Optional[int]:
    return int(optional) if optional is not None else None


def none_throws(optional: Optional[T], msg: str) -> T:
    if optional is None:
        raise Exception(msg)
    return optional


def noneint_throws(optional: Optional[T_Intable], key: str) -> int:
    return none_throws(optint_or_none(optional), f"Unset value for {key}")
