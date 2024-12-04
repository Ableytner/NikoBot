"""
    Pytest fixtures
"""

# pylint: disable=protected-access

import pytest

from src.nikobot.util import storage

@pytest.fixture(scope="function", autouse=True)
def setup_storages():
    """Setup the PersistentStorage, VolatileStorage and StorageView for test usage"""

    PersistentStorage = storage._PersistentStorage.__new__(storage._PersistentStorage)
    PersistentStorage._store = {}
    storage.PersistentStorage = PersistentStorage
    VolatileStorage = storage._VolatileStorage.__new__(storage._VolatileStorage)
    VolatileStorage._store = {}
    storage.VolatileStorage = VolatileStorage
    StorageView = storage._StorageView([
        storage.PersistentStorage,
        storage.VolatileStorage
    ])
    storage.StorageView = StorageView
