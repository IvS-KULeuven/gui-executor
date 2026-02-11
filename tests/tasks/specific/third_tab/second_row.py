from gui_executor.exec import exec_ui
from gui_executor.utils import copy_func

from tasks.specific.second_tab.print_this import print_this

UI_MODULE_DISPLAY_NAME = "Second Row of Tasks"


@exec_ui()
def print_args(name: str = "Rik Huygen", nick_name: str = "Rik"):
    print(f"{name = }, {nick_name = }")


print_this = copy_func(print_this, UI_MODULE_DISPLAY_NAME)


@exec_ui()
def sleep(seconds: float = 20):
    import time

    print(f"Sleeping for {seconds:3.1f}s... ")
    time.sleep(seconds)
