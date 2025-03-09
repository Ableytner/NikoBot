"""Module containing the CTXGrabber class"""

import functools
from time import sleep
from typing import Callable

from abllib.log import get_logger
from abllib.storage import VolatileStorage
from discord.ext.commands import Context

from nikobot.discord_bot import DiscordBot

logger = get_logger("test")

class CTXGrabber():
    """Class to obtain a :func:`~discord.ext.commands.Context` during testing"""

    def __init__(self):
        self._ctx: Context = None
        self._command_name = None
        self._original_callback = None

    def is_context_available(self) -> bool:
        """Whether the context can already be retrieved"""

        return self._ctx is not None

    def get_context(self, timeout: int | None = None) -> Context | None:
        """Return the :func:`~discord.ext.commands.Context`, or None if the timeout ran out"""

        # wait forever
        if timeout is None:
            while not self.is_context_available():
                sleep(1)
            return self._ctx

        if not isinstance(timeout, int):
            raise TypeError()

        while not self.is_context_available() and timeout > 0:
            sleep(1)
            timeout -= 1
        return self._ctx

    def wrap_function(self, callback: Callable) -> Callable:
        """Wrap a function to retrieve the :func:`~discord.ext.commands.Context` from"""

        if not callable(callback):
            raise TypeError()

        self._original_callback = callback

        return self._wrap(callback)

    def wrap_command(self, command_name: str) -> None:
        """Wrap a discord bot command to retrieve the :func:`~discord.ext.commands.Context` from"""

        if not isinstance(command_name, str):
            raise TypeError()

        self._command_name = command_name

        bot: DiscordBot = VolatileStorage["bot"]
        cmd = bot.get_command(command_name)

        self._original_callback = cmd.callback

        cmd.callback = self._wrap(cmd.callback)

    def unwrap_command(self) -> None:
        """Unwrap the discord bot command"""

        if self._command_name is None:
            raise TypeError()
        if self._original_callback is None:
            raise TypeError()

        bot: DiscordBot = VolatileStorage["bot"]
        cmd = bot.get_command(self._command_name)

        cmd.callback = self._original_callback

    def _wrap(self, callback):
        @functools.wraps(callback)
        def wrapper(*args, **kwargs):
            if not isinstance(args[0], Context):
                raise TypeError()

            self._ctx = args[0]

            return callback(*args, **kwargs)
        return wrapper
