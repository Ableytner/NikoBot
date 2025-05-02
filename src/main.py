"""A module to start the discord bot"""

import argparse
import json
import os
import shutil
import typing
from time import sleep

from abllib import fs, log, storage
from abllib.pproc import WorkerThread
from abllib.storage import VolatileStorage, PersistentStorage

from nikobot.discord_bot import DiscordBot

# TODO:
# import some parts of the mcserver-tools bot
# import some parts of the roxy waifu bot
# fix /tc4 path
# write response message if argument is missing (implement in command_failed)
# add README
# create sing module with all music commands
# create command to set manga provider url
# fix manganato search for: oshi no ko, solo leveling, propably a lot more after provider replacement
# create command to list manga with reading status
# replace DEBUG env var with TYPE_CHECKING for testing discord bot startup
# move mal config loading to centralized handler
# move all module-specific code to that module (e.g. help module in on_command_error)
# add command to add all songs from all spotify playlists to one playlist, in order of first added
# update to python 3.13

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

    # load config file
    if not os.path.isfile(args.config):
        raise FileNotFoundError("Config file couldn't be found")
    with open(args.config, "r", encoding="utf8") as cf:
        config: dict[str, typing.Any] = json.load(cf)

    # setup storage
    storage_dir = fs.absolute(config["storage_dir"])
    storage.initialize(os.path.join(storage_dir, "storage.json"), True)

    def save_func():
        """Save PersistentStorage every minute"""
        while True:
            PersistentStorage.save_to_disk()
            sleep(60)
    WorkerThread(target=save_func, daemon=True).start()

    VolatileStorage["config_file"] = args.config
    VolatileStorage["modules_to_load"] = config["modules"]
    VolatileStorage["discord_token"] = config["discord_token"]

    if "mal.malnotifier" in config["modules"]:
        if "malnotifier" not in config \
           or "client_id" not in config["malnotifier"] \
           or config["malnotifier"]["client_id"] == "":
            raise ValueError("Missing client_id for use with the malnotifier module. " +
                             "You can create one https://myanimelist.net/apiconfig and add it to your config.json.")

        VolatileStorage["mal.client_id"] = config["malnotifier"]["client_id"]

    if "spotify.spotify" in config["modules"]:
        if "spotify" not in config \
           or "client_id" not in config["spotify"] \
           or config["spotify"]["client_id"] == "":
            raise ValueError("Missing client_id for use with the spotify module. " +
                             "You can create one here https://developer.spotify.com/dashboard " +
                             "and add it to your config.json.")
        if "spotify" not in config \
           or "client_secret" not in config["spotify"] \
           or config["spotify"]["client_secret"] == "":
            raise ValueError("Missing client_secret for use with the spotify module. " +
                             "You can create one here https://developer.spotify.com/dashboard " +
                             "and add it to your config.json.")

        VolatileStorage["spotify.client_id"] = config["spotify"]["client_id"]
        VolatileStorage["spotify.client_secret"] = config["spotify"]["client_secret"]

    # setup storage directories
    VolatileStorage["cache_dir"] = os.path.join(storage_dir, "cache")
    os.makedirs(VolatileStorage["cache_dir"], exist_ok=True)

    VolatileStorage["temp_dir"] = os.path.join(storage_dir, "temp")
    shutil.rmtree(VolatileStorage["temp_dir"], ignore_errors=True)
    os.makedirs(VolatileStorage["temp_dir"], exist_ok=True)

    bot = DiscordBot()
    VolatileStorage["bot"] = bot

    try:
        bot.start_bot()
    except KeyboardInterrupt:
        PersistentStorage.save_to_disk()
