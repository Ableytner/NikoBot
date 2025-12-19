"""Module containing functions for webscraping natomanga.com"""

from abllib import fs, VolatileStorage
from abllib.log import get_logger
import bs4 as bs

from . import flare_solverr
from .chapter import Chapter

logger = get_logger("mal")

BASE_URL = "https://natomanga.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"
}

def create_chapter(title: str, url: str) -> Chapter:
    """
    Create a new ``Chapter`` using the provided title and chapter url

    The chapter number is read from the url
    """

    if not isinstance(title, str):
        raise TypeError(f"Expected {str}, got {type(title)}")
    if not isinstance(url, str):
        raise TypeError(f"Expected {str}, got {type(url)}")

    number = float(url.rsplit("/", maxsplit=1)[1].split("-", maxsplit=1)[1].replace("-", "."))

    return Chapter(title, url, number)

def get_manga_url(titles: str | list[str]) -> str | None:
    """Return the url of the searched manga, or None if it isn't found"""

    if isinstance(titles, str):
        titles = [titles]

    seen_titles = []
    i = 0
    while i < len(titles):
        sanitized_title = _sanitize_title(titles[i])
        if sanitized_title not in seen_titles:
            seen_titles.append(sanitized_title)
            i += 1
        else:
            titles.pop(i)

    result_urls: list[str] = []
    for title in titles:
        url = f"{BASE_URL}/manga/{_sanitize_title(title)}"

        content = flare_solverr.get(url)

        if "cannot be found" in content: # not found
            continue

        result_urls.append(url)

    if len(result_urls) == 0:
        return None

    if len(result_urls) == 1:
        return result_urls[0]

    logger.debug(f"found multiple urls {result_urls} for manga {titles[0]}")

    max_chapters = -1
    max_url = ""
    for url in result_urls:
        chapters = get_chapters(url)
        if len(chapters) > max_chapters:
            max_chapters = len(chapters)
            max_url = url

    logger.debug(f"picked {max_url} with {max_chapters} chapters")

    return max_url

def get_chapters(url: str) -> list[Chapter]:
    """Get a list of ``Chapter``s from a given manganato url"""

    content = flare_solverr.get(url)

    soup = bs.BeautifulSoup(content, features="html.parser")
    chapter_class = soup.find("div", {"class": "chapter-list"})
    if chapter_class is None:
        logger.warning(f"No chapters found for manga {url}, saving response to 'cache/mal/natomanga.html'")
        with open(fs.absolute(VolatileStorage["cache_dir"], "mal", "natomanga.html"), "w") as f:
            f.write(content)
        return []
    chapter_objects = chapter_class.find_all("a", href=True)
    chapters = [create_chapter(item.contents[0], item["href"]) for item in chapter_objects]

    return chapters

def _sanitize_title(title: str) -> str:
    return title.replace(" ", "-") \
                .replace("(", "") \
                .replace(")", "") \
                .replace("'", "") \
                .replace(".", "") \
                .replace(":", "") \
                .replace("!", "") \
                .replace(",", "") \
                .lower()

def _setup():
    pass
