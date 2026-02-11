from pathlib import Path

from gui_executor.exec import exec_ui

HERE = Path(__file__).parent.resolve()
ICON_PATH = HERE / "../../../../src/gui_executor/icons/"


@exec_ui()
def no_icons_given(): ...


@exec_ui(icons=(ICON_PATH / "arrow-down.svg",))
def one_icon_given(): ...


# @exec_ui(icons=(__file__, __file__))
# def file_is_no_icon_file():
#     ...


# @exec_ui(icons=("a-name-that-surely-does-not-exists.png", __file__))
# def incorrect_icon_path_given():
#     ...


@exec_ui(icons=(ICON_PATH / "arrow-up.svg", ICON_PATH / "arrow-up-selected.svg"))
def two_icons_given(): ...


@exec_ui(icons=(ICON_PATH / "arrow-up.svg", ICON_PATH / "arrow-down.svg"))
def up_down_icons(): ...


@exec_ui(
    icons=(
        ICON_PATH / "hexapod-retract.svg",
        ICON_PATH / "hexapod-retract-selected.svg",
    ),
    display_name="To Retracted Position",
)
def hexapod_to_retracted_position(): ...


@exec_ui(
    icons=(ICON_PATH / "hexapod-homing.svg", ICON_PATH / "hexapod-homing-selected.svg"),
    display_name="Homing",
)
def hexapod_homing(): ...


@exec_ui(
    icons=(HERE / "icons/aeu-on.svg", HERE / "icons/aeu-on-selected.svg"),
    display_name="AEU",
)
def aeu_icon(): ...
