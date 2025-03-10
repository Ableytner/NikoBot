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
# pylint: enable=wrong-import-position, wrong-import-order

import atexit
import json
import shutil
import typing

from abllib import fs, log, storage
from abllib.storage import PersistentStorage, VolatileStorage

# setup testing dirs
STORAGE_DIR = fs.absolute(os.path.dirname(__file__), "..", "..", "test_run")

shutil.rmtree(STORAGE_DIR, ignore_errors=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

# setup logs
log.initialize(log.LogLevel.DEBUG)
log.add_file_handler(os.path.join(STORAGE_DIR, "test.log"))

# setup storage
storage.initialize(os.path.join(STORAGE_DIR, "storage.json"))

VolatileStorage["config_file"] = fs.absolute("config.json")

# load config
if not os.path.isfile(VolatileStorage["config_file"]):
    raise FileNotFoundError("Config file couldn't be found")
with open(VolatileStorage["config_file"], "r", encoding="utf8") as cf:
    config: dict[str, typing.Any] = json.load(cf)
if "test" not in config:
    raise ValueError(f"Missing test section in {VolatileStorage['config_file']}. " +
                     "You can find an example in config.template.json, located at the repository root.")


with open(VolatileStorage["storage_file"], "w", encoding="utf8") as f:
    f.write("{}")

VolatileStorage["cache_dir"] = os.path.join(STORAGE_DIR, "cache")
os.makedirs(VolatileStorage["cache_dir"], exist_ok=True)

VolatileStorage["temp_dir"] = os.path.join(STORAGE_DIR, "temp")
shutil.rmtree(VolatileStorage["temp_dir"], ignore_errors=True)
os.makedirs(VolatileStorage["temp_dir"], exist_ok=True)

atexit.unregister(PersistentStorage.save_to_disk)

# pylint: disable-next=unused-import
from .fixtures import setup_storages, bot, testing_bot, ctx_grabber
