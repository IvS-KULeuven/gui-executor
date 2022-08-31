from pathlib import Path

from gui_executor.exec import exec_ui

UI_MODULE_DISPLAY_NAME = "Path-like Arguments"


@exec_ui(display_name="Open File")
def open_file(
        filename: str = "README.md",
        location: Path = Path("/Users/rik/Documents/PyCharmProjects/gui-executor/"),
):
    print(f"{filename = }")
    print(f"{location = }")
