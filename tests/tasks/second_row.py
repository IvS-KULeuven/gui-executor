from gui_executor.exec import exec_ui

UI_MODULE_DISPLAY_NAME = "Second Row of Tasks"


@exec_ui()
def print_sys_path():
    import sys

    print(sys.path)
