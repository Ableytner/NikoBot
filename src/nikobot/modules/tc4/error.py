"""Custom esceptions for usage within the ``tc4`` module"""

from ...util.error import CustomException

class AspectNotFound(CustomException):
    """Exception raised when the requested aspect wasn't found"""

    default_message = "The requested aspect couldn't be found"

class MissingRoute(CustomException):
    """
    Exception raised when a node doesn't contain a route to another node
    
    This esception should never occur normally
    """

    default_message = ""
