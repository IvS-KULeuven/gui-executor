from gui_executor.exec import exec_ui

UI_MODULE_DISPLAY_NAME = "Second Row of Tasks"


@exec_ui()
def print_args(name: str = "Rik Huygen", nick_name: str = "Rik"):
    print(f"{name = }, {nick_name = }")
