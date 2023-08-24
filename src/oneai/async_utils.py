import asyncio
import concurrent.futures
import os
from typing import Awaitable, TypeVar


# for jupyter environment, to avoid "asyncio.run() cannot be called from a running event loop"
pool = concurrent.futures.ThreadPoolExecutor()

if os.name == "nt":  # Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


T = TypeVar("T")


def async_to_sync(coro: Awaitable[T]) -> T:
    """
    Runs an async function in a synchronous context.
    """
    try:
        asyncio.get_running_loop()
        return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        pass

    return asyncio.run(coro)
