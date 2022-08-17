from pathlib import Path

import pytest

from gui_executor.config import load_config

HERE = Path(__file__).parent.resolve()


def test_check_environment_for_script():

    config = load_config(HERE / "data/scripts.yaml")

    cmd = config.get_command_for_script("Check Environment")
    cmd.execute()
    cmd.get_output()


def test_check_environment_for_snippet():

    config = load_config(HERE / "data/snippets.yaml")

    cmd = config.get_command_for_snippet("Check Environment")
    if cmd.get_required_args():
        pytest.fail("Didn't expect there were required arguments for this test.")
    else:
        cmd.parse_args()

    cmd.execute()
    cmd.get_output()

    assert cmd.get_error() is None
