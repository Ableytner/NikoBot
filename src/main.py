"""A module containing the ``DiscordBot`` class"""

# pylint: disable=protected-access, wrong-import-position, wrong-import-order

# logging needs to be setup before any local imports
from nikobot.util import log_helper
log_helper.setup()

# pylint: enable=wrong-import-position, wrong-import-order

import pathlib
import shutil
import os

from nikobot import util
from nikobot.discord_bot import DiscordBot

MODULES = ["general", "help", "clear", "music", "avatar", "owner", "tc4.tc4", "mal.malnotifier"]
STORAGE_DIR = str(pathlib.Path(os.path.dirname(__file__), "..", "storage").resolve())
STORAGE_FILE = os.path.join(STORAGE_DIR, "storage.json")
CACHE_DIR = os.path.join(STORAGE_DIR, "cache")
TEMP_DIR = os.path.join(STORAGE_DIR, "temp")

# TODO:
# combine some parts of the mcserver-tools bot and roxy waifu bot
# fix /tc4 path
# write response message if argument is missing (implement in command_failed)
# tests (maybe with a second discord bot for testing purposes)
# add README
# create sing module with all music commands
# create command to set manga provider url
# fix manganato search for: oshi no ko, solo leveling
# create command to list manga with reading status

if __name__ == "__main__":
    util.VolatileStorage["storage_file"] = STORAGE_FILE
    util.PersistentStorage._load_from_disk()

    util.VolatileStorage["cache_dir"] = CACHE_DIR
    os.makedirs(util.VolatileStorage["cache_dir"], exist_ok=True)

    util.VolatileStorage["temp_dir"] = TEMP_DIR
    shutil.rmtree(util.VolatileStorage["temp_dir"], ignore_errors=True)
    os.makedirs(util.VolatileStorage["temp_dir"], exist_ok=True)

    util.VolatileStorage["modules_to_load"] = MODULES

    bot = DiscordBot()

    util.VolatileStorage["bot"] = bot

    bot.start_bot()
