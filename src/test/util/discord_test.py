"""Module containing tests for the discord helper functions"""

# pylint: disable=protected-access, missing-class-docstring, pointless-statement, expression-not-assigned, unused-argument

import inspect
import logging
from time import sleep

import pytest
from discord.ext import commands

from nikobot.util import discord, storage
from nikobot.discord_bot import DiscordBot
from ..helpers import CTXGrabber

logger = logging.getLogger("test")

def test_wrap_function_for_normal_command():
    """Test the internal _wrap_function_for_normal_command() function"""

    def func1(self, ctx, name_arg: str, price: float, values: str):
        pass
    def func2(self, ctx, *changes: list[int]):
        pass
    def func3(self, ctx, username: str):
        pass
    def func4(self, ctx, firstname: str, lastname: str | None):
        pass
    def func5(self, ctx, firstname: str, lastname: str):
        pass
    functions = [
        func1,
        func2,
        func3,
        func4,
        func5
    ]
    signatures = [
        "(ctx, name_arg: str, price: float, *values: list[str])",
        "(ctx, *changes: list[int])",
        "(ctx, *username: list[str])",
        "(ctx, firstname: str, *lastname: list[str] | None)",
        "(ctx, firstname: str, *lastname: list[str])"
    ]
    for c, test_func in enumerate(functions):
        wrapped = discord._wrap_function_for_normal_command("example_command", test_func)
        assert wrapped is not None
        wrapped_sig = str(inspect.signature(wrapped))
        assert wrapped_sig == signatures[c]

    def ffunc1(self, ctx, name_arg: str | None, value: str):
        pass
    def ffunc2(self, ctx, value: str, value2: str, name_arg: str | None, value3: str):
        pass
    functions = [
        ffunc1,
        ffunc2
    ]
    for c, test_func in enumerate(functions):
        with pytest.raises(SyntaxError):
            discord._wrap_function_for_normal_command("example_command", test_func)

def test_is_private_channel(bot: DiscordBot, testing_bot: DiscordBot):
    """Test the discord.is_private_channel() method"""

    testing_channel = testing_bot.get_channel(storage.StorageView["test_channel_id"])
    assert testing_channel is not None

    grabber = CTXGrabber()
    grabber.wrap_command("ping")

    testing_bot.loop.create_task(testing_channel.send("niko.ping"))

    while not grabber.is_context_available():
        sleep(1)
    ctx: commands.context.Context = grabber.get_context()

    assert not discord.is_private_channel(ctx)

    # cannot test if is_private_channel actually returns true
    # because private messages between discord bots aren't allowed

# def test_is_slash_command
