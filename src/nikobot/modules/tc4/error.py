"""Custom esceptions for usage within the ``tc4`` module"""

from abllib.error import CustomException

class AspectNotFound(CustomException):
    """Exception raised when the requested aspect wasn't found"""

    default_messages = {
        0: "The requested aspect couldn't be found",
        1: "The requested aspect {0} couldn't be found"
    }

class MissingRoute(CustomException):
    """
    Exception raised when a node doesn't contain a route to another node
    
    This esception should never occur normally
    """

    default_messages = {
        0: ""
    }
