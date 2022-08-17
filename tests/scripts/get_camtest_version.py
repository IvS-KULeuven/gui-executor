"""
This script runs a function from an external package that is installed at a different location.

The purpose of this script is to check that the PYTHONPATH or sys.path are properly set.
"""

import logging
import subprocess
from pathlib import Path

import rich

from egse.system import chdir

LOGGER = logging.getLogger("camtest.version")


with chdir(Path(__file__).parent):
    try:
        std_out = subprocess.check_output(
            ["git", "describe", "--tags", "--long"], stderr=subprocess.PIPE)
        git_version = std_out.strip().decode("ascii")
    except subprocess.CalledProcessError as exc:
        LOGGER.error(
            f"A git error occurred for the `git describe` command: {exc}", stack_info=True)
        git_version = "no git-version determined"

rich.print(f"CAMTEST git version = [bold default]{git_version}[/]")
