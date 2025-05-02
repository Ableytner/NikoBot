"""Module which contains various dataclasses"""

from dataclasses import dataclass

from abllib import log
from abllib.error import WrongTypeError

logger = log.get_logger("Spotify.dclasses")

@dataclass
class Playlist:
    name: str
    id: str
    total_tracks: int

class TrackSet:
    """
    A custom set type which only stores each track id once.

    The oldest timestamp is also stored.
    """

    def __init__(self):
        self._tracks = {}

    def add(self, track_id: str, timestamp: int) -> None:
        """Add a new track id and timestamp to the set"""

        if not isinstance(track_id, str): raise WrongTypeError.with_values(track_id, str)
        if not isinstance(timestamp, int): raise WrongTypeError.with_values(timestamp, int)
        
        # TODO: remove
        if track_id == "5fbSIKNisMBlP1tXxjziJb":
            logger.info(timestamp)

        if track_id not in self._tracks:
            self._tracks[track_id] = timestamp
        elif timestamp < self._tracks[track_id]:
            self._tracks[track_id] = timestamp

    def ids(self) -> list[str]:
        """Return all track ids, sorted from oldest to newest"""

        items = list(self._tracks.items())
        items.sort(key=lambda x: x[1])
        return [item[0] for item in items]
