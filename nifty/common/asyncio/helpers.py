import asyncio
import functools
import logging
from typing import Any, Callable, Coroutine, Optional, TypeVar

_T = TypeVar("_T")
_OrignalFunc = Callable[..., Coroutine[Any, Any, _T]]


def retry(
    max_tries: int,
    stack_id: Optional[str] = __name__,
    first_delay: Optional[float] = 0.1,
) -> Callable[[_OrignalFunc[_T]], _OrignalFunc[_T]]:
    if stack_id is None:
        raise Exception("stack_id cannot be None")

    if first_delay is None or first_delay <= 0:
        raise Exception("first_delay must be > 0")

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
