# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
# Needed for making pytest fixtures working correctly
# pylint: disable=wrong-import-position

"""
    Pytest configuration
"""
import atexit
import os
import sys
import pathlib

# Adding source path to sys path
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))
sys.path.append(f"{pathlib.Path(__file__).parent.parent}")
sys.path.append(f"{pathlib.Path(__file__).parent}")

from .fixtures import *

from src.nikobot.util.storage import PersistentStorage
#pylint: enable=wrong-import-position

# disable atexit storage saving
atexit.unregister(PersistentStorage._save_to_disk)
