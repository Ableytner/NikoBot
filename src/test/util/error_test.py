"""Module containing tests for the different types of errors"""

# pylint: disable=protected-access, missing-class-docstring, pointless-statement, expression-not-assigned

import pytest

from nikobot.util import error

def test_customexception_inheritance():
    """Ensure that CustomException inherits from Exception"""

    assert issubclass(error.CustomException, Exception)

def test_customexception_custom_message():
    """Ensure that CustomException instantiation with a custom messaage keeps the message"""

    class TestException(error.CustomException):
        default_messages = {
            0: "This exception is used in tests"
        }

    try:
        raise TestException("This message should be retained")
    except TestException as e:
        assert str(e) == "This message should be retained"
    else:
        pytest.fail("Expected an exception")

def test_customexception_default_message():
    """Ensure that CustomException instantiation without a custom messaage uses the default message"""

    class TestException(error.CustomException):
        default_messages = {
            0: "This exception is used in tests"
        }

    try:
        raise TestException()
    except TestException as e:
        assert str(e) == "This exception is used in tests"
    else:
        pytest.fail("Expected an exception")
