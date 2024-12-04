"""Module containing the pylint test"""

import os

def test_pylint():
    """Checks if all git-tracked python files adhere to pylint rules"""

    if os.name == "nt":
        files = os.popen("git ls-files *.py").read()
        files = " ".join([file.strip() for file in files.split("\n")])
        assert "Your code has been rated at 10.00/10" in os.popen(f"pylint {files}").read()
    else:
        assert "Your code has been rated at 10.00/10" in os.popen("pylint $(git ls-files '*.py')").read()
