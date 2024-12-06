"""
    Pytest configuration
"""

# pylint: disable=unused-wildcard-import, wildcard-import, wrong-import-position, wrong-import-order, protected-access

# set debug mode
import os
os.environ["DEBUG"] = "True"

# Adding source path to sys path
import sys
import pathlib
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))
sys.path.append(f"{pathlib.Path(__file__).parent.parent}")
sys.path.append(f"{pathlib.Path(__file__).parent}")

# logging needs to be setup before any local imports
from nikobot.util import log_helper
log_helper.setup_for_tests()

# pylint: enable=wrong-import-position, wrong-import-order

import atexit
import logging
import shutil
import _thread
from threading import Thread
from time import sleep

from nikobot.discord_bot import DiscordBot
from nikobot.util import error, storage
# pylint: disable-next=unused-import
from .fixtures import setup_storages, bot

logger = logging.getLogger('test')

# disable atexit storage saving
atexit.unregister(storage.PersistentStorage._save_to_disk)

MODULES = ["general", "help", "clear", "music", "avatar", "owner", "tc4.tc4", "mal.malnotifier"]
STORAGE_DIR = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "test_run").resolve())
STORAGE_FILE = os.path.join(STORAGE_DIR, "storage.json")
CACHE_DIR = os.path.join(STORAGE_DIR, "cache")
TEMP_DIR = os.path.join(STORAGE_DIR, "temp")

# setup testing dirs
shutil.rmtree(STORAGE_DIR, ignore_errors=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

storage.VolatileStorage["storage_file"] = STORAGE_FILE
with open(STORAGE_FILE, "w", encoding="utf8") as f:
    f.write("{}")

storage.VolatileStorage["cache_dir"] = CACHE_DIR
os.makedirs(CACHE_DIR, exist_ok=True)

storage.VolatileStorage["temp_dir"] = TEMP_DIR
os.makedirs(TEMP_DIR, exist_ok=True)

def setup_bot():
    """Setup the main discord bot for testing"""

    if "DISCORD_TOKEN" not in os.environ:
        token_file = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "dc_token_test.txt").resolve())
        if not os.path.isfile(token_file):
            raise error.MissingToken()
        with open(token_file, "r", encoding="utf8") as file:
            os.environ["DISCORD_TOKEN"] = file.readline()

    if "mal.malnotifier" in MODULES and "MAL_CLIENT_ID" not in os.environ:
        mal_client_file = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "client_id.txt").resolve())
        if not os.path.isfile(mal_client_file):
            raise FileNotFoundError()
        with open(mal_client_file, "r", encoding="utf8") as file:
            os.environ["MAL_CLIENT_ID"] = file.readline()

    bot_ready = [False]
    async def on_ready(self: DiscordBot):
        logger.info(f"{self.user} is now online")
        bot_ready[0] = True
    DiscordBot.on_ready = on_ready

    storage.VolatileStorage["modules_to_load"] = MODULES

    bot_obj = DiscordBot()
    storage.VolatileStorage["bot"] = bot_obj

    def thread_func():
        try:
            bot_obj.start_bot()
        # pylint: disable-next=broad-exception-caught
        except Exception as e:
            logger.exception(e)
            _thread.interrupt_main()
    Thread(target=thread_func, daemon=True).start()

    while not bot_ready[0]:
        logger.info("waiting for bot to start...")
        sleep(1)

setup_bot()
