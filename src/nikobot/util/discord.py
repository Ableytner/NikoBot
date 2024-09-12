import functools
import inspect
import re

import discord
from discord import app_commands
from discord.ext import commands

from .storage import VolatileStorage

def get_bot() -> commands.Bot:
    if "bot" not in VolatileStorage:
        raise ValueError("'bot' variable not yet set")

    bot = VolatileStorage["bot"]

    if not isinstance(bot, commands.Bot):
        raise TypeError()
    
    return bot

def normal_command(name: str, description: str, hidden: str = False):
    """register the provided method as a normal command"""

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
            # print(f"Command {name} is already registered, skipping...")
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

        print(f"Registered command {name}")

        return wrapper
    return decorator

def hybrid_command(name: str, description: str):
    """register the provided method as both a normal and a slash command"""

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
            # print(f"Command {name} is already registered, skipping...")
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
        eval(fakefunc_code, {"fakefunc": wrapper, "discord": discord}, fakeglobals)
        wrapper_for_slash_command = fakeglobals["func"]
        get_bot().tree.command(
            name=name,
            description=description
        )(wrapper_for_slash_command)

        print(f"Registered command {name}")

        return wrapper
    return decorator

def grouped_hybrid_command(name: str, description: str, command_group: app_commands.Group):
    """register the provided method as both a normal and a slash command of a given command group"""

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
            # print(f"Command {command_group.name}.{name} is already registered, skipping...")
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
        eval(fakefunc_code, {"fakefunc": wrapper, "discord": discord}, fakeglobals)
        wrapper_for_slash_command = fakeglobals["func"]
        command_group.command(
            name=name,
            description=description
        )(wrapper_for_slash_command)

        # register group of not yet registered
        try:
            get_bot().tree.add_command(command_group)
        except discord.app_commands.CommandAlreadyRegistered:
            pass

        print(f"Registered command {command_group.name}.{name}")

        return wrapper
    return decorator

def is_slash_command(ctx: commands.context.Context | discord.interactions.Interaction):
    # for slash commands
    if isinstance(ctx, discord.interactions.Interaction):
        return True

    # for normal commands
    if isinstance(ctx, commands.context.Context):
        return False

    raise Exception(f"Unknown context type {type(ctx)}")

async def reply(ctx: commands.context.Context | discord.interactions.Interaction, *args, **kwargs):
    if not is_slash_command(ctx):
        return await ctx.reply(*args, **kwargs)
    else:
        if not ctx.response.is_done():
            await ctx.response.send_message(*args, **kwargs)
            return await ctx.original_response()
        else:
            raise Exception("Slash commands can only reply once")

async def parse_user(ctx: commands.context.Context | discord.interactions.Interaction, user: str) -> discord.member.Member | None:
    if user == None:
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
            class ConverterCtx():
                def __init__(slf, bot, message) -> None:
                    slf.bot = bot
                    slf.guild = None
                    slf.message = message

            user = await converter.convert(ConverterCtx(get_bot(), ctx.message), user)
        return user
    except:
        pass

    try:
        user: discord.user.User = get_bot().get_user(int(user))
        return user
    except:
        pass
    
    return None
