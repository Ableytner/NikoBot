from __future__ import annotations

import atexit
import json
from typing import Any

class _VolatileStorage():
    def __init__(self) -> None:
        if _VolatileStorage._store is not None:
            raise Exception("Can only be instantiated once")

        _VolatileStorage._store = {}

    _store: dict[str, Any] = None

    def __getitem__(self, key: str) -> Any:
        if not isinstance(key, str):
            print(key)
            raise TypeError()

        return self._store[key]

    def __setitem__(self, key: str, item: Any) -> None:
        if not isinstance(key, str):
            raise TypeError()

        self._store[key] = item

    def __contains__(self, key: str) -> bool:
        return key in self._store

class _PersistentStorage():
    def __init__(self) -> None:
        if _PersistentStorage._store is not None:
            raise Exception("Can only be instantiated once")

        _PersistentStorage._store = self._store = {}

    _store: dict[str, Any] = None

    def __getitem__(self, key: str) -> Any:
        if not isinstance(key, str):
            raise TypeError()

        return self._store[key]

    def __setitem__(self, key: str, item: Any) -> None:
        if not isinstance(key, str):
            raise TypeError()

        self._store[key] = item

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def _save_to_disk(self) -> None:
        pass

VolatileStorage = _VolatileStorage()
PersistentStorage = _PersistentStorage()

# save persistent storage before program exits
atexit.register(PersistentStorage._save_to_disk)
