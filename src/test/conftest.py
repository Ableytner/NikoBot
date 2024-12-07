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

from nikobot.util import storage

logger = logging.getLogger("test")

# disable atexit storage saving
atexit.unregister(storage.PersistentStorage._save_to_disk)

MODULES = ["general", "help", "clear", "music", "avatar", "owner", "tc4.tc4", "mal.malnotifier"]
STORAGE_DIR = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "test_run").resolve())
STORAGE_FILE = os.path.join(STORAGE_DIR, "storage.json")
CACHE_DIR = os.path.join(STORAGE_DIR, "cache")
TEMP_DIR = os.path.join(STORAGE_DIR, "temp")

if "test_channel_id" not in storage.VolatileStorage:
    channel_id_file = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "test_channel_id.txt").resolve())
    if not os.path.isfile(channel_id_file):
        raise FileNotFoundError()
    with open(channel_id_file, "r", encoding="utf8") as file:
        storage.VolatileStorage["test_channel_id"] = file.readline()

storage.VolatileStorage["test_channel_id"] = 1314744187224195183

storage.VolatileStorage["modules_to_load"] = MODULES

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

# pylint: disable-next=unused-import
from .fixtures import setup_storages, bot, testing_bot
