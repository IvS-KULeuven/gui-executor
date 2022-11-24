from enum import Enum
from pathlib import Path

from gui_executor.exec import exec_task
from gui_executor.exec import exec_recurring_task
from gui_executor.exec import StatusType
from gui_executor.utils import format_datetime
from gui_executor.utils import read_id
from gui_executor.utils import write_id

UI_MODULE_DISPLAY_NAME = "01 - Recurring Tasks"

ID_FILE = Path('~').expanduser() / "id.txt"


class HexapodID(str, Enum):
    H1A = "1A"
    H1B = "1B"
    H2A = "2A"
    H2B = "2B"


@exec_recurring_task(status_type=StatusType.PERMANENT)
def show_hexapod_id():

    return f"Hexapod ID = {read_id(ID_FILE)}"


@exec_task()
def set_id(id_: HexapodID):
    write_id(id_, ID_FILE)


@exec_task(immediate_run=True)
def get_id():
    return f"ID = {read_id(ID_FILE)}"


# @exec_recurring_task(status_type=StatusType.NORMAL)
# def show_time():
#     return format_datetime()
