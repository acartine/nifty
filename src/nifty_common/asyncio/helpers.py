import asyncio
import functools
import logging
from typing import Awaitable, Callable, Optional, ParamSpec, TypeVar

Param = ParamSpec("Param")
RetType = TypeVar("RetType")
OriginalFunc = Callable[Param, RetType]
AsyncOriginalFunc = Callable[Param, Awaitable[RetType]]


def retry(max_tries: int,
                stack_id: Optional[str] = __name__,
                first_delay: Optional[float] = .1) -> Callable[[AsyncOriginalFunc], AsyncOriginalFunc]:
    def decorator(func: AsyncOriginalFunc) -> AsyncOriginalFunc:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
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
                        logging.getLogger(stack_id).error(f"Exception limit '{max_tries}' exceeded")
                        raise e

        return wrapper

    return decorator
