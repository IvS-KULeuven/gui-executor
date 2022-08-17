from pathlib import Path

from gui_executor.command import ScriptCommand
from gui_executor.config import load_config

HERE = Path(__file__).parent.resolve()


def test_command_creation_from_config():

    config = load_config(HERE / "data/scripts.yaml")

    cmd = config.get_command_for_script("Long Running Command")
    assert isinstance(cmd, ScriptCommand)

    required_args = cmd.get_required_args()
    assert ('duration', 'int') in required_args

    cmd.parse_args(duration=2)
    assert cmd.can_execute()

    cmd.execute()
