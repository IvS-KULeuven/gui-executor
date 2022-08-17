"""
This module provides functionality to read the YAML configuration files and work with its content.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict
from typing import List

import yaml
from rich.tree import Tree

from gui_executor.command import ScriptCommand
from gui_executor.command import SnippetCommand
from gui_executor.utils import walk_dict_tree


def load_config(filename: Path | str) -> ExecutorConfiguration:
    """Load the YAML config file from the given filename."""
    filename = Path(filename).expanduser().resolve()

    with filename.open(mode='r') as fd:
        config = yaml.safe_load(fd)

    config = ExecutorConfiguration(config, filename)
    config.check_config()

    return config


class ConfigError(Exception):
    pass


class ExecutorConfiguration:
    """
    This class provides easy access to the content of the Executor Configuration files.
    """
    def __init__(self, config: dict, filename: Path):
        """
        Args:
            config: an ExecutorConfiguration represented in a dictionary
            filename: full pathname of the configuration file
        """
        self._config: Dict = config
        self._filename: Path = filename
        self._name: str = filename.stem

    @property
    def name(self):
        return self._name

    def check_config(self) -> None:
        """
        Perform a basic format and content check on the config dictionary.

        Raises:
            A ConfigError when a problem is encountered.
        """
        if "Python Path" not in self._config:
            raise ConfigError(f"No 'Python Path' in the configuration file at {self._filename}")

    def get_script_names(self) -> List[str]:
        """
        Returns the names of the scripts that are defined in the configuration.
        An empty list is returned if no scripts are defined.
        """
        return list(self._config.get("Scripts", {}).keys())

    def get_app_names(self) -> List[str]:
        """
        Returns the names of the apps that are defined in the configuration.
        An empty list is returned if no apps are defined.
        """
        return list(self._config.get("Apps", {}).keys())

    def get_snippet_names(self) -> List[str]:
        """
        Returns the names of the snippets that are defined in the configuration.
        An empty list is returned if no snippets are defined.
        """
        return list(self._config.get("Snippets", {}).keys())

    def get_absolute_path(self, path: Path | str) -> Path:
        """
        Returns the absolute path for the given path. When a relative path is given, it is assumed
        this path is relative to the location of the config file.

        Args:
            path: a relative or absolute path name

        Returns:
            An absolute path (note that this absolute path may not exist, that is on the caller to check).
        """
        path = Path(path).expanduser()
        if path.is_absolute():
            return path

        config_path = self._filename.parent.resolve()
        return (config_path / path).resolve()

    def get_python_path(self):
        try:
            python_path = self._config["Python Path"]
            orig_python_path = os.environ.get("PYTHONPATH", "")
            prepend = ':'.join(python_path.get("prepend", ""))
            append = ':'.join(python_path.get("append", ""))
            python_path = f"{prepend}:{orig_python_path}:{append}"
        except KeyError:
            python_path = ""

        return python_path

    def get_environment(self):
        return self._config.get("Environment", {})

    def get_command_for_script(self, name: str) -> ScriptCommand:
        """
        Returns a ScriptCommand for the given script name.
        """
        return ScriptCommand.from_config(self, name)

    def get_command_for_snippet(self, name: str) -> SnippetCommand:
        """
        Returns a SnippetCommand for the given snippet name. Note that a snippet
        can also be a script.
        """
        return SnippetCommand.from_config(self, name)

    def __contains__(self, item):
        return item in self._config

    def __getitem__(self, item):
        return self._config[item]

    def __rich__(self):
        tree = Tree(self._name, guide_style="dim")
        walk_dict_tree(self._config, tree, text_style="dark grey")
        return tree
