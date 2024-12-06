"""A module containing the logger creation"""

import logging
import sys

import discord as discordpy

def setup():
    """Setup the log handlers"""

    stream_handler = logging.StreamHandler(sys.stderr)
    discordpy.utils.setup_logging(handler=stream_handler,
                                  level=logging.INFO,
                                  root=True)

    file_handler = logging.FileHandler(filename="latest.log", encoding="utf-8", mode="w")
    discordpy.utils.setup_logging(handler=file_handler,
                                  level=logging.INFO,
                                  root=True)
