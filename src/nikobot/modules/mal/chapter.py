"""A module containing the ```Chapter`` class"""

class Chapter:
    """A class representing a single chapter within a manga"""

    def __init__(self, title: str, url: str) -> None:
        if not isinstance(title, str):
            raise TypeError(f"Expected {str}, got {type(title)}")
        if not isinstance(url, str):
            raise TypeError(f"Expected {str}, got {type(url)}")

        self.title = title
        self.url = url
        self.number = float(self.url.rsplit("/", maxsplit=1)[1].split("-", maxsplit=1)[1])

    def __str__(self) -> str:
        return self.title
