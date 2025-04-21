"""Contains helper functions for working with the Spotify Web API"""

import requests

from abllib import log, VolatileStorage, PersistentStorage

from . import auth_helper
from .error import ApiResponseError

logger = log.get_logger("SpotifyApiHelper")

def get_playlist_ids(user_id: int) -> list[int]:
    """Return all playlist ids for the given user"""

    auth_helper.ensure_token(user_id)

    BASE_URL = "https://api.spotify.com/v1/me/playlists"

    headers = {
        "Authorization": f"Bearer {PersistentStorage[f"spotify.{user_id}.access_token"]}"
    }
    params = {
        "limit": 50
    }

    res = requests.get(BASE_URL, headers=headers, params=params)

    if "error" in res.json():
        raise ApiResponseError.with_values(res.json())

    playlist_ids = set()
    total_playlists = res.json()["total"]

    logger.info(f"Requesting {total_playlists} playlists in total")

    offset = 0
    while offset < total_playlists:
        params = {
            "offset": offset,
            "limit": 50
        }

        res = requests.get(BASE_URL, headers=headers, params=params)

        if "error" in res.json():
            raise ApiResponseError.with_values(res.json())

        for playlist_json in res.json()["items"]:
            playlist_ids.add(playlist_json["id"])
            offset += 1

    logger.info(f"Retrieved {len(playlist_ids)} playlists")

    return list(playlist_ids)

# TODO: rework method
def get_playlist(user_id: int, playlist_id: str) -> tuple[str, list]:
    """Return a certain playlist of a given user"""

    auth_helper.ensure_token(user_id)

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {
        "Authorization": f"Bearer {PersistentStorage[f"spotify.{user_id}.access_token"]}"
    }
    params = {
        "fields": "name,tracks.total"
    }

    res = requests.get(url, headers=headers, params=params)

    if "error" in res.json():
        raise ApiResponseError.with_values(res.json())

    playlist_name = res.json()["name"]
    total_tracks = res.json()["tracks"]["total"]
    print(f"Requesting {total_tracks} tracks from playlist {playlist_name}")

    tracks = []
    offset = 0
    while offset < total_tracks:
        tracks += _get_tracks_from_playlist(playlist_id, offset, 100)
        offset += 100
        print(f"Retrieved {len(tracks)} tracks", end="\r")

    print(f"Retrieved {len(tracks)} tracks")

    return (playlist_name, tracks)

def _get_tracks_from_playlist(user_id: int, playlist_id: str, offset: int, limit: int) -> list:
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": f"Bearer {PersistentStorage[f"spotify.{user_id}.access_token"]}"
    }
    params = {
        "offset": offset,
        "limit": limit,
        "fields": "items(track(name,album,artists))"
    }

    res = requests.get(url, headers=headers, params=params)

    if "error" in res.json():
        raise ApiResponseError.with_values(res.json())

    tracks = []
    for track in [item["track"] for item in res.json()["items"]]:
        try:
            # tracks.append(SpotifyTrack.from_response(track))
            pass
        except ValueError:
            pass

    return tracks
