from pathlib import Path

from gui_executor.config import load_config

HERE = Path(__file__).parent.resolve()


def test_get_cgse_version():
    """
    Test if the PYTHONPATH or sys.path is properly set to import external packages.
    When the configuration is not done correctly, this test will raise a CommandError with a:

        ModuleNotFound: No module named 'egse'.
    """
    config = load_config(HERE / "data/scripts.yaml")

    cmd = config.get_command_for_script("CGSE Version")

    cmd.execute()

    assert "CGSE Version = " in cmd.get_output()


def test_get_camtest_version():
    """
    Test if the PYTHONPATH or sys.path is properly set to import external packages.
    When the configuration is not done correctly, this test will raise a CommandError with a:

        ModuleNotFound: No module named 'egse'.
    """
    config = load_config(HERE / "data/scripts.yaml")

    cmd = config.get_command_for_script("TS Version")

    cmd.execute()

    assert "CAMTEST git version = " in cmd.get_output()
