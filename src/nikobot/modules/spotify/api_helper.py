"""Contains helper functions for working with the Spotify Web API"""

from datetime import datetime
from typing import Generator, AsyncGenerator

from abllib import log, VolatileStorage, PersistentStorage

from . import auth_helper, req
from .dclasses import Playlist
from .error import ApiResponseError

logger = log.get_logger("Spotify.api_helper")

async def get_user_spotify_id(user_id: int) -> str:
    """Return the users' spotify id"""

    await auth_helper.ensure_token(user_id)

    url = f"https://api.spotify.com/v1/me"
    headers = auth_helper.get_auth_headers(user_id)

    res = await req.get(url, headers)
    json_res = await res.json()

    return json_res["id"]

async def create_playlist(user_id: int, playlist_name: str) -> Playlist:
    """Create a new playlist and return its sptify id"""

    await auth_helper.ensure_token(user_id)

    user_spotify_id = await get_user_spotify_id(user_id)

    url = f"https://api.spotify.com/v1/users/{user_spotify_id}/playlists"
    headers = auth_helper.get_auth_headers(user_id)
    body = {
        "name": playlist_name,
        "description": "Playlist with all songs from all your playlists, created by github.com/Ableytner/NikoBot",
        "public": False
    }

    res = await req.post(url, headers, json=body)
    json_res = await res.json()

    return Playlist(playlist_name, json_res["id"], 0)

async def get_playlist_ids(user_id: int) -> list[str]:
    """Return all playlist ids"""

    await auth_helper.ensure_token(user_id)

    user_spotify_id = await get_user_spotify_id(user_id)

    BASE_URL = "https://api.spotify.com/v1/me/playlists"

    headers = auth_helper.get_auth_headers(user_id)
    params = {
        "limit": 50
    }

    res = await req.get(BASE_URL, headers, params)
    json_res = await res.json()

    playlist_ids = set()
    total_playlists = json_res["total"]

    offset = 0
    while offset < total_playlists:
        params = {
            "offset": offset,
            "limit": 50
        }

        res = await req.get(BASE_URL, headers, params)
        json_res = await res.json()

        for playlist_json in json_res["items"]:
            if playlist_json["owner"]["id"] == user_spotify_id:
                playlist_ids.add(playlist_json["id"])
            offset += 1

    logger.info(f"Retrieved {len(playlist_ids)} user-owned playlists")

    return list(playlist_ids)

async def get_playlist_meta(user_id: int, playlist_id: str) -> Playlist:
    """Return the metadata of a playlist"""

    await auth_helper.ensure_token(user_id)

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = auth_helper.get_auth_headers(user_id)
    params = {
        "fields": "name,tracks.total,snapshot_id"
    }

    res = await req.get(url, headers, params)
    json_res = await res.json()

    return Playlist(json_res["name"], playlist_id, json_res["tracks"]["total"], json_res["snapshot_id"])

async def delete_playlist(user_id: int, playlist_id: str) -> Playlist:
    """Delete a given playlist"""

    await auth_helper.ensure_token(user_id)

    # unfollowing a playlist deletes it
    # https://stackoverflow.com/a/78710008/15436169
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/followers"
    headers = auth_helper.get_auth_headers(user_id)

    await req.delete(url, headers)

async def get_tracks(user_id: int, playlist_id: str) -> AsyncGenerator[tuple[str, int], None]:
    """Return a generator over all track ids and date_added of a playlist"""

    await auth_helper.ensure_token(user_id)

    BASE_URL = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    params = {
        "fields": "name,tracks.total"
    }
    headers = auth_helper.get_auth_headers(user_id)

    res = await req.get(BASE_URL, headers, params)
    json_res = await res.json()

    playlist_name = json_res["name"]
    total_tracks = json_res["tracks"]["total"]
    logger.info(f"Requesting {total_tracks} tracks from playlist {playlist_name}")

    offset = 0
    while offset < total_tracks:
        params = {
            "fields": "items(added_at,track.id)",
            "offset": offset,
            "limit": 50
        }

        res = await req.get(BASE_URL + "/tracks", headers, params)
        json_res = await res.json()

        for track_json in json_res["items"]:
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

async def get_saved_tracks(user_id: int) -> AsyncGenerator[tuple[str, int], None]:
    """Return a generator over all saved track ids of the liked songs"""

    await auth_helper.ensure_token(user_id)

    BASE_URL = f"https://api.spotify.com/v1/me/tracks"

    headers = auth_helper.get_auth_headers(user_id)

    res = await req.get(BASE_URL, headers)
    json_res = await res.json()

    total_tracks = json_res["total"]
    logger.info(f"Requesting {total_tracks} tracks from liked songs")

    offset = 0
    while offset < total_tracks:
        params = {
            "offset": offset,
            "limit": 50
        }

        res = await req.get(BASE_URL, headers, params)
        json_res = await res.json()

        for track_json in json_res["items"]:
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

async def add_tracks(user_id: int, playlist_id: str, track_ids: list[str]) -> None:
    """Add all given track ids to a playlist"""

    await auth_helper.ensure_token(user_id)

    BASE_URL = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = auth_helper.get_auth_headers(user_id)

    total_tracks = len(track_ids)
    logger.info(f"Adding {total_tracks} tracks to playlist")

    offset = 0
    while offset < total_tracks:
        body = {
            "uris": [f"spotify:track:{item}" for item in track_ids[-50:]],
            "position": 0
        }

        try:
            await req.post(BASE_URL, headers, json=body)
        except ApiResponseError:
            logger.info(body)

        track_ids = track_ids[:-50]
        offset += len(body["uris"])

async def remove_tracks(user_id: int, playlist_id: str, track_ids: list[str]) -> None:
    """Remove all given track ids from a playlist"""

    await auth_helper.ensure_token(user_id)

    BASE_URL = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = auth_helper.get_auth_headers(user_id)

    total_tracks = len(track_ids)

    offset = 0
    while offset < total_tracks:
        body = {
            "tracks": [{"uri": f"spotify:track:{item}"} for item in track_ids[0:100:]]
        }

        try:
            await req.delete(BASE_URL, headers, json=body)
        except ApiResponseError as ex:
            logger.info(body)
            logger.exception(ex)
            return

        track_ids = track_ids[100:]
        offset += len(body["tracks"])
