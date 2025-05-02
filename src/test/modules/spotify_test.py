"""Module containing tests for the discord.spotify module"""

# pylint: disable=protected-access, missing-class-docstring, pointless-statement, expression-not-assigned, unused-argument

from abllib.log import get_logger

from nikobot.modules.spotify import update_helper

logger = get_logger("test")

def test_calculate_diff_nochange():
    """Ensure that the updatehelper.calculate_diff function works correctly"""

    curr = [
        "AAA",
        "AAB",
        "AAC",
        "AAD"
    ]
    new = [
        "AAA",
        "AAB",
        "AAC",
        "AAD"
    ]
    remove, add = update_helper.calculate_diff(curr, new)
    assert add == []
    assert remove == []

def test_calculate_diff_addonly():
    """Ensure that the updatehelper.calculate_diff function works correctly"""

    curr = [
        "AAA",
        "AAB",
        "AAC",
        "AAD"
    ]
    new = [
        "AAA",
        "AAB",
        "AAC",
        "AAD",
        "AAE"
    ]
    remove, add = update_helper.calculate_diff(curr, new)
    assert add == ["AAE"]
    assert remove == []

    curr = [
        "AAA",
        "AAB",
        "AAC",
        "AAD"
    ]
    new = [
        "AAA",
        "AAB",
        "AAC",
        "AAD",
        "AAE",
        "AAF"
    ]
    remove, add = update_helper.calculate_diff(curr, new)
    assert add == ["AAE", "AAF"]
    assert remove == []

def test_calculate_diff_removeonly():
    """Ensure that the updatehelper.calculate_diff function works correctly"""

    curr = [
        "AAA",
        "AAB",
        "AAC",
        "AAD"
    ]
    new = [
        "AAA",
        "AAB",
        "AAC",
        "AAD",
        "AAE"
    ]
    remove, add = update_helper.calculate_diff(curr, new)
    assert add == ["AAE"]
    assert remove == []

    curr = [
        "AAA",
        "AAB",
        "AAC",
        "AAD",
        "AAE",
        "AAF"
    ]
    new = [
        "AAA",
        "AAC",
        "AAD",
        "AAF"
    ]
    remove, add = update_helper.calculate_diff(curr, new)
    assert add == []
    assert remove == ["AAB", "AAE"]

    curr = [
        "AAA",
        "AAB",
        "AAC",
        "AAD",
        "AAE",
        "AAF",
        "AAG"
    ]
    new = [
        "AAA",
        "AAB",
        "AAC"
    ]
    remove, add = update_helper.calculate_diff(curr, new)
    assert add == []
    assert remove == ["AAD", "AAE", "AAF", "AAG"]

def test_calculate_diff_both():
    """Ensure that the updatehelper.calculate_diff function works correctly"""

    curr = [
        "AAA",
        "AAB",
        "AAC",
        "AAH",
        "AAI"
    ]
    new = [
        "AAA",
        "AAB",
        "AAH",
        "AAJ",
        "AAK"
    ]
    remove, add = update_helper.calculate_diff(curr, new)
    assert add == ["AAJ", "AAK"]
    assert remove == ["AAC", "AAI"]
