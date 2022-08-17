import time
from pathlib import Path

import pytest
from executor import ExternalCommand

from gui_executor.command import CommandError
from gui_executor.config import load_config

HERE = Path(__file__).parent.resolve()


def test_script_execution():

    config = load_config(HERE / "data/scripts.yaml")

    cmd = config.get_command_for_script("Long Running Command")

    args = cmd.get_required_args()
    assert ('duration', 'int') in args

    duration = 2
    cmd.parse_args(duration=duration)

    assert cmd.can_execute()

    cmd_line = cmd.get_command_line()
    assert f"--duration {duration}" in cmd_line

    cmd = ExternalCommand(cmd_line, capture=True, asynchronous=True)
    cmd.start()

    cmd.wait()

    assert f"sleep({duration}).." in cmd.output


def test_script_execution_high_level_command():

    config = load_config(HERE / "data/scripts.yaml")

    duration = 3

    cmd = config.get_command_for_script("Long Running Command")
    cmd.parse_args(duration=duration)
    cmd.execute()  # wait for the command to finish
    response = cmd.get_output()

    assert f"sleep({duration}).." in response
    assert f"Finished sleeping." in cmd.get_output()

    cmd.execute(asynchronous=True)

    time.sleep(1)

    assert cmd.is_running()
    assert cmd.get_error() is None
    # WARNING: When executing asynchronous, make sure the output is flushed regularly by the script
    assert f"sleep({duration})" in cmd.get_output()
    assert f"Finished sleeping." not in cmd.get_output()

    while cmd.is_running():
        time.sleep(1)

    assert f"sleep({duration})..." in cmd.get_output()
    assert f"Finished sleeping." in cmd.get_output()


def test_script_execution_value_error():

    config = load_config(HERE / "data/scripts.yaml")

    cmd = config.get_command_for_script("Raise ValueError")

    cmd.parse_args(value=5)  # this will not trigger a ValueError
    cmd.execute()  # wait for the command to finish

    response = cmd.get_output()

    assert response == ""

    value = 50

    cmd.parse_args(value=value)  # this will trigger a ValueError
    with pytest.raises(CommandError):
        cmd.execute()

    assert cmd.get_output() == ""
    assert f"ValueError: Incorrect input received: {value}" in cmd.get_error()
