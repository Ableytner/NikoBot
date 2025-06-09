"""Module containing classes for interfacing with the Spotify-related caches"""

from abllib import CacheStorage

from .dclasses import Track, Playlist

# TODO: save / load cache in PersistentStorage

class Cache():
    """Base class for all spotify caches"""

    user_id: int
    key: str

    @classmethod
    def get_instance(cls, user_id: int):
        """Return the Cache instance of the given user"""

        inst = cls()

        inst.user_id = user_id
        inst.key = f"spotify.{user_id}.cache"

        return inst

class PlaylistCache(Cache):
    """Class used for caching playlists"""

    def get(self, p_meta: Playlist) -> list[Track] | None:
        """Return the cached playlist, or None on missed or out-of-date cache"""

        if p_meta.id is None or p_meta.id == "":
            raise RuntimeError()

        key = f"{self.key}.{p_meta.id}"

        # cache miss
        if f"{key}" not in CacheStorage:
            return None

        # prefer snapshot_id
        if p_meta.snapshot_id is not None and f"{key}.snapshot_id" in CacheStorage:
            if CacheStorage[f"{key}.snapshot_id"] == p_meta.snapshot_id:
                # the playlist hasn't changed since
                return CacheStorage[f"{key}.tracks"]

            # out-of-date cache
            del CacheStorage[f"{key}"]
            return None

        # fall back to track count
        if len(CacheStorage[f"{key}.tracks"]) == p_meta.total_tracks:
            return CacheStorage[f"{key}.tracks"]

        # out-of-date cache
        del CacheStorage[f"{key}"]
        return None

    def set(self, p_meta: Playlist, tracks: list[Track]) -> None:
        """Add the given playlist to the cache"""

        key = f"{self.key}.{p_meta.id}"

        if p_meta.snapshot_id is not None:
            CacheStorage[f"{key}.snapshot_id"] = p_meta.snapshot_id

        # copy tracks to be sure
        CacheStorage[f"{key}.tracks"] = tracks.copy()
