from pathlib import Path

from gui_executor.model import Model
from gui_executor.utils import sys_path

HERE = Path(__file__).parent.resolve()


def test_get_ui_modules():
    with sys_path(HERE):
        model = Model(["tasks.shared.unit_tests"])

        modules = model.get_ui_modules()
        assert "immediate_run" in modules
        assert "input_requests" in modules


def test_get_ui_subpackages():
    module_path = "tasks.specific"

    with sys_path(HERE):
        model = Model([module_path])

        subpackages = model.get_ui_subpackages()
        assert "concurrency" in subpackages

        modules = model.get_ui_modules([f"{module_path}.concurrency"])
        assert "print_hello" in modules
