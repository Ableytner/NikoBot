"""Module containing VolatileStorage and PersistentStorage"""

from __future__ import annotations

import atexit
import json
import os
from typing import Any

from . import error

class _BaseStorage():
    def __init__(self) -> None:
        raise NotImplementedError()

    _store: dict[str, Any] = None

    def contains_item(self, key: str, item: Any) -> bool:
        """
        Checks whether a key within the storage contains an item
        If 'key' contains a '.', also checks if all sub-dicts exist
        """

        if not isinstance(key, str):
            raise TypeError()

        if not self.contains(key):
            return False
        return item == self[key]

    def contains(self, key: str) -> bool:
        """
        Checks whether a key exists within the storage
        If 'key' contains a '.', also checks if all sub-dicts exist
        """
        # allows checking multi-layer dicts with the following format:
        # util.PersistentStorage["some_module.some_subdict.another_subdict.key"]

        if not isinstance(key, str):
            raise TypeError()

        if "." not in key:
            return key in self._store

        parts = key.split(".")
        curr_dict: dict[str, Any] = self._store
        for c, part in enumerate(parts):
            if part not in curr_dict:
                return False
            # if it isn't the last part
            if c < len(parts) - 1:
                curr_dict: dict[str, Any] = curr_dict[part]

        return parts[-1] in curr_dict

    def __getitem__(self, key: str) -> Any:
        # allows getting multi-layer dicts with the following format:
        # util.PersistentStorage["some_module.some_subdict.another_subdict.key"]

        if not isinstance(key, str):
            raise TypeError()

        if "." not in key:
            if key not in self._store:
                raise error.KeyNotFound("Key not found in storage: " + key)
            return self._store[key]

        parts = key.split(".")
        curr_dict = self._store
        for c, part in enumerate(parts):
            if part not in curr_dict:
                raise error.KeyNotFound("Key not found in storage: " +
                                        ".".join([item if item != part else f"'{item}'" for item in parts]))
            # if it isn't the last part
            if c < len(parts) - 1:
                curr_dict = curr_dict[part]

        return curr_dict[parts[-1]]

    def __setitem__(self, key: str, item: Any) -> None:
        # allows adding multi-layer dicts with the following format:
        # util.PersistentStorage["some_module.some_subdict.another_subdict.key"] = "value"

        if not isinstance(key, str):
            raise TypeError()

        if "." not in key:
            self._store[key] = item
            return

        parts = key.split(".")
        curr_dict = self._store
        for c, part in enumerate(parts):
            # if it isn't the last part
            if c < len(parts) - 1:
                # add a missing dictionary
                if part not in curr_dict:
                    curr_dict[part] = {}
                curr_dict = curr_dict[part]
            else:
                # add the actual value
                curr_dict[part] = item

    def __delitem__(self, key: str) -> None:
        # items can be removed using:
        # del util.PersistentStorage["some_module"]["some_subdict"]["another_subdict"]["key"]
        # or
        # del util.PersistentStorage["some_module.some_subdict.another_subdict.key"]

        if not isinstance(key, str):
            raise TypeError()

        if "." not in key:
            if key not in self._store:
                raise error.KeyNotFound("Key not found in storage: " + key)
            del self._store[key]
            return

        parts = key.split(".")
        curr_dict = self._store
        for c, part in enumerate(parts):
            if part not in curr_dict:
                raise error.KeyNotFound("Key not found in storage: " +
                                        ".".join([item if item != part else f"'{item}'" for item in parts]))

            # if it isn't the last part
            if c < len(parts) - 1:
                # if a directory is missing, the key definitly doesn't exist
                if part not in curr_dict:
                    return
                curr_dict = curr_dict[part]
            else:
                # delete the actual key
                del curr_dict[part]

    def __contains__(self, key: str) -> bool:
        return self.contains(key)

    def __str__(self) -> str:
        return str(self._store)

class _VolatileStorage(_BaseStorage):
    """Storage that is not saved across restarts"""

    def __init__(self) -> None:
        if _VolatileStorage._store is not None:
            raise error.SingletonInstantiation

        _VolatileStorage._store = self._store = {}

class _PersistentStorage(_BaseStorage):
    """Storage that is persistent across restarts"""

    def __init__(self) -> None:
        if _PersistentStorage._store is not None:
            raise error.SingletonInstantiation

        _PersistentStorage._store = self._store = {}

    _store: dict[str, Any] = None

    def __setitem__(self, key: str, item: Any) -> None:
        if not isinstance(item, (str, int, list, dict)):
            raise TypeError(f"Tried to add item with type {type(item)} to PersistentStorage")

        return super().__setitem__(key, item)

    def _load_from_disk(self) -> None:
        if "storage_file" not in self:
            raise error.KeyNotFound()

        path = self["storage_file"]
        if not os.path.isfile(path):
            print("Storage file doesn't yet exist")
            return

        with open(path, "r", encoding="utf8") as f:
            self._store = json.load(f)

    def _save_to_disk(self) -> None:
        if "storage_file" not in self:
            raise error.KeyNotFound()

        path = self["storage_file"]
        if len(self._store) == 0 and os.path.isfile(path):
            print("Not overwriting existing storage file with empty storage")
            return

        with open(path, "w", encoding="utf8") as f:
            json.dump(self._store, f)

class _StorageView():
    """A read-only view on both the PersistentStorage and VolatileStorage"""

    def contains_item(self, key: str, item: Any) -> bool:
        """
        Checks whether a key within the storage contains an item
        If 'key' contains a '.', also checks if all sub-dicts exist
        """

        return PersistentStorage.contains_item(key, item) \
               or VolatileStorage.contains_item(key, item)

    def contains(self, key: str) -> bool:
        """
        Checks whether a key exists within the storage
        If 'key' contains a '.', also checks if all sub-dicts exist
        """

        return PersistentStorage.contains(key) \
               or VolatileStorage.contains(key)

    def __getitem__(self, key: str) -> Any:
        if key in PersistentStorage:
            return PersistentStorage[key]
        return VolatileStorage[key]

    def __contains__(self, key: str) -> bool:
        return self.contains(key)

VolatileStorage = _VolatileStorage()
PersistentStorage = _PersistentStorage()
StorageView = _StorageView()

# save persistent storage before program exits
# pylint: disable-next=protected-access
atexit.register(PersistentStorage._save_to_disk)
