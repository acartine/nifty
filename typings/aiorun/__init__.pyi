"""
This type stub file was generated by pyright.
"""

import signal
import sys
import logging
import inspect
import asyncio
from asyncio import AbstractEventLoop, CancelledError, Task, gather, get_event_loop
from concurrent.futures import Executor, ThreadPoolExecutor
from typing import Any, Callable, Coroutine, Optional, Union
from weakref import WeakSet
from functools import partial

"""Boilerplate for asyncio applications"""
__all__ = ["run", "shutdown_waits_for"]
__version__ = ...
logger = ...
WINDOWS = ...
_DO_NOT_CANCEL_COROS = ...

def shutdown_waits_for(coro, loop=...):  # -> Coroutine[Any, Any, Unknown | Any]:
    """Prevent coro from being cancelled during the shutdown sequence.

    The trick here is that we add this coro to the global
    "DO_NOT_CANCEL" collection, and then later during the shutdown
    sequence we make sure that the task that wraps this coro will NOT
    be cancelled.

    To make this work, we have to create a super-secret task, below, that
    communicates with the caller (which "awaits" us) via a Future. Using
    a Future in this way allows us to avoid awaiting the Task, which
    decouples the Task from the normal exception propagation which would
    normally happen when the outer Task gets cancelled.  We get the
    result of coro back to the caller via Future.set_result.

    NOTE that during the shutdown sequence, the caller WILL NOT be able
    to receive a result, since the caller will likely have been
    cancelled.  So you should probably not rely on capturing results
    via this function.
    """
    ...

def run(
    coro: Optional[Coroutine[Any, Any, Any]] = ...,
    *,
    loop: Optional[AbstractEventLoop] = ...,
    shutdown_handler: Optional[Callable[[AbstractEventLoop], None]] = ...,
    shutdown_callback: Any = ...,
    executor_workers: Optional[int] = ...,
    executor: Optional[Executor] = ...,
    use_uvloop: bool = ...,
    stop_on_unhandled_errors: bool = ...,
    timeout_task_shutdown: float = ...
) -> None:
    """
    Start up the event loop, and wait for a signal to shut down.

    :param coro: Optionally supply a coroutine. The loop will still
        run if missing. The loop will continue to run after the supplied
        coroutine finishes. The supplied coroutine is typically
        a "main" coroutine from which all other work is spawned.
    :param loop: Optionally supply your own loop. If missing, a new
        event loop instance will be created.
    :param shutdown_handler: By default, SIGINT and SIGTERM will be
        handled and will stop the loop, thereby invoking the shutdown
        sequence. Alternatively you can supply your own shutdown
        handler function. It should conform to the type spec as shown
        in the function signature.
    :param shutdown_callback: Callable, executed after loop is stopped, before
        cancelling any tasks.
        Useful for graceful shutdown.
    :param executor_workers: The number of workers in the executor.
        NOTE: ``run()`` creates a new executor instance internally,
        regardless of whether you supply your own loop. Note that this
        parameter will be ignored if you provide an executor parameter.
    :param executor: You can decide to use your own executor instance
        if you like. If you provide an executor instance, the
        executor_workers parameter will be ignored.
    :param use_uvloop: The loop policy will be set to use uvloop. It
        is your responsibility to install uvloop. If missing, an
        ``ImportError`` will be raised.
    :param stop_on_unhandled_errors: By default, the event loop will
        handle any exceptions that get raised and are not handled. This
        means that the event loop will continue running regardless of errors,
        and the only way to stop it is to call `loop.stop()`. However, if
        this flag is set, any unhandled exceptions will stop the loop, and
        be re-raised after the normal shutdown sequence is completed.
    :param timeout_task_shutdown: When shutdown is initiated, for example
        by a signal like SIGTERM, or even by an unhandled exception if
        ``stop_on_unhandled_errors`` is True, then the first action taken
        during shutdown is to cancel all currently pending or running tasks
        and then wait for them all to complete. This timeout sets an upper
        limit on how long to wait.
    """
    ...

async def windows_support_wakeup():
    """See https://stackoverflow.com/a/36925722"""
    ...