"""
    Pytest configuration
"""

# pylint: disable=unused-wildcard-import, wildcard-import, wrong-import-position, wrong-import-order

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
#pylint: enable=unused-wildcard-import, wildcard-import, wrong-import-position, wrong-import-order

# disable atexit storage saving
# pylint: disable-next=protected-access
atexit.unregister(PersistentStorage._save_to_disk)
