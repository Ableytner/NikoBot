"""A module containing wrapping functions around requests which retries on rate-limit exceedings"""

import asyncio

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
    # also see https://developer.spotify.com/documentation/web-api/concepts/api-calls

    if await _has_json(res) and "error" in await res.json():
        error_json = await res.json()

        # authentication error
        if isinstance(error_json["error"], str):
            message = error_json["error"]
        # regular error
        else:
            message = error_json["error"]["message"]

        err = ApiResponseError(f"The API returned status code {res.status} and error: {message}")
        err.message = message
        err.status_code = res.status

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
        return False
