"""Contains helper functions for working with the Spotify Web API"""

from datetime import datetime
from typing import Generator

from abllib import log, VolatileStorage, PersistentStorage

from . import auth_helper, req
from .dclasses import Playlist
from .error import ApiResponseError

logger = log.get_logger("Spotify.api_helper")

def get_user_spotify_id(user_id: int) -> str:
    """Return the users' spotify id"""

    auth_helper.ensure_token(user_id)

    url = f"https://api.spotify.com/v1/me"
    headers = auth_helper.get_auth_headers(user_id)

    res = req.get(url, headers=headers, timeout=10)

    return res.json()["id"]

def create_playlist(user_id: int, playlist_name: str) -> Playlist:
    """Create a new playlist and return its sptify id"""

    auth_helper.ensure_token(user_id)

    user_spotify_id = get_user_spotify_id(user_id)

    url = f"https://api.spotify.com/v1/users/{user_spotify_id}/playlists"
    headers = auth_helper.get_auth_headers(user_id)
    body = {
        "name": playlist_name,
        "description": "Playlist with all songs from all your playlists, created by github.com/Ableytner/NikoBot",
        "public": False
    }

    res = req.post(url, headers=headers, json=body, timeout=10)

    return Playlist(playlist_name, res.json()["id"], 0)

def get_playlist_ids(user_id: int) -> list[str]:
    """Return all playlist ids"""

    auth_helper.ensure_token(user_id)

    user_spotify_id = get_user_spotify_id(user_id)

    BASE_URL = "https://api.spotify.com/v1/me/playlists"

    headers = {
        "Authorization": f"Bearer {PersistentStorage[f"spotify.{user_id}.access_token"]}"
    }
    params = {
        "limit": 50
    }

    res = req.get(BASE_URL, headers=headers, params=params, timeout=10)

    playlist_ids = set()
    total_playlists = res.json()["total"]

    offset = 0
    while offset < total_playlists:
        params = {
            "offset": offset,
            "limit": 50
        }

        res = req.get(BASE_URL, headers=headers, params=params, timeout=10)

        for playlist_json in res.json()["items"]:
            if playlist_json["owner"]["id"] == user_spotify_id:
                playlist_ids.add(playlist_json["id"])
            offset += 1

    logger.info(f"Retrieved {len(playlist_ids)} user-owned playlists")

    return list(playlist_ids)

def get_playlist_meta(user_id: int, playlist_id: str) -> Playlist:
    """Return the metadata of a playlist"""

    auth_helper.ensure_token(user_id)

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = auth_helper.get_auth_headers(user_id)
    params = {
        "fields": "name,tracks.total"
    }

    res = req.get(url, headers=headers, params=params, timeout=10)

    return Playlist(res.json()["name"], playlist_id, res.json()["tracks"]["total"])

def get_tracks(user_id: int, playlist_id: str) -> Generator[tuple[str, int], None, None]:
    """Return a generator over all track ids and date_added of a playlist"""

    auth_helper.ensure_token(user_id)

    BASE_URL = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = auth_helper.get_auth_headers(user_id)
    params = {
        "fields": "name,tracks.total"
    }

    res = req.get(BASE_URL, headers=headers, params=params, timeout=10)

    playlist_name = res.json()["name"]
    total_tracks = res.json()["tracks"]["total"]
    logger.info(f"Requesting {total_tracks} tracks from playlist {playlist_name}")

    offset = 0
    while offset < total_tracks:
        params = {
            "fields": "items(added_at,track.id)",
            "offset": offset,
            "limit": 50
        }

        res = req.get(BASE_URL + "/tracks", headers=headers, params=params, timeout=10)

        for track_json in res.json()["items"]:
            if track_json["track"]["id"] is not None:
                yield (
                    track_json["track"]["id"],
                    int(datetime.strptime(track_json["added_at"], r"%Y-%m-%dT%H:%M:%SZ").timestamp())
                )
            else:
                # local files can't currently be added to playlists using the web api
                # https://developer.spotify.com/documentation/web-api/concepts/playlists under #Limitations
                pass
            offset += 1

def add_tracks(user_id: int, playlist_id: str, track_ids: list[str]) -> None:
    """Add all given track ids to a playlist"""

    auth_helper.ensure_token(user_id)

    BASE_URL = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = auth_helper.get_auth_headers(user_id)

    total_tracks = len(track_ids)
    logger.info(f"Adding {len(track_ids)} tracks to playlist")

    offset = 0
    while offset < total_tracks:
        body = {
            "uris": [f"spotify:track:{item}" for item in track_ids[0:50:]]
        }

        try:
            res = req.post(BASE_URL, headers=headers, json=body, timeout=10)
        except ApiResponseError:
            logger.info(body)

        track_ids = track_ids[50:]
        offset += len(body["uris"])
