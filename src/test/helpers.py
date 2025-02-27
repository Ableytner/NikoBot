import logging
import functools
from typing import Callable

from discord.ext.commands import Context

from nikobot.discord_bot import DiscordBot
from nikobot.util import storage

logger = logging.getLogger("test")

class CTXGrabber():
    def __init__(self):
        self._callback = None
        self._command_name = None
        self._ctx: Context = None
    
    def is_context_available(self) -> bool:
        return self._ctx is not None

    def get_context(self) -> Context | None:
        return self._ctx

    def wrap_function(self, callback: Callable) -> Callable:
        if not callable(callback):
            raise TypeError()
        
        return self._wrap(callback)
    
    def wrap_command(self, command_name: str) -> None:
        if not isinstance(command_name, str):
            raise TypeError()
        
        bot: DiscordBot = storage.VolatileStorage["bot"]
        cmd = bot.get_command(command_name)
        cmd.callback = self._wrap(cmd.callback)

    def _wrap(self, callback):
        def wrapper(*args, **kwargs):
            if not isinstance(args[0], Context):
                raise TypeError()

            self._ctx = args[0]

            return callback(*args, **kwargs)
        return wrapper
