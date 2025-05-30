"""Custom esceptions for general usage"""

from abllib.error import CustomException

from discord.ext import commands

class MissingToken(CustomException):
    """Exception raised when the discord bots' token is missing"""

    default_messages = {
        0: "The discord bots' token is missing. Visit https://discord.com/developers to create a new one."
    }

class MultipleReplies(CustomException):
    """Exception raised when replying multiple times to the same discord command"""

    default_messages = {
        0: "Commands can only be replied once to"
    }

class UserNotFound(CustomException):
    """Exception raised when the discord user wasn't found"""

    default_messages = {
        0: "The discord user couldn't be found",
        1: "The discord user {0} couldn't be found"
    }

class MissingRequiredArgument(commands.MissingRequiredArgument):
    """Exception raised when a command was called without a required argument"""

class TooManyArguments(commands.TooManyArguments):
    """Exception raised when a command was called with too many arguments"""
