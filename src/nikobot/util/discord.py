"""Module containing general functionality which works for both 'normal' text commands and slash commands"""

import asyncio
import functools
import inspect
import logging
import re
import typing

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
        )(_wrap_function_for_normal_command(name, wrapper))

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
        )(_wrap_function_for_normal_command(name, wrapper))

        get_bot().tree.command(
            name=name,
            description=description
        )(_wrap_function_for_slash_command(name, wrapper))

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
        )(_wrap_function_for_normal_command(f"{command_group.name}.{name}", wrapper))

        # register slash command
        command_group.command(
            name=name,
            description=description
        )(_wrap_function_for_slash_command(f"{command_group.name}.{name}", wrapper))

        # register group of not yet registered
        try:
            get_bot().tree.add_command(command_group)
        except discordpy.app_commands.CommandAlreadyRegistered:
            pass

        logger.debug(f"Registered command {command_group.name}.{name}")

        return wrapper
    return decorator

def _wrap_function_for_normal_command(command_name: str, func: typing.Callable) -> typing.Callable:
    """Wrap a given function for use with normal command registration"""

    # the signature looks like this:
    # (self, ctx, <some_arg>: <some_type>, <another_arg>: <another_type>)
    sig = str(inspect.signature(func))

    # remove self from args and remove brackets
    sig = sig.replace("self, ", "").strip("()")

    args = sig.split(",")

    # clean up type hints for later replacements
    for c in range(len(args)):
        arg = args[c]

        arg = arg.strip()

        if "None | str" in arg:
            arg = arg.replace("None | str", "str | None")

        args[c] = arg

    valid_strings = [
        [": str", 0],
        [": str | None = None", 0]
    ]
    for arg in args:
        # optional parameters can't be placed before normal parameters
        if valid_strings[1][1] > 0 and valid_strings[0][0] in arg:
            raise SyntaxError(f"Command {command_name} contains optional str parameter before normal str parameter")

        if valid_strings[1][0] in arg:
            valid_strings[1][1] += 1
        elif valid_strings[0][0] in arg:
            valid_strings[0][1] += 1

#    if valid_strings[1][1] > 1:
#        raise SyntaxError(f"Command {command_name} contains more than one optional str parameters")

    # replace str type hints
    num_of_strings = sum([item[1] for item in valid_strings])
    if num_of_strings > 0:
        if num_of_strings == 1:
            for c in range(len(args)):
                arg = args[c]

                # replace '<some_arg>: str | None = None' with '*<some_arg>: list[str] | None'
                if ": str | None = None" in arg:
                    arg = "*" + arg.replace(": str | None = None", ": list[str] | None")
                # replace '<some_arg>: str' with '*<some_arg>: list[str]'
                elif ": str" in arg:
                    arg = "*" + arg.replace(": str", ": list[str]")

                args[c] = arg
        # if multiple str parameters are present, only replace the last one
        else:
            arg = args[-1]

            # replace '<some_arg>: str | None = None' with '*<some_arg>: list[str] | None'
            if ": str | None = None" in arg:
                arg = "*" + arg.replace(": str | None = None", ": list[str] | None")
            # replace '<some_arg>: str' with '*<some_arg>: list[str]'
            elif ": str" in arg:
                arg = "*" + arg.replace(": str", ": list[str]")

            args[-1] = arg

    sig = ", ".join(args)
    sig_without_types = _remove_type_hints(sig)

    fakefunc = [
        f"async def func({sig}):"
    ]

    # check if sig contains a string that has to be recombined
    if num_of_strings == 1:
        name_matches = re.search(r"\*(.+): list\[str\]", sig)
        if name_matches is None:
            raise RuntimeError()

        arg_name = name_matches.group(1)

        sig_without_types = sig_without_types.replace(f" {arg_name}", f" {arg_name}_recombined")

        fakefunc.append(f"    if len({arg_name}) > 0:")
        fakefunc.append(f"        {arg_name}_recombined = ' '.join([''.join(item) for item in {arg_name}])")
        fakefunc.append(f"    else:")

        if re.search(r"\*(.+): list\[str\] \| None", sig):
            fakefunc.append(f"        {arg_name}_recombined = None")
        else:
            fakefunc.append(f"        raise error.MissingRequiredArgument(ctx.command.params['{arg_name}'])")
