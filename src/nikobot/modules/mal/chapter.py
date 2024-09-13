"""A module containing the ```Chapter`` class"""

class Chapter:
    """A class representing a single chapter within a manga"""

    def __init__(self, title: str, url: str, number: float) -> None:
        if not isinstance(title, str): raise TypeError()
        if not isinstance(url, str): raise TypeError()
        if not isinstance(number, float): raise TypeError()

        self.title = title
        self.url = url
        self.number = number

    def __str__(self) -> str:
        return self.title
