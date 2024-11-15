"""Custom esceptions for general usage"""

class CustomException(Exception):
    """The base class for all custom exceptions"""

    def __init__(self, *args, **kwargs):
        default_message = type(self).default_message

        if args:
            super().__init__(*args, **kwargs)
        else:
            # exception was raised without args
            super().__init__(default_message, **kwargs)

    default_message = ""

class KeyNotFound(CustomException):
    """Exception raised when the key is not found in the storage"""

    default_message = "The requested key could not be found"

class MultipleReplies(CustomException):
    """Exception raised when replying multiple times to the same discord command"""

    default_message = "Commands can only be replied once to"

class NoneTypeException(CustomException):
    """Exception raised when a value is unexpectedly None"""

    default_message = "DIdn't expect None as a value here"

class SingletonInstantiation(CustomException):
    """Exception raised when a singleton classi sinstantiated twice"""

    default_message = "The singleton class can only be instantiated once"

class UserNotFound(CustomException):
    """Exception raised when the discord user wasn't found"""

    default_message = "The discord user couldn't be found"
