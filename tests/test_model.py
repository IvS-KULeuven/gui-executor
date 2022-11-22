from pathlib import Path

from gui_executor.model import Model
from gui_executor.utils import sys_path

HERE = Path(__file__).parent.resolve()


def test_get_ui_modules():

    with sys_path(HERE):
        model = Model("tasks")

        modules = model.get_ui_modules()
        assert "first_row" in modules
        assert "second_row" in modules


def test_get_ui_subpackages():

    module_path = "tasks"

    with sys_path(HERE):
        model = Model(module_path)

        subpackages = model.get_ui_subpackages()
        assert "second_tab" in subpackages

        for subpackage in subpackages:
            modules = model.get_ui_modules(f"{module_path}.{subpackage}")
            assert "print_this" in modules
