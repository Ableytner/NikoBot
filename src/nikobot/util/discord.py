"""Module containing general functionality which works for both 'normal' text commands and slash commands"""

import functools
import inspect
import re
import typing

from abllib.log import get_logger
from abllib.storage import VolatileStorage
import discord as discordpy
from discord import app_commands
from discord.ext import commands

from . import error

logger = get_logger("core")

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

        # for some reason the decorator gets called twice for every command
        # so we skip registrating an already existing command
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

        # for some reason the decorator gets called twice for every command
        # so we skip registrating an already existing command
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

        # register command group if not yet registered
        try:
            get_bot().tree.add_command(command_group)
        except discordpy.app_commands.CommandAlreadyRegistered:
            pass

        logger.debug(f"Registered command {command_group.name}.{name}")

        return wrapper
    return decorator

# pylint: disable=f-string-without-interpolation

# pylint: disable-next=too-many-statements
def _wrap_function_for_normal_command(command_name: str, func: typing.Callable) -> typing.Callable:
    """Wrap a given function for use with normal command registration"""

    # ----------------------------------------------------------------------------------------------------
    # setup warpping function signature
    # the original signature looks like this:
    # (self, ctx, <some_arg>: <some_type>, <another_arg>: <another_type>)
    # a concrete example with string args:
    # (self, ctx, firstname: str, secondname: str, extra: str | None)
    sig = str(inspect.signature(func))

    # remove self from args and remove brackets
    sig = sig.replace("self, ", "").strip("()")

    args = sig.split(",")

    # ----------------------------------------------------------------------------------------------------
    # clean up type hints for later replacements
    # a concrete example with string args:
    # (self, ctx, firstname: str, secondname: str, extra: str | None)
    for c, arg in enumerate(args):
        arg = arg.strip()

        if "None | str" in arg:
            arg = arg.replace("None | str", "str | None")

        if ": str | None" in arg \
           and ": str | None = None" not in arg:
            arg = arg.replace(": str | None", ": str | None = None")

        args[c] = arg

    # ----------------------------------------------------------------------------------------------------
    # count number of string arguments
    # raises an SyntaxError if an optional argument
    # <some_arg>: str | None
    # is placed after a required argument
    # <some_arg>: str
    num_of_required_string_args = 0
    num_of_optional_string_args = 0
    for arg in args:
        if ": str" in arg:
            if ": str | None = None" in arg:
                num_of_optional_string_args += 1
            else:
                num_of_required_string_args += 1

            # optional parameters can't be placed before required parameters
            if num_of_optional_string_args > 0 \
               and ": str | None = None" not in arg:
                raise SyntaxError(f"Command {command_name} contains optional str"
                                  + " parameter before required str parameter")

    num_of_string_args = num_of_required_string_args + num_of_optional_string_args

    # ----------------------------------------------------------------------------------------------------
    # replace str type hints
    # a concrete example with string args:
    # (self, ctx, firstname: str, secondname: str, *extra: list[str] | None)
    if num_of_string_args > 0:
        c = len(args)
        while c > 0:
            c -= 1
            arg = args[c]

            # replace
            # <some_arg>: str | None = None
            # with
            # *<some_arg>: list[str] | None
            if ": str | None = None" in arg:
                arg = "*" + arg.replace(": str | None = None", ": list[str] | None")
            # replace
            # <some_arg>: str
            # with
            # *<some_arg>: list[str]
            elif ": str" in arg:
                arg = "*" + arg.replace(": str", ": list[str]")

            # if the argument got replaced, break the loop
            # this way only the last str argument gets replaced
            if arg != args[c]:
                args[c] = arg
                break

    sig = ", ".join(args)

    # ----------------------------------------------------------------------------------------------------
    # extract and store all argument names
    # a concrete example with string args:
    # (self, ctx, firstname: str, secondname: str, *extra: list[str] | None)
    # optional_arg_names:      []
    # required_arg_names:      ["firstname", "secondname"]
    # optional_final_arg_name: "extra"
    # required_final_arg_name: None
    optional_arg_names = re.findall(r"([^ ]+): str \| None", sig)
    required_arg_names = [arg for arg in re.findall(r"([^ ]+): str", sig) if arg not in optional_arg_names]

    optional_final_arg_name = re.findall(r"\*(.+): list\[str\] \| None", sig) or None
    required_final_arg_name = re.findall(r"\*(.+): list\[str\]", sig) or None
    if required_final_arg_name is not None:
        required_final_arg_name = required_final_arg_name[0]
    if optional_final_arg_name is not None:
        optional_final_arg_name = optional_final_arg_name[0]
        required_final_arg_name = None

    # ----------------------------------------------------------------------------------------------------
    # initialize wrapping function
    fakefunc = [f"async def func({sig}):"]
    fakefunc.append(f"    parts = []")

    # ----------------------------------------------------------------------------------------------------
    # add all argument values to the parts list (as words, seperated by " ")
    # the final list looks like this:
    # parts = ["the", "quick", "brown", "fox", "jumps", "over"]
    for arg_name in required_arg_names:
        fakefunc.append(f"    parts.append({arg_name})")
    for arg_name in optional_arg_names:
        fakefunc.append(f"    if {arg_name} is not None:")
        fakefunc.append(f"        parts.append({arg_name})")
    if required_final_arg_name is not None:
        fakefunc.append(f"    parts += [''.join(item) for item in {required_final_arg_name}]")
    if optional_final_arg_name is not None:
        fakefunc.append(f"    parts += [''.join(item) for item in {optional_final_arg_name} if item is not None]")

    fakefunc.append("    for part in parts:")
    fakefunc.append("        if not isinstance(part, str):")
    fakefunc.append("            raise RuntimeError(f'argument {part} is not str in parts: {parts}')")

    # ----------------------------------------------------------------------------------------------------
    # divide argument values upon all arguments
    parts_c = 0
    sig_without_types = _remove_type_hints(sig)

    for arg_name in required_arg_names:
        fakefunc.append(f"    if {parts_c} < len(parts):")
        fakefunc.append(f"        {arg_name}_recombined = parts[{parts_c}]")
        fakefunc.append(f"    else:")
        fakefunc.append(f"        raise error.MissingRequiredArgument(ctx.command.params['{arg_name}'])")

        parts_c += 1

        sig_without_types = sig_without_types.replace(f" {arg_name}",
                                                      f" {arg_name}_recombined")
    if required_final_arg_name is not None:
        fakefunc.append(f"    if {parts_c} < len(parts):")
        fakefunc.append(f"        {required_final_arg_name}_recombined = ' '.join(parts[{parts_c}:])")
        fakefunc.append(f"    else:")
        fakefunc.append(f"        raise error.MissingRequiredArgument(ctx.command.params['{required_final_arg_name}'])")

        parts_c += 1

        sig_without_types = sig_without_types.replace(f" {required_final_arg_name}",
                                                      f" {required_final_arg_name}_recombined")
    for arg_name in optional_arg_names:
        fakefunc.append(f"    if {parts_c} < len(parts):")
        fakefunc.append(f"        {arg_name}_recombined = parts[{parts_c}]")
        fakefunc.append(f"    else:")
        fakefunc.append(f"        {arg_name}_recombined = None")

        parts_c += 1

        sig_without_types = sig_without_types.replace(f" {arg_name}",
                                                      f" {arg_name}_recombined")
    if optional_final_arg_name is not None:
        fakefunc.append(f"    if {parts_c} < len(parts):")
        fakefunc.append(f"        {optional_final_arg_name}_recombined = ' '.join(parts[{parts_c}:])")
        fakefunc.append(f"    else:")
        fakefunc.append(f"        {optional_final_arg_name}_recombined = None")

        parts_c += 1

        sig_without_types = sig_without_types.replace(f" {optional_final_arg_name}",
                                                      f" {optional_final_arg_name}_recombined")

    fakefunc.append(f"    return await original_func({sig_without_types})")

    # ----------------------------------------------------------------------------------------------------
    # compile the wrapping function
    # code from https://stackoverflow.com/a/1409496/15436169
    fakefunc_code = compile("\n".join(fakefunc), "fakesource", "exec")
    fakefunc_locals = {}
    # pylint: disable-next=eval-used
    eval(fakefunc_code,
        {
            "original_func": func,
            "discord": discordpy,
            "error": error
        },
        fakefunc_locals
    )
    return fakefunc_locals["func"]

