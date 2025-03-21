"""General non-discord specific help functions"""

import asyncio
from typing import Any

from abllib.storage import VolatileStorage
import numpy

def sync(coro, loop: asyncio.AbstractEventLoop = None) -> Any:
    """
    Run an async coroutine synchronously
    If no event loop is provided, use the bot's loop
    """

    if loop is None:
        bot = VolatileStorage["bot"]
        loop = bot.loop

    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    return fut.result()

def levenshtein_distance(token1: str, token2: str) -> int:
    """
    Calculate the levenshtein distance between token1 and token2
    Represents the edit distance between two strings
    """

    if not isinstance(token1, str):
        raise TypeError(f"Expected {type(str)}, got {type(token1)} for token1")
    if not isinstance(token2, str):
        raise TypeError(f"Expected {type(str)}, got {type(token2)} for token2")

    distances = numpy.zeros((len(token1) + 1, len(token2) + 1))

    for t1 in range(len(token1) + 1):
        distances[t1][0] = t1

    for t2 in range(len(token2) + 1):
        distances[0][t2] = t2

    a = 0
    b = 0
    c = 0

    for t1 in range(1, len(token1) + 1):
        for t2 in range(1, len(token2) + 1):
            if token1[t1-1] == token2[t2-1]:
                distances[t1][t2] = distances[t1 - 1][t2 - 1]
            else:
                a = distances[t1][t2 - 1]
                b = distances[t1 - 1][t2]
                c = distances[t1 - 1][t2 - 1]

                if (a <= b and a <= c):
                    distances[t1][t2] = a + 1
                elif (b <= a and b <= c):
                    distances[t1][t2] = b + 1
                else:
                    distances[t1][t2] = c + 1

    return distances[len(token1)][len(token2)]
