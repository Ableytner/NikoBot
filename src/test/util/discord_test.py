"""Module containing tests for the discord helper functions"""

# pylint: disable=protected-access, missing-class-docstring, pointless-statement, expression-not-assigned, unused-argument

import inspect

from abllib.log import get_logger
from abllib.storage import StorageView
import pytest
import discord as discordpy
from discord.ext import commands

from nikobot.util import discord, general
from nikobot.discord_bot import DiscordBot
from ..helpers import CTXGrabber

logger = get_logger("test")

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

def test_is_cog_loaded(bot: DiscordBot):
    """Test the discord.is_cog_loaded() method"""

    assert discord.is_cog_loaded("help")
    assert not discord.is_cog_loaded("invalid")
    assert not discord.is_cog_loaded("")

def test_is_owner(bot: DiscordBot):
    """Test the discord.is_owner() method"""

    assert general.sync(discord.is_owner(650587171375284226), bot.loop)
    assert not general.sync(discord.is_owner(650587199375284226), bot.loop)
    assert not general.sync(discord.is_owner(468720945692147712), bot.loop)

def test_is_private_channel(bot: DiscordBot, testing_bot: DiscordBot, ctx_grabber: CTXGrabber):
    """
    Test the discord.is_private_channel() method
    We cannot test if is_private_channel actually returns True in private channels
    because private messages between discord bots aren't allowed
    """

    testing_channel = testing_bot.get_channel(StorageView["test_channel_id"])
    assert testing_channel is not None

    ctx_grabber.wrap_command("ping")

    general.sync(testing_channel.send("niko.ping"), testing_bot.loop)

    ctx: commands.context.Context = ctx_grabber.get_context(30)
    assert ctx is not None

    assert not discord.is_private_channel(ctx)

def test_is_slash_command(bot: DiscordBot, testing_bot: DiscordBot, ctx_grabber: CTXGrabber):
    """
    Test the discord.is_slash_command() method
    We cannot test if is_slash_command actually returns False for slash commands
    because discord bots can't initiate them
    """

    testing_channel = testing_bot.get_channel(StorageView["test_channel_id"])
    assert testing_channel is not None

    ctx_grabber.wrap_command("ping")

    general.sync(testing_channel.send("niko.ping"), testing_bot.loop)

    ctx: commands.context.Context = ctx_grabber.get_context(30)
    assert ctx is not None

    assert not discord.is_slash_command(ctx)

def test_is_sent_by_owner(bot: DiscordBot, testing_bot: DiscordBot, ctx_grabber: CTXGrabber):
    """
    Test the discord.is_sent_by_owner() method
    We cannot test if is_sent_by_owner actually returns True
    because the discord bot doesn't own the other bot
    """

    testing_channel = testing_bot.get_channel(StorageView["test_channel_id"])
    assert testing_channel is not None

    ctx_grabber.wrap_command("ping")

    general.sync(testing_channel.send("niko.ping"), testing_bot.loop)

    ctx: commands.context.Context = ctx_grabber.get_context(30)
    assert ctx is not None

    assert not general.sync(discord.is_sent_by_owner(ctx))

def test_channel_message(bot: DiscordBot, testing_bot: DiscordBot):
    """Test the discord.channel_message() method"""

    general.sync(discord.channel_message(StorageView["test_channel_id"], content="the message content"))

    testing_channel = testing_bot.get_channel(StorageView["test_channel_id"])
    assert testing_channel is not None

    async def get_last_message():
        async for message in testing_channel.history(limit=1):
            return message
        raise ValueError()

    last_message: discordpy.Message = general.sync(get_last_message(), testing_bot.loop)
    assert last_message is not None

    assert last_message.content == "the message content"

def test_parse_user(bot: DiscordBot, testing_bot: DiscordBot, ctx_grabber: CTXGrabber):
    """Test the discord.parse_user() method"""

    testing_channel = testing_bot.get_channel(StorageView["test_channel_id"])
    assert testing_channel is not None

    ctx_grabber.wrap_command("ping")

    general.sync(testing_channel.send("niko.ping"), testing_bot.loop)

    ctx: commands.context.Context = ctx_grabber.get_context(30)
    assert ctx is not None

    user: discordpy.Member = general.sync(discord.parse_user(ctx, "ableytner"))
    assert user.id == 650587171375284226

    user: discordpy.Member = general.sync(discord.parse_user(ctx, "Ableytner"))
    assert user.id == 650587171375284226

    user: discordpy.Member = general.sync(discord.parse_user(ctx, "\"Ableytner\""))
    assert user.id == 650587171375284226

    user: discordpy.Member = general.sync(discord.parse_user(ctx, 650587171375284226))
    assert user.id == 650587171375284226

    user: discordpy.Member = general.sync(discord.parse_user(ctx, None))
    assert user is None

def test_username(bot: DiscordBot, testing_bot: DiscordBot, ctx_grabber: CTXGrabber):
    """Test the discord.username() method"""

    testing_channel = testing_bot.get_channel(StorageView["test_channel_id"])
    assert testing_channel is not None

    ctx_grabber.wrap_command("ping")

    general.sync(testing_channel.send("niko.ping"), testing_bot.loop)

    ctx: commands.context.Context = ctx_grabber.get_context(30)
    assert ctx is not None

    assert isinstance(discord.username(ctx), str)
    assert discord.username(ctx) == "AbleytnersTestBot"
