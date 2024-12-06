"""
    Pytest fixtures
"""

# pylint: disable=protected-access

import asyncio

import pytest

from nikobot.util import discord, storage

@pytest.fixture(scope="function", autouse=True)
def setup_storages():
    """Setup the PersistentStorage, VolatileStorage and StorageView for test usage"""

    yield None

    keys_to_keep = [
        "storage_file",
        "cache_dir",
        "temp_dir",
        "bot",
        "modules",
        "mal.CLIENT-ID"
    ]
    keys_to_remove = []
    for store in [item._store for item in (storage.PersistentStorage, storage.VolatileStorage)]:
        for key in store.keys():
            remove = True
            for key_to_keep in keys_to_keep:
                if key in (key_to_keep,
                           key_to_keep.split(".", maxsplit=1)[0]):
                    remove = False
            if remove:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del store[key]

@pytest.fixture(scope="session")
def bot():
    """Setup the DiscordBot for use with tests"""

    bot_obj = discord.get_bot()

    yield bot_obj

    # stop discord bot after session ends
    send_fut = asyncio.run_coroutine_threadsafe(bot_obj.close(), bot_obj.loop)
    send_fut.result()
