class CustomException(Exception):
    def __init__(self, *args, **kwargs):
        default_message = type(self).default_message

        if args:
            super().__init__(*args, **kwargs)
        else:
            # exception was raised without args
            super().__init__(default_message, **kwargs)
    
    default_message = ""

class MangaFetchException(CustomException):
    """Exception raised when fetching the manga failed"""

    default_message = "The requested manga could not be fetched"

class MangaNotFound(CustomException):
    """Exception raised when the manga is not found on the current provider's website"""

    default_message = "The requested manga could not be found"

class MediaTypeError(CustomException):
    """Exception raised when trying to process a light novel/novel"""

    default_message = "Currently only supports manga and not light novel/novel"

class UnknownProvider(CustomException):
    """Exception raised when the manga provider is not (yet) supported"""

    default_message = "The manga provider is not (yet) supported"

class UserNotFound(CustomException):
    """Exception raised when the MAL user is not found"""

    default_message = "The requested user could not be found"
