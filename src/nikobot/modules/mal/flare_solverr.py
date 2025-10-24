from datetime import datetime, timedelta

import requests
from abllib import VolatileStorage, get_logger, NamedLock

logger = get_logger("FlareSolverr")

@NamedLock("FlareSolverr_solve")
def solve(key: str, url: str) -> tuple[dict[str, str], dict[str, str]]:
    """
    Try to obtain cloudflare cookies, which are returned.
    
    If cookies are already cached under the specified key, use them instead.
    """

    if f"flaresolverr.{key}" in VolatileStorage:
        cached = VolatileStorage[f"flaresolverr.{key}"]
        if datetime.fromtimestamp(cached["expires"]) > (datetime.now() + timedelta(minutes=1)):
            logger.debug("Using cached cf cookies")
            return (cached["jar"], cached["headers"])

        logger.debug("Removing cached cf cookies")
        del VolatileStorage[f"flaresolverr.{key}"]

    logger.info("Requesting new CloudFlare token from FlareSolverr")

    headers = {"Content-Type": "application/json"}
    data = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    }
    r = requests.post("http://192.168.0.145:9213/v1", headers=headers, json=data)

    if "status" in r.json() and r.json()["message"] == "Challenge not detected!":
        logger.debug("No cf challenge necessary")
        return ({}, {})

    if "solution" not in r.json() or r.json()["status"] != "ok":
        logger.warning(f"FlareSolverr returned invalid data: {r.json()}")
        raise Exception()

    solution = r.json()["solution"]

    jar = {}
    for cookie in solution["cookies"]:
        jar[cookie["name"]] = cookie["value"]

    headers = {
        "User-Agent": solution["userAgent"]
    }

    VolatileStorage[f"flaresolverr.{key}"] = {
        "expires": min((cookie["expiry"] for cookie in solution["cookies"])),
        "jar": jar,
        "headers": headers
    }

    return (jar, headers)
