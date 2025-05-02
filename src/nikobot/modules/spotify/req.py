"""A module containing wrapping functions around requests which retires on rate-limit exceedings"""

import asyncio
import json
from typing import Any, NoReturn

import aiohttp
from abllib import log

from .error import ApiResponseError

logger = log.get_logger("Spotify.req")

_session = aiohttp.ClientSession()

async def get(url: str, headers: dict | None = None, params: dict | None = None, json: dict | None = None, **kwargs) -> aiohttp.ClientResponse:
    code = 429
    while code == 429:
        res = await _session.get(url, headers=headers, params=params, json=json, **kwargs)
        code = res.status
        if code == 429:
            timeout = int(res.headers["Retry-After"])
            logger.warning(f"We are being rate-limited, sleeping for {timeout} seconds")
            await asyncio.sleep(timeout)

    await _check_res(res)
    
    return res

async def post(url: str, headers: dict | None = None, params: dict | None = None, json: dict | None = None, **kwargs) -> aiohttp.ClientResponse:
    code = 429
    while code == 429:
        res = await _session.post(url, headers=headers, params=params, json=json, **kwargs)
        code = res.status
        if code == 429:
            timeout = int(res.headers["Retry-After"])
            logger.warning(f"We are being rate-limited, sleeping for {timeout} seconds")
            await asyncio.sleep(timeout)

    await _check_res(res)
    
    return res

async def delete(url: str, headers: dict | None = None, params: dict | None = None, json: dict | None = None, **kwargs) -> aiohttp.ClientResponse:
    code = 429
    while code == 429:
        res = await _session.delete(url, headers=headers, params=params, json=json, **kwargs)
        code = res.status
        if code == 429:
            timeout = int(res.headers["Retry-After"])
            logger.warning(f"We are being rate-limited, sleeping for {timeout} seconds")
            await asyncio.sleep(timeout)

    await _check_res(res)
    
    return res

async def _check_res(res: aiohttp.ClientResponse) -> None:
    if await _has_json(res) and "error" in await res.json():
        error_json = await res.json()

        err = ApiResponseError.with_values(error_json["error"]["message"])
        err.message = error_json["error"]["message"]
        err.status_code = error_json["error"]["status"]

        raise err
    elif res.status != 200:
        err = ApiResponseError(f"Unexpected status code {res.status}")
        err.message = await res.text()
        err.status_code = res.status

        raise err

async def _has_json(res: aiohttp.ClientResponse) -> bool:
    try:
        await res.json()
        return True
    except aiohttp.ContentTypeError:
        try:
            await res.json(content_type=None)
            return True
        except json.JSONDecodeError:
            return False
