"""Module containing general functionality which works for both 'normal' text commands and slash commands"""

import asyncio
import functools
import inspect
import logging
import re

import discord as discordpy
from discord import app_commands
from discord.ext import commands

from . import error
from .storage import VolatileStorage

logger = logging.getLogger("core")

def get_command_name(ctx: commands.context.Context | discordpy.interactions.Interaction) -> str:
    """Return the full name of the contexts' command"""

    if not is_slash_command(ctx):
        return ctx.command.qualified_name

    return ctx.command.qualified_name

def get_bot() -> commands.Bot:
    """Return the ``DiscordBot`` instance"""

    if "bot" not in VolatileStorage:
        raise ValueError("'bot' variable not yet set")

    bot = VolatileStorage["bot"]

    if not isinstance(bot, commands.Bot):
        raise TypeError()

    return bot

def get_owner_id() -> int:
    """Return the discord bot owners' user_id"""

    return 650587171375284226

async def get_reply(ctx: commands.context.Context | discordpy.interactions.Interaction) \
          -> discordpy.Message | discordpy.interactions.InteractionMessage | None:
    """Return the reply message for the given context, or None if the bot didn't reply yet"""

    if not is_slash_command(ctx):
        ctx: commands.context.Context = ctx
        async for message in ctx.channel.history(limit=100):
            if message.reference is not None and message.reference.message_id == ctx.message.id:
                return message
        return None

    if not ctx.response.is_done():
        return None

    return await ctx.original_response()

def get_user_id(ctx: commands.context.Context | discordpy.interactions.Interaction) -> int:
    """Get discords user id from the message's sender"""

    if not is_slash_command(ctx):
        return ctx.author.id

    return ctx.user.id

def normal_command(name: str, description: str, hidden: str = False):
    """Register the provided method as a normal command"""

    def decorator(func):
        """The decorator, which is called at program start"""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            """The wrapped function that is called on command execution"""

            # __qualname__ looks like this: <classname>.<methodname>
            cls_name = func.__qualname__.split(".", maxsplit=1)[0]
            cog = get_bot().cogs[cls_name]
            return await func(cog, *args, **kwargs)

        if get_bot() is None:
            raise ValueError("bot variable is not yet set")

        # for some reason the decorator gets called twice for every command
        # so we skip registratin an already existing command
        if name in [item.name for item in list(get_bot().commands)]:
#           logger.warning(f"Command {name} is already registered, skipping...")
            return wrapper

        # add hidden attribute to hide command from help
        if hidden:
            desc = "__hidden__" + description
        else:
            desc = description

        # register normal command
        get_bot().command(
            name=name,
            brief=desc,
            description=desc
        )(wrapper)

        logger.debug(f"Registered command {name}")

        return wrapper
    return decorator

def hybrid_command(name: str, description: str):
    """Register the provided method as both a normal and a slash command"""

    def decorator(func):
        """The decorator, which is called at program start"""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            """The wrapped function that is called on command execution"""

            # __qualname__ looks like this: <classname>.<methodname>
            cls_name = func.__qualname__.split(".", maxsplit=1)[0]
            cog = get_bot().cogs[cls_name]
            return await func(cog, *args, **kwargs)

        if get_bot() is None:
            raise ValueError("bot variable is not yet set")

        # for some reason the decorator gets called twice for every command
        # so we skip registratin an already existing command
        if name in [item.name for item in list(get_bot().commands)]:
#           logger.warning(f"Command {name} is already registered, skipping...")
            return wrapper

        # register normal command
        get_bot().command(
            name=name,
            brief=description,
            description=description
        )(wrapper)

        # register slash command
        # replace signature
        sig = str(inspect.signature(wrapper)).replace("self, ", "")
        # replace *<some_arg>: list[str] with <some_arg>: str
        sig = re.sub(r"\*(.+): list\[str\]", r"\1: str", sig).strip("()")
        sig_without_types = re.sub(r": .+[,]", ",", sig)
        sig_without_types = re.sub(r": .+[\006]", "", sig_without_types + "\006")
        # eval function with new signature
        # code from https://stackoverflow.com/a/1409496/15436169
        fakefunc = f"async def func({sig}):\n    return await fakefunc({sig_without_types})"
        fakefunc_code = compile(fakefunc, "fakesource", "exec")
        fakeglobals = {}
        # pylint: disable-next=eval-used
        eval(fakefunc_code, {"fakefunc": wrapper, "discord": discordpy}, fakeglobals)
        wrapper_for_slash_command = fakeglobals["func"]
        get_bot().tree.command(
            name=name,
            description=description
        )(wrapper_for_slash_command)

        logger.debug(f"Registered command {name}")

        return wrapper
    return decorator

