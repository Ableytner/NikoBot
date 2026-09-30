"""General non-discord specific help functions"""

import asyncio
import json
import os
from time import sleep
from typing import Any

from abllib.storage import VolatileStorage

_config_cache: dict[str, Any] | None = None

def load_config() -> dict[str, Any]:
    """Load config from the file path stored in VolatileStorage["config_file"]"""

    # pylint: disable-next=global-statement
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config_file = VolatileStorage.get("config_file")
    if config_file is None or not os.path.isfile(config_file):
        raise FileNotFoundError("Config file couldn't be found")

    with open(config_file, "r", encoding="utf8") as cf:
        _config_cache = json.load(cf)

    return _config_cache

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
