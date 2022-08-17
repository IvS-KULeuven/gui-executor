import os
from pathlib import Path

import pytest

from gui_executor.config import load_config

HERE = Path(__file__).parent.resolve()


@pytest.fixture
def sample_config():
    return load_config(HERE / "data/sample_config.yaml")


def test_load_config(sample_config):

    assert "Python Path" in sample_config
    assert "Startup" in sample_config

    assert sample_config.name == "sample_config"
    assert sample_config.get_absolute_path("../xxx") == HERE / "xxx"

    assert "script" in sample_config["Startup"]
    assert sample_config["Startup"]["script"] == "~/cgse_startup.py"

    assert "prepend" in sample_config["Python Path"]
    assert "append" in sample_config["Python Path"]

    assert sample_config["Python Path"]["append"] == []
    assert sample_config["Python Path"]["prepend"]

    # TODO:
    #  add further tests here for other fields like Apps, Scripts, and Snippets


def test_get_script_names(sample_config):

    assert "script 01" in sample_config.get_script_names()


def test_get_app_names(sample_config):

    assert "app 01" in sample_config.get_app_names()


def test_get_snippet_names(sample_config):

    assert "snippet 01" in sample_config.get_snippet_names()


def test_get_absolute_path(sample_config):

    # get_absolute_path uses the location of the config file is the anchor point for relative paths.

    assert sample_config.get_absolute_path(Path("~")) == Path(os.environ.get("HOME"))
    assert sample_config.get_absolute_path(Path("..")) == HERE
    assert sample_config.get_absolute_path(Path(".")) == HERE / "data"