def grouped_hybrid_command(name: str, description: str, command_group: app_commands.Group):
    """Register the provided method as both a normal and a slash command of a given command group"""

    def decorator(func):
        """The decorator, which is called at program start"""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            """The wrapped function that is called on command execution"""

            # __qualname__ looks like this: <classname>.<methodname>
            cls_name = func.__qualname__.split(".", maxsplit=1)[0]
            cog = get_bot().cogs[cls_name]
            return await func(cog, *args, **kwargs)

        if get_bot() is None:
            raise ValueError("bot variable is not yet set")

        # for some reason the decorator gets called twice for every command
        # so we skip registratin an already existing command
        if f"{command_group.name}.{name}" in [item.name for item in list(get_bot().commands)]:
#           logger.warning(f"Command {command_group.name}.{name} is already registered, skipping...")
            return wrapper

        # register normal command
        get_bot().command(
            name=f"{command_group.name}.{name}",
            brief=description,
            description=description
        )(wrapper)

        # register slash command
        # replace signature
        sig = str(inspect.signature(wrapper)).replace("self, ", "")
        # replace *<some_arg>: list[str] with <some_arg>: str
        sig = re.sub(r"\*(.+): list\[str\]", r"\1: str", sig).strip("()")
        sig_without_types = re.sub(r": .+[,]", ",", sig)
        sig_without_types = re.sub(r": .+[\006]", "", sig_without_types + "\006")
        # eval function with new signature
        # code from https://stackoverflow.com/a/1409496/15436169
        fakefunc = f"async def func({sig}):\n    return await fakefunc({sig_without_types})"
        fakefunc_code = compile(fakefunc, "fakesource", "exec")
        fakeglobals = {}
        # pylint: disable-next=eval-used
        eval(fakefunc_code, {"fakefunc": wrapper, "discord": discordpy}, fakeglobals)
        wrapper_for_slash_command = fakeglobals["func"]
        command_group.command(
            name=name,
            description=description
        )(wrapper_for_slash_command)

        # register group of not yet registered
        try:
            get_bot().tree.add_command(command_group)
        except discordpy.app_commands.CommandAlreadyRegistered:
            pass

        logger.debug(f"Registered command {command_group.name}.{name}")

        return wrapper
    return decorator

def is_private_channel(ctx: commands.context.Context | discordpy.interactions.Interaction) -> bool:
    """Checks whether the message related to ``ctx`` was received as a private / direct message"""

    if is_slash_command(ctx):
        return isinstance(ctx.channel, discordpy.channel.DMChannel)

    return isinstance(ctx.channel, discordpy.channel.DMChannel)

def is_slash_command(ctx: commands.context.Context | discordpy.interactions.Interaction) -> bool:
    """Checks whether the ``ctx`` was received from a 'normal' text command or a slash command"""

    # for slash commands
    if isinstance(ctx, discordpy.interactions.Interaction):
        return True

    # for normal commands
    if isinstance(ctx, commands.context.Context):
        return False

    raise TypeError(f"Unknown context type {type(ctx)}")

def is_sent_by_owner(ctx: commands.context.Context | discordpy.interactions.Interaction) -> bool:
    """
    Checks whether the message related to the ``ctx`` is sent by one of the bot's owners
    
    This is really only used for testing
    """

    if is_slash_command(ctx):
        return asyncio.run_coroutine_threadsafe(get_bot().is_owner(ctx.user), get_bot().loop)

    return asyncio.run_coroutine_threadsafe(get_bot().is_owner(ctx.author), get_bot().loop)

async def reply(ctx: commands.context.Context | discordpy.interactions.Interaction, *args, **kwargs) \
          -> discordpy.Message | discordpy.interactions.InteractionMessage:
    """
    Send a reply in the current context
    
    The ``args`` and ``kwargs`` are passed on as-is
    """

    if not is_slash_command(ctx):
        return await ctx.reply(*args, **kwargs)

    if ctx.response.is_done():
        raise error.MultipleReplies()

    await ctx.response.send_message(*args, **kwargs)
    return await ctx.original_response()

async def private_message(user_id: int, *args, **kwargs) \
          -> discordpy.Message | discordpy.interactions.InteractionMessage:
    """
    Send a private message to a discord user, specified via his user id
    
    The ``args`` and ``kwargs`` are passed on as-is
    """

    user = get_bot().get_user(user_id)
    if user is None:
        raise error.UserNotFound()

    await user.send(*args, **kwargs)

async def parse_user(ctx: commands.context.Context | discordpy.interactions.Interaction, user: str) \
          -> discordpy.member.Member | None:
    """
    Convert a given string to a ``discord.member.Member``
    
    The string can be either a username, server nickname or user id
    """

    if user is None:
        return None

    if isinstance(user, str):
        user = user.strip('"')

    try:
        # convert string to user
        converter = commands.MemberConverter()
        if not is_slash_command(ctx):
            user = await converter.convert(ctx, user)
        else:
            # this is stupid, but it works
            # pylint: disable-next=missing-class-docstring
            class ConverterCtx():
                def __init__(self, bot, message) -> None:
                    self.bot = bot
                    self.guild = None
                    self.message = message

            user = await converter.convert(ConverterCtx(get_bot(), ctx.message), user)
        return user
    except:
        pass

    try:
        user: discordpy.user.User = get_bot().get_user(int(user))
        return user
    except:
        pass

    return None
