"""A module containing wrapping functions around requests which retires on rate-limit exceedings"""

from typing import Any

import requests
from abllib import log

from .error import ApiResponseError

logger = log.get_logger("Spotify.req")

def get(*args, **kwargs) -> Any:
    res = requests.get(*args, **kwargs)

    if res.status_code not in [200, 201]:
        logger.info(res.json())

    if "error" in res.json():
        raise ApiResponseError.with_values(res.json())
    
    return res

def post(*args, **kwargs) -> Any:
    res = requests.post(*args, **kwargs)

    if res.status_code not in [200, 201]:
        logger.info(res.json())

    if "error" in res.json():
        raise ApiResponseError.with_values(res.json())
    
    return res
