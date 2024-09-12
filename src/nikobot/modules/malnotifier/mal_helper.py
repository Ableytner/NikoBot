import requests
from typing import Any

from . import exec
from ... import util

BASE_URL = "https://api.myanimelist.net/v2"
HEADERS = {
    "X-MAL-CLIENT-ID": ""
}

def get_manga_from_id(mal_id: int) -> dict[str, Any]:
    r = requests.get(f"{BASE_URL}/manga/{mal_id}?fields=id,title,alternative_titles,main_picture,mean,media_type,status,genres,my_list_status,authors{{first_name,last_name}}", headers=HEADERS)

    if "error" in r.json():
        if r.json()["error"] == "not_found":
            raise exec.MangaNotFound()
        else:
            raise exec.CustomException(r.json()["error"])

    if r.json()["media_type"] != "manga" and r.json()["media_type"] != "mahnwa":
        raise exec.MediaTypeError("Currently only supports manga/mahnwa and not light novel/novel")

    to_return = {
        "id": r.json()["id"],
        "title": r.json()["title"],
        "title_en": r.json()["alternative_titles"]["en"],
        "synonyms": r.json()["alternative_titles"]["synonyms"]
    }

    if r.json()["status"] == "currently_publishing":
        to_return["status"] = "currently publishing"
    else:
        to_return["status"] = r.json()["status"]

    if "picture" in r.json():
        to_return["picture"] = r.json()["picture"]
    elif "main_picture" in r.json():
        to_return["picture"] = r.json()["main_picture"]["large"]
    
    if "mean" in r.json():
        to_return["score"] = r.json()["mean"]
    else:
        to_return["score"] = float("nan")

    return to_return

def get_manga_list_from_username(mal_username: str) -> list[dict[str, str | int]]:
    r = requests.get(f"{BASE_URL}/users/{mal_username}/mangalist?fields=list_status&status=reading&limit=1000", headers=HEADERS)

    if "error" in r.json():
        if r.json()["error"] == "not_found":
            raise exec.UserNotFound()
        else:
            raise exec.CustomException(r.json()["error"])

    return_data = []
    for manga_json in r.json()["data"]:
        return_data.append({
            "mal_id": manga_json["node"]["id"],
            "read_chapters": manga_json["list_status"]["num_chapters_read"]
        })
    return return_data

def _setup():
    HEADERS["X-MAL-CLIENT-ID"] = util.VolatileStorage["mal"]["CLIENT-ID"]
