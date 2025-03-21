"""Custom esceptions for usage within the ``mal`` module"""

from abllib.error import CustomException

class MangaFetchException(CustomException):
    """Exception raised when fetching the manga failed"""

    default_message = "The requested manga could not be fetched"

class MangaNotFound(CustomException):
    """Exception raised when the manga is not found on the current provider's website"""

    default_message = "The requested manga could not be found"

class MediaTypeError(CustomException):
    """Exception raised when trying to process a light novel/novel"""

    default_message = "Currently only supports manga and not light novel/novel"

class MALResponseError(CustomException):
    """Exception raised when MyAnimeList returns an error as a response"""

    default_message = "MyAnimeList responded with an internal error"

class UnknownProvider(CustomException):
    """Exception raised when the manga provider is not (yet) supported"""

    default_message = "The manga provider is not (yet) supported"

class UserNotFound(CustomException):
    """Exception raised when the MAL user is not found"""

    default_message = "The requested user could not be found"
