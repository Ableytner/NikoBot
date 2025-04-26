"""Module which contains various dataclasses"""

from dataclasses import dataclass

from abllib.error import WrongTypeError

@dataclass
class Playlist:
    name: str
    id: str
    total_tracks: int

class TrackSet:
    def __init__(self):
        self._tracks = {}

    def add(self, track_id: str, timestamp: int) -> None:
        if not isinstance(track_id, str): raise WrongTypeError.with_values(track_id, str)
        if not isinstance(timestamp, int): raise WrongTypeError.with_values(timestamp, int)
        
        if track_id not in self._tracks:
            self._tracks[track_id] = timestamp
        elif timestamp < self._tracks[track_id]:
            self._tracks[track_id] = timestamp

    def ids(self) -> list[str]:
        items = list(self._tracks.items())
        items.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in items]
