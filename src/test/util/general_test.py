"""Module containing tests for the util.general module"""

# pylint: disable=protected-access, missing-class-docstring, pointless-statement, expression-not-assigned

import pytest

from src.nikobot.util import general

def test_levenshthein_input_types():
    """Ensures the levenshtein_distance() function doesn't allow invalid inputs"""

    general.levenshtein_distance("test", "teet")

    class TestClass():
        pass
    disallowed = [
        None,
        15,
        ["test", "test"],
        TestClass()
    ]

    for item in disallowed:
        with pytest.raises(TypeError):
            general.levenshtein_distance(item, "test")
        with pytest.raises(TypeError):
            general.levenshtein_distance("test", item)
        with pytest.raises(TypeError):
            general.levenshtein_distance(item, item)

def test_levenshthein_output():
    """Ensures the levenshtein_distance() function generates correct outputs"""

    assert general.levenshtein_distance("test", "test") == 0
    assert general.levenshtein_distance("test", "teet") == 1
    assert general.levenshtein_distance("test", "salad") == 5
