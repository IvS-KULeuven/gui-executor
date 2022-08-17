import os
import textwrap

import pytest

from gui_executor.utils import get_required_args
from gui_executor.utils import replace_environment_variable
from gui_executor.utils import replace_required_args
from gui_executor.utils import var_exists


def test_replace_environment_variable():

    assert replace_environment_variable("PLAIN_STRING") == "PLAIN_STRING"

    assert replace_environment_variable("~/data/CSL") == "~/data/CSL"

    os.environ["DATA_STORAGE_LOCATION"] = "/Users/rik/data/CSL"
    assert replace_environment_variable("ENV['DATA_STORAGE_LOCATION']") == "/Users/rik/data/CSL"

    os.environ["DATA_STORAGE_LOCATION"] = "/Users/rik/data"
    assert replace_environment_variable("ENV['DATA_STORAGE_LOCATION']/CSL") == "/Users/rik/data/CSL"


@pytest.mark.parametrize("code", [
    "just one line without arg template",
    "a = <<a:int>>",
    "b = <<b:str>>",
    textwrap.dedent(
        """\
        # This script requires the following arguments: count, obsid, timeout
        
        count = <<count:int>>
        func(<<obsid:str>>, <<timeout:float>>)
        
        """
    )
])
def test_get_required_args(code):

    print()
    args = get_required_args(code)
    print(f"{args = }")
    code = replace_required_args(code, args)
    print(f"{code = }")

GLOBAL_VAR = 42

def test_var_exists():

    print()

    assert not var_exists("x")
    assert not var_exists("__GUI_INPUTS__")

    for _ in range(2):
        ...

    assert var_exists("_")
    print(f"{_ = }")
    assert var_exists("__name__")
    print(f"{__name__ = }")
    assert var_exists("__file__")
    print(f"{__file__ = }")

    assert var_exists('GLOBAL_VAR')
    print(f"{GLOBAL_VAR = }")
