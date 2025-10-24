from datetime import datetime, timedelta

import requests
from abllib import VolatileStorage, get_logger

logger = get_logger("FlareSolverr")

def solve(key: str, url: str) -> dict[str, str]:
    """
    Try to obtain cloudflare cookies, which are returned.
    
    If cookies are already cached under the specified key, use them instead.
    """

    if f"flaresolverr.{key}" in VolatileStorage:
        cached = VolatileStorage[f"flaresolverr.{key}"]
        if datetime.fromtimestamp(cached["expires"]) < (datetime.now() - timedelta(minutes=1)):
            logger.debug("Using cached cf cookies")
            return cached["jar"]

        logger.debug("Removing cached cf cookies")
        del VolatileStorage[f"flaresolverr.{key}"]

    headers = {"Content-Type": "application/json"}
    data = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    }

    r = requests.post("http://192.168.0.145:9213/v1", headers=headers, json=data)

    if "cookies" not in r.json():
        logger.warning(f"FlareSolverr didn't return any cookies, return data: {r.json()}")
        raise Exception()

    jar = {}
    for cookie in r.json()["cookies"]:
        jar[cookie["name"]] = cookie["value"]

    VolatileStorage[f"flaresolverr.{key}"] = {
        "expires": min((cookie["expires"] for cookie in r.json()["cookies"])),
        "jar": jar
    }

    return jar
