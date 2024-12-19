"""Module containing tests for the discord helper functions"""

# pylint: disable=protected-access, missing-class-docstring, pointless-statement, expression-not-assigned, unused-argument

import inspect
import logging
from time import sleep

from discord.ext import commands

from nikobot.util import discord, storage
from nikobot.discord_bot import DiscordBot

logger = logging.getLogger("test")

def test_wrap_function_for_normal_command():
    """Test the internal _wrap_function_for_normal_command() function"""

    def func1(self, ctx, name_arg: str, price: float, values: str):
        pass
    def func2(self, ctx, *changes: list[int]):
        pass
    def func3(self, ctx, username: str):
        pass

    functions = [
        func1,
        func2,
        func3
    ]
    signatures = [
        "(ctx, name_arg: str, price: float, *values: list[str])",
        "(ctx, *changes: list[int])",
        "(ctx, *username: list[str])"
    ]

    for c, test_func in enumerate(functions):
        wrapped = discord._wrap_function_for_normal_command("example_command", test_func)
        assert wrapped is not None
        wrapped_sig = str(inspect.signature(wrapped))
        assert wrapped_sig == signatures[c]

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

    # cannot test if is_private_channel actually returns true
    # because private messages between discord bots aren't allowed

# def test_is_slash_command
