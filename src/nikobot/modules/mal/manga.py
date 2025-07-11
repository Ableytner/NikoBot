"""Module containing the ``Manga`` class"""

from __future__ import annotations

import os
from datetime import datetime
from enum import Enum

from abllib import fs
from abllib.log import get_logger
from abllib.storage import VolatileStorage
import requests
from PIL import Image
from discord import Embed, File

from . import error, mal_helper, manganato_helper, natomanga_helper
from .chapter import Chapter

logger = get_logger("mal")

class MangaProvider(Enum):
    """
    An Enum replesenting Manga providers
    
    These are websites which provide manga chapters
    """

    MANGANATO = "manganato" # manganato.com is down, don't use it
    NATOMANGA = "natomanga"

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
        self.chapters: list[Chapter] = []
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
        if "provider" in export and not isinstance(export["provider"], str):
            raise TypeError()
        if "provider_url" in export and not isinstance(export["provider_url"], str):
            raise TypeError()
        if "chapters_last_notified" in export and not isinstance(export["chapters_last_notified"], int):
            raise TypeError()

        manga = Manga.from_mal_id(export["mal_id"])

        if "provider" in export \
           and "provider_url" in export \
           and export["provider"] != MangaProvider.MANGANATO.name:
            manga.set_manga_provider(MangaProvider[export["provider"]], export["provider_url"])
        if "chapters_last_notified" in export:
            manga._chapters_last_notified = export["chapters_last_notified"]

        return manga
    # pylint: enable=protected-access

    @staticmethod
    def from_mal_id(mal_id: int) -> Manga:
        """Factory method creating a new Manga object using the MyAnimeList id"""

        if not isinstance(mal_id, int):
            raise TypeError()

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
            "mal_id": self.mal_id
        }
        if self._manga_provider is not None \
           and self._manga_provider_url is not None:
            export_data["provider"] = self._manga_provider.name
            export_data["provider_url"] = self._manga_provider_url
        if self._chapters_last_notified is not None and self._chapters_last_notified > 0:
            export_data["chapters_last_notified"] = self._chapters_last_notified
        return export_data

    def fetch_chapters(self) -> bool:
        """
        Fetch the newest released chapter from the set provider, using manganato as the default
        
        Return whether fetching worked or not
        """

        if self._manga_provider is not None:
            self._fetch_chapters()
        else:
            manga_url = natomanga_helper.get_manga_url([self.title, self.title_translated] + self.synonyms)
            if manga_url is None:
                logger.warning(f"Manga {self.mal_id} could not be found automatically")
                return False

            self.set_manga_provider(MangaProvider.NATOMANGA, manga_url)

            try:
                self._fetch_chapters()
            except error.CustomException as e:
                # reset manga_provider if fetching didn't work
                self.set_manga_provider(None, None)
                raise e

        return True

    def _fetch_chapters(self) -> None:
        chapters: list[Chapter] = None
        match self._manga_provider:
            case MangaProvider.MANGANATO:
                chapters = manganato_helper.get_chapters(self._manga_provider_url)
            case MangaProvider.NATOMANGA:
                chapters = natomanga_helper.get_chapters(self._manga_provider_url)
            # default case
            case _:
                raise error.UnknownProvider()

        if len(chapters) == 0:
            logger.warning(f"Manga {self.mal_id} was propably deleted at url {self._manga_provider_url}, " +
                  "removing and trying again later")
            self.set_manga_provider(None, None)
            return

        self.chapters = chapters

        latest_chapter = max(chapters, key=lambda x: x.number)
        self._chapters_total = int(latest_chapter.number)

    def picture_file(self) -> str:
        """
        Download the preview picture, returning the picture file path

        Returns a cached picture if available
        """

        path = fs.absolute(VolatileStorage["cache_dir"], "mal", str(self.mal_id))

        os.makedirs(path, exist_ok=True)

        filename = fs.sanitize(f"{self.title_translated}.{self.picture_url.rsplit('.', maxsplit=1)[1]}")
        path = fs.absolute(path, filename)

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

        if not isinstance(manga_provider, MangaProvider) and manga_provider is not None:
            raise TypeError()
        if not isinstance(manga_provider_url, str) and manga_provider is not None:
            raise TypeError()
        if manga_provider_url == "":
            raise ValueError()

        self._manga_provider = manga_provider
        self._manga_provider_url = manga_provider_url

    def to_embed(self) -> tuple[Embed, File]:
        """Convert the ``Manga`` to a ``discord.Embed`` and ``discord.File``"""

        image_path = self.picture_file()

        # TODO: fix!!!
        # get the average color
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

        embed_var.add_field(name="English title",
                            value=self.title_translated,
                            inline=False)

        if self._chapters_read is not None or self._chapters_total is not None:
            embed_var.add_field(name="Chapters read",
                                value=f"{self._chapters_read or '?'} / {self._chapters_total or '?'}",
                                inline=False)

        embed_var.add_field(name="Score",
                            value=str(self.score),
                            inline=False)
        embed_var.add_field(name="Status",
                            value=self.status,
                            inline=False)

        if len(self.chapters) > 0 and self._chapters_read is not None:
            for chapter in self.chapters:
                if int(chapter.number) == self._chapters_read + 1:
                    embed_var.add_field(name="Next chapter link",
                                        value=chapter.url,
                                        inline=False)
        if embed_var.fields[-1].name != "Next chapter link" and self._manga_provider_url is not None:
            embed_var.add_field(name="Manga provider url",
                                value=self._manga_provider_url,
                                inline=False)

        embed_var.add_field(name="MAL link",
                            value=f"https://myanimelist.net/manga/{self.mal_id}",
                            inline=False)

        file = File(image_path)
        embed_var.set_image(url=f"attachment://{os.path.basename(image_path)}")

        return embed_var, file

    def __str__(self) -> str:
        return self.title
