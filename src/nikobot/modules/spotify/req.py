"""A module containing wrapping functions around requests which retires on rate-limit exceedings"""

from typing import Any, NoReturn

import aiohttp
import requests
from abllib import log

from .error import ApiResponseError

logger = log.get_logger("Spotify.req")

_session = aiohttp.ClientSession()

async def get(url: str, headers: dict | None = None, params: dict | None = None, json: dict | None = None, **kwargs) -> aiohttp.ClientResponse:
    res = await _session.get(url, headers=headers, params=params, json=json, **kwargs)

    if await _has_json(res) and "error" in await res.json():
        _raise_error(await res.json())
    
    return res

async def post(url: str, headers: dict | None = None, params: dict | None = None, json: dict | None = None, **kwargs) -> aiohttp.ClientResponse:
    res = await _session.post(url, headers=headers, params=params, json=json, **kwargs)

    if await _has_json(res) and "error" in await res.json():
        _raise_error(await res.json())
    
    return res

async def delete(url: str, headers: dict | None = None, params: dict | None = None, json: dict | None = None, **kwargs) -> aiohttp.ClientResponse:
    res = await _session.delete(url, headers=headers, params=params, json=json, **kwargs)

    if await _has_json(res) and "error" in await res.json():
        _raise_error(await res.json())
    
    return res

def _raise_error(error_json: dict) -> NoReturn:
    err = ApiResponseError.with_values(error_json["error"]["message"])
    err.message = error_json["error"]["message"]
    err.status_code = error_json["error"]["status"]
    raise err

async def _has_json(res: aiohttp.ClientResponse) -> bool:
    try:
        await res.json()
        return True
    except aiohttp.ContentTypeError:
        return False
