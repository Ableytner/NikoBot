"""Custom esceptions for usage within the ``mal`` module"""

from abllib.error import CustomException

class CloudflareChallengeError(CustomException):
    """Exception raised when solving a Cloudflare challenge didn't work"""

    default_messages = {
        0: "Cloudflare challenge solving didn't work"
    }

class FlareSolverrResponseError(CustomException):
    """Exception raised when FlareSolverr returns an invalid response"""

    default_messages = {
        0: "FlareSolverr responded with an invalid response",
        1: "FlareSolverr responded with an invalid response: {0}"
    }

class MangaFetchException(CustomException):
    """Exception raised when fetching the manga failed"""

    default_messages = {
        0: "The requested manga could not be fetched"
    }

class MangaNotFound(CustomException):
    """Exception raised when the manga is not found on the current provider's website"""

    default_messages = {
        0: "The requested manga could not be found"
    }

class MediaTypeError(CustomException):
    """Exception raised when trying to process a light novel/novel"""

    default_messages = {
        0: "Currently only supports manga and not light novel/novel"
    }

class MALResponseError(CustomException):
    """Exception raised when MyAnimeList returns an error as a response"""

    default_messages = {
        0: "MyAnimeList responded with an internal error"
    }

class UnknownProvider(CustomException):
    """Exception raised when the manga provider is not (yet) supported"""

    default_messages = {
        0: "The manga provider is not (yet) supported"
    }

class UserNotFound(CustomException):
    """Exception raised when the MAL user is not found"""

    default_messages = {
        0: "The requested user could not be found"
    }
