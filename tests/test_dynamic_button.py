from PyQt5.QtWidgets import QApplication

from gui_executor.view import DynamicButton
from gui_executor.exec import exec_ui

UI_MODULE_DISPLAY_NAME = "Dynamic Button"


def test_constructor():

    @exec_ui()
    def func(x):
        return x

    app = QApplication([])

    # func.__ui_module_name__ = "local"

    button = DynamicButton("Test Button", func)

    assert button
    assert button.module_name == "test_dynamic_button"
    assert button.function_display_name == "Test Button"
    assert button.module_display_name == "Dynamic Button"
