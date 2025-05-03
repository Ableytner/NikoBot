"""A module containing wrapping functions around requests which retires on rate-limit exceedings"""

import asyncio
from json import JSONDecodeError

import aiohttp
from abllib import log

from .error import ApiResponseError

logger = log.get_logger("spotify.req")

_session = None

async def get(url: str, headers: dict, params: dict | None = None, json: dict | None = None, **kwargs) \
             -> aiohttp.ClientResponse:
    """Send a get request asynchronously"""

    await _ensure_session()

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

async def post(url: str, headers: dict, params: dict | None = None, json: dict | None = None, **kwargs) \
              -> aiohttp.ClientResponse:
    """Send a post request asynchronously"""

    await _ensure_session()

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

async def delete(url: str, headers: dict, params: dict | None = None, json: dict | None = None, **kwargs) \
                -> aiohttp.ClientResponse:
    """Send a delete request asynchronously"""

    await _ensure_session()

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

async def _ensure_session() -> None:
    # pylint: disable-next=global-statement
    global _session
    if _session is None:
        _session = aiohttp.ClientSession()

async def _check_res(res: aiohttp.ClientResponse) -> None:
    if await _has_json(res) and "error" in await res.json():
        error_json = await res.json()

        err = ApiResponseError.with_values(error_json["error"]["message"])
        err.message = error_json["error"]["message"]
        err.status_code = error_json["error"]["status"]

        raise err

    if res.status not in [200, 201]:
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
        except JSONDecodeError:
            return False
