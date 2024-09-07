from __future__ import annotations

import functools

import discord
from discord import app_commands
from discord.ext import commands

bot: commands.Bot | None = None

def hybrid_command(name: str, description: str):
    """register the provided method as both a normal and a slash command"""

    def decorator(func):
        """The decorator, which is called at program start"""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            """The wrapped function that is called on command execution"""

            # __qualname__ looks like this: <classname>.<methodname>
            cls_name = func.__qualname__.split(".", maxsplit=1)[0]
            cog = bot.cogs[cls_name]
            return await func(cog, *args, **kwargs)

        if bot is None:
            raise ValueError("bot variable is not yet set")

        # for some reason the decorator gets called twice for every command
        # so we skip registratin an already existing command
        if name in [item.name for item in list(bot.commands)]:
            # print(f"Command {name} is already registered, skipping...")
            return wrapper

        # register normal command
        bot.command(
            name=name,
            brief=description,
            description=description
        )(wrapper)

        # register slash command
        bot.tree.command(
            name=name,
            description=description
        )(wrapper)

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
            cog = bot.cogs[cls_name]
            return await func(cog, *args, **kwargs)

        if bot is None:
            raise ValueError("bot variable is not yet set")

        # for some reason the decorator gets called twice for every command
        # so we skip registratin an already existing command
        if f"{command_group.name}.{name}" in [item.name for item in list(bot.commands)]:
            # print(f"Command {command_group.name}.{name} is already registered, skipping...")
            return wrapper

        # register normal command
        bot.command(
            name=f"{command_group.name}.{name}",
            brief=description,
            description=description
        )(wrapper)

        # register slash command
        command_group.command(
            name=name,
            description=description
        )(wrapper)

        # register group of not yet registered
        try:
            bot.tree.add_command(command_group)
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
