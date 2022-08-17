# This script is intended to be imported and define some global variables and functions

from gui_executor.exec import exec_ui


EXEC_SCRIPT = True


def echo(msg: str):
    return msg


@exec_ui()
def ui_echo(msg: str):
    return msg
