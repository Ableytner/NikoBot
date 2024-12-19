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
import json
import logging
import shutil
import typing

from nikobot.util import storage

logger = logging.getLogger("test")

# disable atexit storage saving
atexit.unregister(storage.PersistentStorage._save_to_disk)

STORAGE_DIR = str(pathlib.Path(os.path.dirname(__file__), "..", "..", "test_run").resolve())
storage.VolatileStorage["config_file"] = "./config.json"

# load config
if not os.path.isfile(storage.VolatileStorage["config_file"]):
    raise FileNotFoundError("Config file couldn't be found")
with open(storage.VolatileStorage["config_file"], "r", encoding="utf8") as cf:
    config: dict[str, typing.Any] = json.load(cf)
if "test" not in config:
    raise ValueError(f"Missing test section in {storage.VolatileStorage['config_file']}. " +
                     "You can find an example in config.template.json, located at the repository root.")

# setup testing dirs
shutil.rmtree(STORAGE_DIR, ignore_errors=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

storage.VolatileStorage["storage_file"] = os.path.join(STORAGE_DIR, "storage.json")
with open(storage.VolatileStorage["storage_file"], "w", encoding="utf8") as f:
    f.write("{}")

storage.VolatileStorage["cache_dir"] = os.path.join(STORAGE_DIR, "cache")
os.makedirs(storage.VolatileStorage["cache_dir"], exist_ok=True)

storage.VolatileStorage["temp_dir"] = os.path.join(STORAGE_DIR, "temp")
shutil.rmtree(storage.VolatileStorage["temp_dir"], ignore_errors=True)
os.makedirs(storage.VolatileStorage["temp_dir"], exist_ok=True)

# pylint: disable-next=unused-import
from .fixtures import setup_storages, bot, testing_bot
