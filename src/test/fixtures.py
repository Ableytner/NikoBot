"""
    Pytest fixtures
"""

# pylint: disable=protected-access, missing-class-docstring

import asyncio
import json
import logging
import os
import typing
import _thread
from threading import Thread
from time import sleep

import discord as discordpy
import pytest
from discord.ext import commands

from nikobot.discord_bot import DiscordBot
from nikobot.util import storage

logger = logging.getLogger("test")

@pytest.fixture(scope="function", autouse=True)
def setup_storages():
    """Setup the PersistentStorage, VolatileStorage and StorageView for test usage"""

    yield None

    keys_to_keep = [
        "storage_file",
        "config_file",
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

    # load config
    if not os.path.isfile(storage.VolatileStorage["config_file"]):
        raise FileNotFoundError("Config file couldn't be found")
    with open(storage.VolatileStorage["config_file"], "r", encoding="utf8") as cf:
        config: dict[str, typing.Any] = json.load(cf)

    storage.VolatileStorage["modules_to_load"] = config["modules"]

    if "discord_token_testbot" not in config["test"] \
       or config["test"]["discord_token_testbot"] == "":
        raise ValueError("Missing discord_token_testbot for use with integration tests. " +
                         "Refer to the README for more information.")
    storage.VolatileStorage["discord_token"] = config["test"]["discord_token_testbot"]

    if "test_channel_id" not in config["test"] \
       or config["test"]["test_channel_id"] == "":
        raise ValueError("Missing test_channel_id for use with integration tests. " +
                         "Refer to the README for more information.")
    storage.VolatileStorage["test_channel_id"] = int(config["test"]["test_channel_id"])

    if "mal.malnotifier" in config["modules"]:
        if "malnotifier" not in config \
            or "client_id" not in config["malnotifier"] \
            or config["malnotifier"]["client_id"] == "":
            raise ValueError("Missing client_id for use with the malnotifier module. " +
                             "You can create one https://myanimelist.net/apiconfig and add it to your config.json.")

        storage.VolatileStorage["mal.client_id"] = config["malnotifier"]["client_id"]

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

    # load config
    if not os.path.isfile(storage.VolatileStorage["config_file"]):
        raise FileNotFoundError("Config file couldn't be found")
    with open(storage.VolatileStorage["config_file"], "r", encoding="utf8") as cf:
        config: dict[str, typing.Any] = json.load(cf)

    if "discord_token_helperbot" not in config["test"] \
       or config["test"]["discord_token_helperbot"] == "":
        raise ValueError("Missing discord_token_helperbot for use with integration tests. " +
                         "Refer to the README for more information.")
    storage.VolatileStorage["discord_token_helperbot"] = config["test"]["discord_token_helperbot"]

    bot_ready = [False]
    class TestingDiscordBot(commands.Bot):
        def __init__(self) -> None:
            super().__init__(command_prefix = "testing.", help_command=None, intents = discordpy.Intents.all())

        def start_bot(self):
            """Override start_bot to set the proper token"""

            self.run(storage.VolatileStorage["discord_token_helperbot"], log_handler=None)

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
