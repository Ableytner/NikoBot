"""A module to start the discord bot"""

# pylint: disable=protected-access, wrong-import-position, wrong-import-order

# logging needs to be setup before any local imports
from nikobot.util import log_helper
log_helper.setup()

# pylint: enable=wrong-import-position, wrong-import-order

import argparse
import json
import os
import pathlib
import shutil
import typing

from nikobot import util
from nikobot.discord_bot import DiscordBot

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
# add lock for threaded Storage access
# replace DEBUG env var with TYPE_CHECKING for testing discord bot startup
# support multiple optional str args in normal commands

if __name__ == "__main__":
    # https://stackoverflow.com/a/4480202/15436169
    parser = argparse.ArgumentParser("nikobot")
    parser.add_argument("--config",
                        type=str,
                        default="./config.json",
                        help="A config file in json format. A template is contained in the repository.")
    args = parser.parse_args()
    util.VolatileStorage["config_file"] = args.config

    if not os.path.isfile(util.VolatileStorage["config_file"]):
        raise FileNotFoundError("Config file couldn't be found")
    with open(util.VolatileStorage["config_file"], "r", encoding="utf8") as cf:
        config: dict[str, typing.Any] = json.load(cf)

    util.VolatileStorage["modules_to_load"] = config["modules"]
    util.VolatileStorage["discord_token"] = config["discord_token"]

    if "mal.malnotifier" in config["modules"]:
        if "malnotifier" not in config \
           or "client_id" not in config["malnotifier"] \
           or config["malnotifier"]["client_id"] == "":
            raise ValueError("Missing client_id for use with the malnotifier module. " +
                             "You can create one https://myanimelist.net/apiconfig and add it to your config.json.")

        util.VolatileStorage["mal.client_id"] = config["malnotifier"]["client_id"]

    # setup storage
    storage_dir = str(pathlib.Path(config["storage_dir"]).resolve())

    util.VolatileStorage["storage_file"] = os.path.join(storage_dir, "storage.json")
    util.PersistentStorage._load_from_disk()

    util.VolatileStorage["cache_dir"] = os.path.join(storage_dir, "cache")
    os.makedirs(util.VolatileStorage["cache_dir"], exist_ok=True)

    util.VolatileStorage["temp_dir"] = os.path.join(storage_dir, "temp")
    shutil.rmtree(util.VolatileStorage["temp_dir"], ignore_errors=True)
    os.makedirs(util.VolatileStorage["temp_dir"], exist_ok=True)

    bot = DiscordBot()
    util.VolatileStorage["bot"] = bot
    bot.start_bot()
