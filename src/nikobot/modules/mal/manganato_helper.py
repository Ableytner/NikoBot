"""Module containing functions for webscraping manganato.com"""

import bs4 as bs
import requests

from .chapter import Chapter
from ... import util

BASE_URL = "https://manganato.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"
}

def get_manga_url(titles: str | list[str]) -> str | None:
    """Return the url of the searched manga, or None if it isn't found"""

    if isinstance(titles, str):
        titles = [titles]

    results: dict[str, int] = {}
    for title in titles:
        name_sanitized = title.replace(" ", "_") \
                              .replace("(", "") \
                              .replace(")", "") \
                              .replace("'", "") \
                              .replace("-", "_") \
                              .replace(".", "") \
                              .replace(":", "") \
                              .replace("!", "") \
                              .lower()
        r = requests.get(f"{BASE_URL}/search/story/{name_sanitized}", timeout=30)

        soup = bs.BeautifulSoup(r.content, features="html.parser")
        search_results = soup.find("div", {"class": "panel-search-story"})
        if search_results is None:
            continue

        title_objects = search_results.find_all("a", {"class": "a-h text-nowrap item-title"}, href=True)

        found_titles = []
        for item in title_objects:
            # ignore empty manga such as https://chapmanganato.to/manga-zw1002905
            # this is too request-heavy
#            if len(get_chapters(item["href"])) == 0:
#                continue
            found_titles.append((util.general.levenshtein_distance(item.contents[0], title), item["href"]))

        found_titles.sort(key=lambda x: x[0])
        for c, item in enumerate(found_titles):
            if item[1] not in results:
                results[item[1]] = 0
            results[item[1]] += 5 - c
            if c >= 5:
                break

    results = [(score, url) for url, score in results.items()]
    closest_match = max(results, default=(None,None), key=lambda x: x[0])
    return closest_match[1]

def get_chapters(url: str) -> list[Chapter]:
    """Get a list of ``Chapter``s from a given manganato url"""

    r = requests.get(url, timeout=30)

    soup = bs.BeautifulSoup(r.content, features="html.parser")
    chapter_class = soup.find("ul", {"class": "row-content-chapter"})
    if chapter_class is None:
        return []
    chapter_objects = chapter_class.find_all("a", href=True)
    chapters = [Chapter(item.contents[0], item["href"]) for item in chapter_objects]

    return chapters

def _setup():
    pass
