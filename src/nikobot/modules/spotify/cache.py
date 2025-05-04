"""Module containing classes for interfacing with the Spotify-related cache"""

from typing import Any

from abllib import PersistentStorage

from .dclasses import Playlist

class Cache():
    """Base class for all spotify caches"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.key = f"spotify.{user_id}.cache"

class PlaylistCache(Cache):
    """Class used for caching playlists"""

    def get(self, p_meta: Playlist) -> list[Any] | None:
        """Return the cached playlist, or None on missed or out-of-date cache"""

        key = f"{self.key}.{p_meta.id}"

        # cache miss
        if f"{key}" not in PersistentStorage:
            return None

        # prefer snapshot_id
        if p_meta.snapshot_id is not None and f"{key}.snapshot_id" in PersistentStorage:
            if PersistentStorage[f"{key}.snapshot_id"] == p_meta.snapshot_id:
                # the playlist hasn't changed since
                return PersistentStorage[f"{key}.tracks"]

            # out-of-date cache
            del PersistentStorage[f"{key}"]
            return None

        # fall back to track count
        if len(PersistentStorage[f"{key}.tracks"]) == p_meta.total_tracks:
            return PersistentStorage[f"{key}.tracks"]

        # out-of-date cache
        del PersistentStorage[f"{key}"]
        return None

    def set(self, p_meta: Playlist, tracks: list[Any]) -> None:
        """Add the given playlist to the cache"""

        key = f"{self.key}.{p_meta.id}"

        if p_meta.snapshot_id is not None:
            PersistentStorage[f"{key}.snapshot_id"] = p_meta.snapshot_id

        PersistentStorage[f"{key}.tracks"] = tracks.copy()
