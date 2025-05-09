"""General non-discord specific help functions"""

import asyncio
from time import sleep
from typing import Any

from abllib.storage import VolatileStorage

def sync(coro, loop: asyncio.AbstractEventLoop = None) -> Any:
    """
    Run an async coroutine synchronously
    If no event loop is provided, use the bot's loop
    """

    if loop is None:
        bot = VolatileStorage["bot"]
        loop = bot.loop

    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    while not fut.done():
        sleep(0.1)
    return fut.result()