#           fakefunc.append(f"        get_bot().dispatch('command_error', ctx, exc)")
    elif num_of_strings > 1:
        # if all str parameters are normal
        if valid_strings[1][1] == 0:
            arg_names = re.findall(r"([^ ]+): str", sig)
            arg_names += re.findall(r"\*(.+): list\[str\]", sig)
            if len(arg_names) != valid_strings[0][1]:
                raise RuntimeError()

            fakefunc.append(f"    parts = []")
            for arg_name in arg_names:
                if arg_name != arg_names[-1]:
                    fakefunc.append(f"    parts.append({arg_name})")
                else:
                    fakefunc.append(f"    parts += [''.join(item) for item in {arg_name}]")
                    fakefunc.append(f"    logger.info(parts)")

            fakefunc.append(f"    if len(parts) > {len(arg_names)}:")
            fakefunc.append(f"        raise error.TooManyArguments('Command ' + str(ctx.invoked_with) + ' received ' + str(len(parts)) + ' arguments, but only expected {len(arg_names)}')")

            for c, arg_name in enumerate(arg_names):
                sig_without_types = sig_without_types.replace(f" {arg_name}", f" {arg_name}_recombined")
                fakefunc.append(f"    if {c} >= len(parts):")
                fakefunc.append(f"        raise error.MissingRequiredArgument(ctx.command.params['{arg_name}'])")
                fakefunc.append(f"    {arg_name}_recombined = parts[{c}]")

        # if the last str parameter is optional
        elif valid_strings[1][1] == 1:
            arg_names = re.findall(r"\*(.+): str", sig)
            arg_names += re.findall(r"\*(.+): list\[str\] \| None", sig)
            if len(arg_names) != valid_strings[0][1] + valid_strings[1][1]:
                raise RuntimeError()

            fakefunc.append(f"    parts = []")
            for arg_name in arg_names:
                if arg_name != arg_names[-1]:
                    fakefunc.append(f"    parts.append({arg_name})")
                else:
                    fakefunc.append(f"    parts += {arg_name}")

            for c, arg_name in enumerate(arg_names):
                sig_without_types = sig_without_types.replace(f" {arg_name}", f" {arg_name}_recombined")
                if c < len(arg_names) - 1:
                    fakefunc.append(f"    if {c} >= len(parts):")
                    fakefunc.append(f"        raise error.MissingRequiredArgument({arg_name})")
                    fakefunc.append(f"    {arg_name}_recombined = parts[{c}]")
                else:
                    fakefunc.append(f"    {arg_name}_recombined = ' '.join(parts[{c}:])")
        # if multiple str parameters are optional
        else:
            arg_names = re.findall(r"\*(.+): str", sig)
#            arg_names += re.findall(r"\*(.+): str \| None", sig)
            arg_names += re.findall(r"\*(.+): list\[str\] \| None", sig)
            if len(arg_names) != valid_strings[0][1] + valid_strings[1][1]:
                raise RuntimeError()

            fakefunc.append(f"    parts = []")
            for arg_name in arg_names:
                if arg_name != arg_names[-1]:
                    fakefunc.append(f"    parts.append({arg_name})")
                else:
                    fakefunc.append(f"    parts += {arg_name}")

            for c, arg_name in enumerate(arg_names):
                sig_without_types = sig_without_types.replace(f" {arg_name}", f" {arg_name}_recombined")
                if c < len(arg_names) - 1:
                    fakefunc.append(f"    {arg_name}_recombined = parts[{c}] if len(parts) > {c} else None")
                else:
                    fakefunc.append(f"    {arg_name}_recombined = ' '.join(parts[{c}:])")

    fakefunc.append(f"    return await original_func({sig_without_types})")

    fakefunc_code = compile("\n".join(fakefunc), "fakesource", "exec")
    locals = {}
    # pylint: disable-next=eval-used
    eval(fakefunc_code,
        {
            "original_func": func,
            "discord": discordpy,
            "error": error,
            "logger": logger,
            "get_bot": get_bot
        },
        locals
    )
    return locals["func"]

def _wrap_function_for_slash_command(command_name: str, func: typing.Callable) -> typing.Callable:
    """Wrap a given function for use with slash command registration"""

    # the signature looks like this:
    # (self, ctx, <some_arg>: <some_type>, <another_arg>: <another_type>)
    sig = str(inspect.signature(func))

    # remove self from args and remove brackets
    sig = sig.replace("self, ", "").strip("()")

    sig_without_types = _remove_type_hints(sig)

    fakefunc = [
        f"async def func({sig}):",
        f"    return await original_func({sig_without_types})"
    ]

    fakefunc_code = compile("\n".join(fakefunc), "fakesource", "exec")
    locals = {}
    # pylint: disable-next=eval-used
    eval(fakefunc_code,
        {
            "original_func": func,
            "discord": discordpy,
            "get_bot": get_bot
        },
        locals
    )
    return locals["func"]

def _compile_func(func: typing.Callable, signature: str) -> typing.Callable:
    """
    Compile the given signature to a function calling func
    Base code from https://stackoverflow.com/a/1409496/15436169
    """

    sig_without_types = _remove_type_hints(signature)

    fakefunc = [
        f"async def func({signature}):"
    ]

    # check if sig contains a string which has to be recombined
    name_matches = re.match(r"\*(.+): list\[str\]", signature)
    if name_matches is not None:
        arg_name = name_matches.string

        sig_without_types = sig_without_types.replace(arg_name, f"{arg_name}_recombined")

        fakefunc.append(f"    if len({arg_name}) > 0:")
        fakefunc.append(f"        {arg_name}_recombined = ' '.join([''.join(item) for item in {arg_name}])")
        fakefunc.append(f"    else:")

        if re.match(r"\*(.+): list\[str\] \| None", signature):
            fakefunc.append(f"        {arg_name}_recombined = None")
        else:
            fakefunc.append(f"        exc = discordpy.errors.CommandNotFound('Command ' + str(ctx.invoked_with) + ' is not found')")
            fakefunc.append(f"        get_bot().dispatch('command_error', ctx, exc)")

    fakefunc.append(f"    return await original_func({sig_without_types})")

    fakefunc_code = compile("\n".join(fakefunc), "fakesource", "exec")
    locals = {}
    # pylint: disable-next=eval-used
    eval(fakefunc_code,
        {
            "original_func": func,
            "discord": discordpy,
            "get_bot": get_bot
        },
        locals
    )
    return locals["func"]

def _remove_type_hints(signature: str) -> str:
    args = signature.split(",")

    for c in range(len(args)):
        arg = args[c]

        arg = arg.strip()
        arg = arg.replace("*", "")
        arg = arg.split(":")[0]

        args[c] = arg

    return ", ".join(args)

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
