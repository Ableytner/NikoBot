"""
    Pytest fixtures
"""

# pylint: disable=protected-access, missing-class-docstring

import asyncio
import logging
import os
import pathlib
import _thread
from threading import Thread
from time import sleep

import discord as discordpy
import pytest
from discord.ext import commands

from nikobot.discord_bot import DiscordBot
from nikobot.util import error, storage

logger = logging.getLogger("test")

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
        "modules_to_load",
        "mal.CLIENT-ID",
        "test_channel_id"
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

    if "DISCORD_TOKEN" not in os.environ:
        token_file = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "dc_token_test.txt").resolve())
        if not os.path.isfile(token_file):
            raise error.MissingToken()
        with open(token_file, "r", encoding="utf8") as file:
            os.environ["DISCORD_TOKEN"] = file.readline()

    if "mal.malnotifier" in storage.VolatileStorage["modules_to_load"] and "MAL_CLIENT_ID" not in os.environ:
        mal_client_file = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "client_id.txt").resolve())
        if not os.path.isfile(mal_client_file):
            raise FileNotFoundError()
        with open(mal_client_file, "r", encoding="utf8") as file:
            os.environ["MAL_CLIENT_ID"] = file.readline()

    # don't ignore commands sent by other bots
    async def process_commands(self, message):
        """Override process_commands to listen to messages of other bots"""

        ctx = await self.get_context(message)
        await self.invoke(ctx)
    DiscordBot.process_commands = process_commands

    bot_ready = [False]
    async def on_ready(self: DiscordBot):
        """Override on_ready to wait for the bot to start"""

        logger.info(f"{self.user} is now online")
        bot_ready[0] = True
    DiscordBot.on_ready = on_ready

    bot_obj = DiscordBot()
    storage.VolatileStorage["bot"] = bot_obj

    def thread_func():
        try:
            bot_obj.start_bot()
        # pylint: disable-next=broad-exception-caught
        except Exception as e:
            logger.exception(e)
            _thread.interrupt_main()
    Thread(target=thread_func, daemon=True).start()

    while not bot_ready[0]:
        logger.info("waiting for bot to start...")
        sleep(1)

    yield bot_obj

    # stop discord bot after session ends
    send_fut = asyncio.run_coroutine_threadsafe(bot_obj.close(), bot_obj.loop)
    send_fut.result()

@pytest.fixture(scope="session")
def testing_bot():
    """Setup another DiscordBot to be used in tests"""

    if "TESTING_DISCORD_TOKEN" not in os.environ:
        token_file = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "dc_token_testingbot.txt").resolve())
        if not os.path.isfile(token_file):
            raise error.MissingToken()
        with open(token_file, "r", encoding="utf8") as file:
            os.environ["TESTING_DISCORD_TOKEN"] = file.readline()

    bot_ready = [False]

    class TestingDiscordBot(commands.Bot):
        def __init__(self) -> None:
            super().__init__(command_prefix = "testing.", help_command=None, intents = discordpy.Intents.all())

        def start_bot(self):
            """Override start_bot to set the proper token"""

            self.run(os.environ["TESTING_DISCORD_TOKEN"], log_handler=None)

        async def on_ready(self: DiscordBot):
            """Override on_ready to wait for the bot to start"""

            logger.info(f"{self.user} is now online")
            bot_ready[0] = True

    bot_obj = TestingDiscordBot()

    def thread_func():
        try:
            bot_obj.start_bot()
        # pylint: disable-next=broad-exception-caught
        except Exception as e:
            logger.exception(e)
            _thread.interrupt_main()
    Thread(target=thread_func, daemon=True).start()

    while not bot_ready[0]:
        logger.info("waiting for testing bot to start...")
        sleep(1)

    yield bot_obj

    # stop discord bot after session ends
    send_fut = asyncio.run_coroutine_threadsafe(bot_obj.close(), bot_obj.loop)
    send_fut.result()
