"""Module containing tests for the discord helper functions"""

# pylint: disable=protected-access, missing-class-docstring, pointless-statement, expression-not-assigned

import logging
from time import sleep

from discord.ext import commands

from nikobot.util import discord, storage
from nikobot.discord_bot import DiscordBot

logger = logging.getLogger("test")

def test_is_private_channel(bot: DiscordBot, testing_bot: DiscordBot):
    """Test the discord.is_private_channel() method"""

    testing_channel = testing_bot.get_channel(storage.StorageView["test_channel_id"])
    assert testing_channel is not None

    contexts = []
    def ctx_hook(ctx: commands.context.Context):
        contexts.append(ctx)
    bot.cogs["General"].ctx_hook = ctx_hook

    testing_bot.loop.create_task(testing_channel.send("niko.ping"))

    while len(contexts) == 0:
        sleep(1)
    ctx: commands.context.Context = contexts[0]

    assert not discord.is_private_channel(ctx)