# pylint: disable-next=unused-argument
def _wrap_function_for_slash_command(command_name: str, func: typing.Callable) -> typing.Callable:
    """Wrap a given function for use with slash command registration"""

    # ----------------------------------------------------------------------------------------------------
    # setup warpping function signature
    # the original signature looks like this:
    # (self, ctx, <some_arg>: <some_type>, <another_arg>: <another_type>)
    sig = str(inspect.signature(func))

    # remove self from args and remove brackets
    sig = sig.replace("self, ", "").strip("()")

    # ----------------------------------------------------------------------------------------------------
    # create wrapping function
    sig_without_types = _remove_type_hints(sig)

    fakefunc = [
        f"async def func({sig}):",
        f"    return await original_func({sig_without_types})"
    ]

    # ----------------------------------------------------------------------------------------------------
    # compile the wrapping function
    # code from https://stackoverflow.com/a/1409496/15436169
    fakefunc_code = compile("\n".join(fakefunc), "fakesource", "exec")
    fakefunc_locals = {}
    # pylint: disable-next=eval-used
    eval(fakefunc_code,
        {
            "original_func": func,
            "discord": discordpy,
            "get_bot": get_bot
        },
        fakefunc_locals
    )
    return fakefunc_locals["func"]

# pylint: enable=f-string-without-interpolation

def _remove_type_hints(signature: str) -> str:
    """Remove all type hints from a function signature"""

    args = signature.split(",")

    for c, arg in enumerate(args):
        arg = arg.strip()
        arg = arg.replace("*", "")
        arg = arg.split(":")[0]

        args[c] = arg

    return ", ".join(args)

def is_cog_loaded(name: str) -> bool:
    """Checks whether the cog with the given name is loaded"""

    return name.lower() in (cog.lower() for cog in get_bot().cogs)

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

async def is_sent_by_owner(ctx: commands.context.Context | discordpy.interactions.Interaction) -> bool:
    """
    Checks whether the message related to the ``ctx`` is sent by one of the bot's owners
    
    This is really only used for testing
    """

    if not is_slash_command(ctx):
        return await get_bot().is_owner(ctx.author)

    return await get_bot().is_owner(ctx.user)

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

async def channel_message(channel_id: int, *args, **kwargs) -> discordpy.Message:
    """
    Send the given text to the given channel
    
    The ``args`` and ``kwargs`` are passed on as-is
    """

    channel = get_bot().get_channel(channel_id)
    return await channel.send(*args, **kwargs)

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
