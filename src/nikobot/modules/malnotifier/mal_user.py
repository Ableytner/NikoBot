from __future__ import annotations

from . import exec, mal_helper
from .manga import Manga
from ... import util

class MALUser():
    def __init__(self, mal_username: str, discord_id: int) -> None:
        self.username: str = mal_username
        self.discord_id: int = discord_id
        self.manga: dict[int, Manga] = {}

    @staticmethod
    def from_export(discord_user_id: int, export: dict[str, str]) -> MALUser:
        """Factory method creating a new MALUser object using the export data created by my_user.export()"""

        if not isinstance(discord_user_id, int):
            raise TypeError()
        if not isinstance(export["mal_username"], str):
            raise TypeError()
        if not isinstance(export["manga"], list):
            raise TypeError()

        maluser = MALUser(export["mal_username"], discord_user_id)
        for manga in export["manga"]:
            maluser.add_manga(Manga.from_export(manga))
        return maluser

    def add_manga(self, manga: Manga) -> None:
        if not isinstance(manga, Manga):
            raise TypeError()
        
        self.manga[manga.mal_id] = manga

    def export(self) -> dict[str, str]:
        """Create a dictionary which is JSON-compliant and can be used to recreate this exact User"""

        return {
            "mal_username": self.username,
            "manga": [
                manga.export() for manga in self.manga.values()
            ]
        }

    def fetch_manga_chapters(self) -> None:
        """Fetch the released number of chapters from the respective providers"""

        for manga in self.manga.values():
            try:
                manga.fetch_chapters()
            except Exception as e:
                raise exec.MangaFetchException(f"Error fetching manga {manga.mal_id}: {e.args[0]}")
        self.save_to_storage()

    def fetch_manga_list(self) -> None:
        """Fetch the users manga list from MyAnimeList"""

        manga_list = mal_helper.get_manga_list_from_username(self.username)
        for entry in manga_list:
            mal_id = entry["mal_id"]
            if mal_id in self.manga:
                self.manga[mal_id].set_chapters_read(entry["read_chapters"])
            else:
                try:
                    manga = Manga.from_mal_id(mal_id)
                    manga.set_chapters_read(entry["read_chapters"])
                    self.manga[mal_id] = manga
                except exec.MediaTypeError:
                    pass
        self.save_to_storage()

    def save_to_storage(self) -> None:
        util.PersistentStorage[f"mal.user.{self.discord_id}"] = self.export()
