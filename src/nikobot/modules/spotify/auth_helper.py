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
from .error import UserNotRegisteredError, UserRegistrationExpired

logger = log.get_logger("spotify.auth_helper")

REDIRECT_URL = "https://nikobot.ableytner.at/spotify_auth"

def is_authed(user_id: int) -> bool:
    """Return whether the given user is already authenticated"""

    return f"spotify.{user_id}" in PersistentStorage

def is_auth_expired(user_id: int) -> bool:
    """Return whether the given users' authentication is expired"""

    refresh_token_expiry_str = PersistentStorage[f"spotify.{user_id}.refresh_token_expiration_date"]
    refresh_token_expiration = datetime.fromtimestamp(refresh_token_expiry_str)
    refresh_token_expiration -= timedelta(days=1) # make the expiration date a bit sooner

    return refresh_token_expiration < datetime.now()

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
                 " playlist-modify-public playlist-modify-private",
        "state": state,
        "redirect_uri": REDIRECT_URL
    }
    url_with_params = BASE_URL + urllib.parse.urlencode(params)

    return url_with_params

async def complete_auth(user_id: int, auth_code: str):
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

    res = await req.post(BASE_URL, headers, params)
    json_res = await res.json()

    PersistentStorage[f"spotify.{user_id}.access_token"] = json_res["access_token"]
    expires_at = datetime.now() + timedelta(seconds=json_res["expires_in"])
    PersistentStorage[f"spotify.{user_id}.access_token_expiration_date"] = expires_at.timestamp()
    PersistentStorage[f"spotify.{user_id}.refresh_token"] = json_res["refresh_token"]
    expires_at = datetime.now() + timedelta(weeks=24) # 6 months
    PersistentStorage[f"spotify.{user_id}.refresh_token_expiration_date"] = expires_at.timestamp()
    PersistentStorage.save_to_disk()

    del VolatileStorage[f"spotify.auth.{user_id}"]

    logger.info(f"Successfully linked Spotify account of user {user_id}")

def cancel_auth(user_id: int) -> None:
    """Cancel the given users' ongoing authentication"""

    if f"spotify.auth.{user_id}" in VolatileStorage:
        del VolatileStorage[f"spotify.auth.{user_id}"]

async def ensure_token(user_id: int) -> None:
    """
    Ensure that the given user has a valid Spotify token
    
    If the user is not yet registered, raise an UserNotRegisteredError
    """

    if f"spotify.{user_id}" not in PersistentStorage:
        raise UserNotRegisteredError()

    access_token_expiry_str = PersistentStorage[f"spotify.{user_id}.access_token_expiration_date"]
    access_token_expiration = datetime.fromtimestamp(access_token_expiry_str)
    access_token_expiration -= timedelta(minutes=5) # make the expiration date a bit sooner

    refresh_token_expiry_str = PersistentStorage[f"spotify.{user_id}.refresh_token_expiration_date"]
    refresh_token_expiration = datetime.fromtimestamp(refresh_token_expiry_str)
    refresh_token_expiration -= timedelta(days=1) # make the expiration date a bit sooner

    if refresh_token_expiration < datetime.now():
        # the refresh token has expired
        raise UserRegistrationExpired.with_values(user_id)

    if access_token_expiration < datetime.now():
        # the access token has expired
        await refresh_token(user_id)

async def refresh_token(user_id: int) -> None:
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

    res = await req.post(BASE_URL, headers, params)
    json_res = await res.json()

    PersistentStorage[f"spotify.{user_id}.access_token"] = json_res["access_token"]
    if "refresh_token" in json_res:
        PersistentStorage[f"spotify.{user_id}.refresh_token"] = json_res["refresh_token"]
    expires_at = datetime.now() + timedelta(seconds=json_res["expires_in"])
    PersistentStorage[f"spotify.{user_id}.access_token_expiration_date"] = expires_at.timestamp()

def _hash_user_id(user_id: int) -> str:
    user_id = str(user_id).encode("utf8")
    sha = hashlib.sha256()
    sha.update(user_id)
    return sha.hexdigest()

def get_auth_string() -> str:
    """Get the base64-encoded client_id/client_secret"""

    authorization = f"{VolatileStorage['spotify.client_id']}:{VolatileStorage['spotify.client_secret']}"
    authorization_encoded = base64.b64encode(authorization.encode("ascii")).decode("ascii")
    return authorization_encoded

def get_auth_headers(user_id: int) -> dict[str, str]:
    """Get the Oauth header containing the access token"""

    return {
        "Authorization": f"Bearer {PersistentStorage[f'spotify.{user_id}.access_token']}"
    }
