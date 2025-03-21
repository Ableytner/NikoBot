"""A module to start the discord bot"""

import argparse
import json
import os
import shutil
import typing

from abllib import fs, log, storage
from abllib.storage import PersistentStorage, VolatileStorage

from nikobot.discord_bot import DiscordBot

# TODO:
# combine some parts of the mcserver-tools bot and roxy waifu bot
# fix /tc4 path
# write response message if argument is missing (implement in command_failed)
# add README
# create sing module with all music commands
# create command to set manga provider url
# fix manganato search for: oshi no ko, solo leveling, propably a lot more after provider replacement
# create command to list manga with reading status
# replace DEBUG env var with TYPE_CHECKING for testing discord bot startup
# move mal config loading to malnotifier module
# pylint test fails if a file was deleted but not yet committed
# implement abllib.error

if __name__ == "__main__":
    # setup logging
    log.initialize()
    log.add_console_handler()
    log.add_file_handler()

    # https://stackoverflow.com/a/4480202/15436169
    parser = argparse.ArgumentParser("nikobot")
    parser.add_argument("--config",
                        type=str,
                        default="./config.json",
                        help="A config file in json format. A template is contained in the repository.")
    args = parser.parse_args()

    #setup storage
    storage.initialize()

    VolatileStorage["config_file"] = args.config

    if not os.path.isfile(VolatileStorage["config_file"]):
        raise FileNotFoundError("Config file couldn't be found")
    with open(VolatileStorage["config_file"], "r", encoding="utf8") as cf:
        config: dict[str, typing.Any] = json.load(cf)

    VolatileStorage["modules_to_load"] = config["modules"]
    VolatileStorage["discord_token"] = config["discord_token"]

    if "mal.malnotifier" in config["modules"]:
        if "malnotifier" not in config \
           or "client_id" not in config["malnotifier"] \
           or config["malnotifier"]["client_id"] == "":
            raise ValueError("Missing client_id for use with the malnotifier module. " +
                             "You can create one https://myanimelist.net/apiconfig and add it to your config.json.")

        VolatileStorage["mal.client_id"] = config["malnotifier"]["client_id"]

    # setup storage
    storage_dir = fs.absolute(config["storage_dir"])

    VolatileStorage["storage_file"] = os.path.join(storage_dir, "storage.json")

    VolatileStorage["cache_dir"] = os.path.join(storage_dir, "cache")
    os.makedirs(VolatileStorage["cache_dir"], exist_ok=True)

    VolatileStorage["temp_dir"] = os.path.join(storage_dir, "temp")
    shutil.rmtree(VolatileStorage["temp_dir"], ignore_errors=True)
    os.makedirs(VolatileStorage["temp_dir"], exist_ok=True)

    PersistentStorage.load_from_disk()

    bot = DiscordBot()
    VolatileStorage["bot"] = bot
    bot.start_bot()
