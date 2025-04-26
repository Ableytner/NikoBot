"""
Module which contains helper functions for spotify OAuth

See https://developer.spotify.com/documentation/web-api/tutorials/code-flow for more details
"""

import base64
import hashlib
import urllib.parse
from datetime import datetime, timedelta

from abllib import log, VolatileStorage, PersistentStorage

from . import req
from .error import ApiResponseError, UserNotRegisteredError

logger = log.get_logger("Spotify.auth_helper")

REDIRECT_URL = "https://nikobot.ableytner.duckdns.org/spotify_auth"

def is_authed(user_id: int) -> bool:
    """Return whether the given user is already authenticated"""

    return f"spotify.{user_id}" in PersistentStorage

def auth(user_id: int) -> str:
    """
    Authorize the given user with spotify.
    
    Return the URL the user has to open.
    """

    BASE_URL = "https://accounts.spotify.com/authorize?"

    state = _hash_user_id(user_id)
    VolatileStorage[f"spotify.auth.{user_id}"] = state

    params = {
        "response_type": "code",
        "client_id": VolatileStorage["spotify.client_id"],
        "scope": "playlist-read-private playlist-read-collaborative user-library-read" \
                 + " playlist-modify-public playlist-modify-private",
        "state": state,
        "redirect_uri": REDIRECT_URL
    }
    url_with_params = BASE_URL + urllib.parse.urlencode(params)

    return url_with_params

def complete_auth(user_id: int, auth_code: str):
    """Complete the user authorization"""

    BASE_URL = "https://accounts.spotify.com/api/token"

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {get_auth_string()}"
    }
    params = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URL
    }

    res = req.post(BASE_URL, headers=headers, params=params, timeout=10)

    PersistentStorage[f"spotify.{user_id}.access_token"] = res.json()["access_token"]
    PersistentStorage[f"spotify.{user_id}.refresh_token"] = res.json()["refresh_token"]
    expires_at = datetime.now() + timedelta(seconds=res.json()["expires_in"])
    PersistentStorage[f"spotify.{user_id}.token_expiration_date"] = expires_at.timestamp()
    PersistentStorage.save_to_disk()

    del VolatileStorage[f"spotify.auth.{user_id}"]

    logger.info(f"Successfully linked Spotify account of user {user_id}")

def cancel_auth(user_id: int) -> None:
    """Cancel the given users' ongoing authentication"""

    if f"spotify.auth.{user_id}" in VolatileStorage:
        del VolatileStorage[f"spotify.auth.{user_id}"]

def ensure_token(user_id: int) -> None:
    """
    Ensure that the given user has a valid Spotify token
    
    If the user is not yet registered, raise an UserNotRegisteredError
    """

    if f"spotify.{user_id}" not in PersistentStorage:
        raise UserNotRegisteredError()

    expiration_time = datetime.fromtimestamp(PersistentStorage[f"spotify.{user_id}.token_expiration_date"])
    expiration_time -= timedelta(minutes=5) # make the expiration date a bit sooner

    if expiration_time > datetime.now():
        # the token has not yet expired
        return

    # the token has already expired
    refresh_token(user_id)

def refresh_token(user_id: int) -> None:
    """Refresh the given users Spotify token"""

    BASE_URL = "https://accounts.spotify.com/api/token"

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {get_auth_string()}"
    }
    params = {
        "grant_type": "refresh_token",
        "refresh_token": PersistentStorage[f"spotify.{user_id}.refresh_token"]
    }

    res = req.post(BASE_URL, headers=headers, params=params, timeout=10)

    PersistentStorage[f"spotify.{user_id}.access_token"] = res.json()["access_token"]
    if "refresh_token" in res.json():
        PersistentStorage[f"spotify.{user_id}.refresh_token"] = res.json()["refresh_token"]
    expires_at = datetime.now() + timedelta(seconds=res.json()["expires_in"])
    PersistentStorage[f"spotify.{user_id}.token_expiration_date"] = expires_at.timestamp()

def _hash_user_id(user_id: int) -> str:
    user_id = str(user_id).encode("utf8")
    sha = hashlib.sha256()
    sha.update(user_id)
    return sha.hexdigest()

def get_auth_string() -> str:
    """Get the base64-encoded client_id/client_secret"""

    authorization = f"{VolatileStorage["spotify.client_id"]}:{VolatileStorage["spotify.client_secret"]}"
    authorization_encoded = base64.b64encode(authorization.encode("ascii")).decode("ascii")
    return authorization_encoded

def get_auth_headers(user_id: int) -> str:
    return {
        "Authorization": f"Bearer {PersistentStorage[f"spotify.{user_id}.access_token"]}"
    }
