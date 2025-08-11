"""Custom esceptions for usage within the ``spotify`` module"""

from abllib.error import CustomException

class ApiResponseError(CustomException):
    """Exception raised when the spotify API returns an error"""

    default_messages = {
        0: "The API returned an error",
        1: "The API returned an error: {0}"
    }
    status_code: int | None
    message: str | None

class UserNotRegisteredError(CustomException):
    """Exception raised when the requested user is not yet registered"""

    default_messages = {
        0: "The requested user is not yet registered",
        1: "The requested user {0} is not yet registered"
    }
