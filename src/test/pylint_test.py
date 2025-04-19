"""Module containing the pylint test"""

import os

import pytest

from abllib import log

logger = log.get_logger("pylint")

def test_pylint():
    """Checks if all git-tracked python files adhere to pylint rules"""

    if os.name == "nt":
        files = os.popen("git ls-files *.py").read()
        files = " ".join([file.strip() for file in files.split("\n")])

        pylint_output = []
        for line in os.popen(f"pylint {files}").readlines():
            if line.strip().strip("-") != "":
                pylint_output.append(line.strip())

        if not "Your code has been rated at 10.00/10" in pylint_output[-1]:
            for line in pylint_output:
                logger.warning(line)

            pytest.fail(pylint_output[-1])
    else:
        # logging pylint errors on linux doesn't work
        assert "Your code has been rated at 10.00/10" in os.popen("pylint $(git ls-files '*.py')").read()
