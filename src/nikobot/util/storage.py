from __future__ import annotations

import atexit
import json
import os
from collections import defaultdict
from typing import Any

class _BaseStorage():
    _store: dict[str, Any] = None

    def exists(self, key: str) -> bool:
        """
        Checks whether a key exists within the storage
        If 'key' contains a '.', also checks if all sub-dicts exist
        """

        if not isinstance(key, str):
            raise TypeError()

        # allows checking multi-layer dicts with the following format:
        # util.PersistentStorage["some_module.some_subdict.another_subdict.key"]
        if "." in key:
            parts = key.split(".")
            curr_dict = self._store
            for c, part in enumerate(parts):
                if part not in curr_dict:
                    return False
                # if it isn't the last part
                if c < len(parts) - 1:
                    curr_dict = curr_dict[part]
                else:
                    return part in curr_dict
        else:
            return key in self._store

    def __getitem__(self, key: str) -> Any:
        if not isinstance(key, str):
            raise TypeError()

        # allows getting multi-layer dicts with the following format:
        # util.PersistentStorage["some_module.some_subdict.another_subdict.key"]
        if "." in key:
            parts = key.split(".")
            curr_dict = self._store
            for c, part in enumerate(parts):
                # if it isn't the last part
                if c < len(parts) - 1:
                    curr_dict = curr_dict[part]
                else:
                    return curr_dict[part]
        else:
            return self._store[key]

    def __setitem__(self, key: str, item: Any) -> None:
        if not isinstance(key, str):
            raise TypeError()

        # allows adding multi-layer dicts with the following format:
        # util.PersistentStorage["some_module.some_subdict.another_subdict.key"] = "value"
        # items can be accessed using:
        # util.PersistentStorage["some_module"]["some_subdict"]["another_subdict"]["key"]
        if "." in key:
            parts = key.split(".")
            curr_dict = self._store
            for c, part in enumerate(parts):
                # if it isn't the last part
                if c < len(parts) - 1:
                    # add a missing dictionary
                    if part not in curr_dict:
                        curr_dict[part] = {}
                    curr_dict = curr_dict[part]
                # add the actual value
                else:
                    curr_dict[part] = item
        else:
            self._store[key] = item

    def __contains__(self, key: str) -> bool:
        return key in self._store
    
    def __str__(self) -> str:
        return str(self._store)

class _VolatileStorage(_BaseStorage):
    """Storage that is not saved across restarts"""

    def __init__(self) -> None:
        if _VolatileStorage._store is not None:
            raise Exception("Can only be instantiated once")

        _VolatileStorage._store = self._store = defaultdict(dict)

class _PersistentStorage(_BaseStorage):
    """Storage that is persistent across restarts"""

    def __init__(self) -> None:
        if _PersistentStorage._store is not None:
            raise Exception("Can only be instantiated once")

        _PersistentStorage._store = self._store = defaultdict(dict)

    _store: dict[str, Any] = None

    def __setitem__(self, key: str, item: Any) -> None:
        if not isinstance(item, (str, int, list, dict)):
            raise TypeError(f"Tried to add item with type {type(item)} to PersistentStorage")

        return super().__setitem__(key, item)

    def _load_from_disk(self) -> None:
        if "storage_file" not in VolatileStorage:
            raise Exception()
        
        path = VolatileStorage["storage_file"]
        if not os.path.isfile(path):
            print("Storage file doesn't yet exist")
            return
        
        with open(path, "r") as f:
            self._store = json.load(f)

    def _save_to_disk(self) -> None:
        if "storage_file" not in VolatileStorage:
            raise Exception()
        
        path = VolatileStorage["storage_file"]
        if len(self._store) == 0 and os.path.isfile(path):
            print("Not overwriting existing storage file with empty storage")
            return
        
        with open(path, "w") as f:
            json.dump(self._store, f)

VolatileStorage = _VolatileStorage()
PersistentStorage = _PersistentStorage()

# save persistent storage before program exits
atexit.register(PersistentStorage._save_to_disk)
