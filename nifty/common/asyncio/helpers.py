import asyncio
import functools
import logging
from typing import Any, Callable, Coroutine, Optional, TypeVar

_T = TypeVar("_T")
_OrignalFunc = Callable[..., Coroutine[Any, Any, _T]]


def retry(
    max_tries: int,
    stack_id: str,
    first_delay: Optional[float] = 0.1,
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

    if not first_delay or first_delay < 0:
        raise ValueError("first_delay must be >= 0")

    def decorator(func: _OrignalFunc[_T]) -> _OrignalFunc[_T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> _T:
            ex: Exception | None = None
            for attempt in range(max_tries):
                # linear for now, keep it simple
                delay = attempt * first_delay
                if delay > 0:
                    await asyncio.sleep(delay)
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logging.getLogger(stack_id).debug(e)
                    if attempt >= max_tries - 1:
                        ex = e
                        break

            logging.getLogger(stack_id).error(f"Exception limit '{max_tries}' exceeded")
            raise ex if ex else Exception(f"Exception limit '{max_tries}' exceeded")

        return wrapper

    return decorator
