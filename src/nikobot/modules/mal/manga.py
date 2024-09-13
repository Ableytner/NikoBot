"""Module containing the ``Manga`` class"""

from __future__ import annotations

import os
from datetime import datetime
from enum import Enum

import requests
from PIL import Image
from discord import Embed, File, Color

from . import error, mal_helper, manganato_helper
from .chapter import Chapter
from ... import util

class MangaProvider(Enum):
    """
    An Enum replesenting Manga providers
    
    These are websites which provide manga chapters
    """

    MANGANATO = "manganato"

class Manga():
    """
    A class representing a specific Manga belonging to an user
    
    Manga are comics or graphic novels originating from Japan 
    """

    def __init__(self, mal_id: int, title: str, title_translated: str | None, synonyms: list[str],
                 status: str, picture_url: str, score: float) -> None:
        if not isinstance(mal_id, int):
            raise TypeError()
        if not isinstance(title, str):
            raise TypeError()
        if not isinstance(title_translated, (str, None)):
            raise TypeError()
        if not isinstance(synonyms, list):
            raise TypeError()
        if not isinstance(status, str):
            raise TypeError()
        if not isinstance(picture_url, str):
            raise TypeError()
        if not isinstance(score, float):
            raise TypeError()

        self.mal_id = mal_id
        self.title = title
        self.title_translated = title_translated or title # fall back to title if translated title is empty
        self.synonyms = synonyms # can also be empty
        self.status = status
        self.picture_url = picture_url
        self.score = score
        self._manga_provider: MangaProvider | None = None
        self._manga_provider_url: str | None = None
        self._chapters_read: int | None = None
        self._chapters_total: int | None = None
        self._chapters_last_notified: int | None = None
        self._time_next_notify: datetime = datetime.now()

    # pylint: disable=protected-access
    @staticmethod
    def from_export(export: dict[str, str]) -> Manga:
        """Factory method creating a new Manga object using the export data created by my_manga.export()"""

        if not isinstance(export["mal_id"], int):
            raise TypeError()
        if not isinstance(export["time_next_notify"], float):
            raise TypeError()
        if "provider" in export and not isinstance(export["provider"], str):
            raise TypeError()
        if "provider_url" in export and not isinstance(export["provider_url"], str):
            raise TypeError()
        if "chapters_last_notified" in export and not isinstance(export["chapters_last_notified"], int):
            raise TypeError()

        manga = Manga.from_mal_id(export["mal_id"])
        manga._time_next_notify = datetime.fromtimestamp(export["time_next_notify"])
        if "provider" in export \
           and "provider_url" in export:
            manga.set_manga_provider(MangaProvider[export["provider"]], export["provider_url"])
        if "chapters_last_notified" in export:
            manga._chapters_last_notified = export["chapters_last_notified"]

        return manga
    # pylint: enable=protected-access

    @staticmethod
    def from_mal_id(mal_id: int) -> Manga:
        """Factory method creating a new Manga object using the MyAnimeList id"""

        data = mal_helper.get_manga_from_id(mal_id)
        manga = Manga(mal_id,
                      data["title"],
                      data["title_en"],
                      data["synonyms"],
                      data["status"],
                      data["picture"],
                      data["score"])
        return manga

    def export(self) -> dict[str, str]:
        """Create a dictionary which is JSON-compliant and can be used to recreate this exact Manga"""

        export_data = {
            "mal_id": self.mal_id,
            "time_next_notify": self._time_next_notify.timestamp()
        }
        if self._manga_provider is not None \
           and self._manga_provider_url is not None:
            export_data["provider"] = self._manga_provider.name
            export_data["provider_url"] = self._manga_provider_url
        if self._chapters_last_notified is not None:
            export_data["chapters_last_notified"] = self._chapters_last_notified
        return export_data

    def fetch_chapters(self) -> None:
        """Fetch the newest released chapter from the set provider, using manganato as the default"""

        if self._manga_provider is not None:
            self._fetch_chapters()
        else:
            manga_url = manganato_helper.get_manga_url([self.title, self.title_translated] + self.synonyms)
            if manga_url is None:
                raise error.MangaNotFound("Manga could not be found automatically")
            self.set_manga_provider(MangaProvider.MANGANATO, manga_url)

            try:
                self._fetch_chapters()
            except error.CustomException as e:
                # reset manga_provider if fetching didn't work
                self.set_manga_provider(None, None)
                raise e

    def _fetch_chapters(self) -> None:
        chapters: list[Chapter] = None
        if self._manga_provider == MangaProvider.MANGANATO:
            chapters = manganato_helper.get_chapters(self._manga_provider_url)

        if chapters is None:
            raise error.UnknownProvider()

        latest_chapter = max(chapters, key=lambda x: x.number)
        self._chapters_total = int(latest_chapter.number)

    def picture_file(self) -> str:
        """
        Download the preview picture, returning the picture file path

        Returns a cached picture if available
        """

        path = os.path.join(util.VolatileStorage["cache_dir"], "mal")
        os.makedirs(path, exist_ok=True)
        path = os.path.join(path, f"preview_{self.mal_id}.{self.picture_url.rsplit(".", maxsplit=1)[1]}")

        if os.path.isfile(path):
            return path

        r = requests.get(self.picture_url, timeout=30)
        with open(path, "wb") as f:
            f.write(r.content)
        return path

    def set_chapters_read(self, chapters_read: int) -> None:
        """
        Set the number of chapters that the user already read
        
        Also initializes ``self._chapters_last_notified`` if not yet set
        """

        if not isinstance(chapters_read, int):
            raise TypeError()

        self._chapters_read = chapters_read

        if self._chapters_last_notified is None:
            self._chapters_last_notified = 0

    def set_manga_provider(self, manga_provider: MangaProvider | None, manga_provider_url: str | None) -> None:
        """Set the manga_provider and its url to the current ``Manga``"""

        if not isinstance(manga_provider, (MangaProvider, None)):
            raise TypeError()
        if not isinstance(manga_provider_url, (str, None)) or manga_provider_url == "":
            raise TypeError()

        self._manga_provider = manga_provider
        self._manga_provider_url = manga_provider_url

    def to_embed(self) -> tuple[Embed, File]:
        """Convert the ``Manga`` to a ``discord.Embed`` and ``discord.File``"""

        image_path = self.picture_file()

        # TODO: fix!!!
        # get the aspect color
        im = Image.open(image_path)
        pix = im.load()
        central_rgb = pix[int(im.size[0]/2), int(im.size[1]/2)][:-1:]
        c = 0
        # while the color is black, look at the next pixel
        while all((item < 50 for item in central_rgb)):
            c += 1
            if int(im.size[0]/2+c) >= im.width or int(im.size[1]/2+c) >= im.height:
                break
            central_rgb = pix[int(im.size[0]/2+c), int(im.size[1]/2+c)][:-1:]

        embed_var = Embed(title=self.title) #, color=Color.from_rgb(*central_rgb))
        embed_var.add_field(name="English title", value=self.title_translated, inline=False)
        embed_var.add_field(name="Chapters read", value=f"{self._chapters_read or '?'} / {self._chapters_total or '?'}")
        embed_var.add_field(name="Score", value=str(self.score), inline=False)
        embed_var.add_field(name="Status", value=self.status, inline=False)
        embed_var.add_field(name="MAL link", value=f"https://myanimelist.net/manga/{self.mal_id}")

        file = File(image_path, filename=os.path.basename(image_path))
        embed_var.set_image(url=f"attachment://{os.path.basename(image_path)}")

        return embed_var, file

    def __str__(self) -> str:
        return self.title
