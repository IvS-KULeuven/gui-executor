from enum import Enum
from enum import IntEnum

from gui_executor.exec import exec_ui

UI_MODULE_DISPLAY_NAME = "Enum Arguments"


class Digit(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9


class OperatingMode(IntEnum):
    STANDBY = 0
    SELFTEST = 1
    ALIGNMENT = 2
    FC_TVAC = 3


class CSLSiteId(str, Enum):
    CSL = "CSL"
    CSL1 = "CSL1"
    CSL2 = "CSL2"


@exec_ui()
def str_enum(csl_site: CSLSiteId = CSLSiteId.CSL, setup_id: int = 98):
    print(f"{csl_site=}, {setup_id=}")


@exec_ui()
def name_of(digit: Digit):
    print(f"{digit.value} -> {digit.name}")


@exec_ui()
def value_of(digit: Digit):
    print(f"{digit.name} = {digit.value}")


@exec_ui()
def select_operating_mode(mode: OperatingMode):

    print(f"{mode.name} = {mode.value} \[{mode=}]")
