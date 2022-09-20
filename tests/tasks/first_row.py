from gui_executor.exec import exec_ui

UI_MODULE_DISPLAY_NAME = "First Row of Tasks"


@exec_ui(immediate_run=True)
def immediate_run():
    print("[blue]The task has run successfully[/]")


@exec_ui(immediate_run=True, use_kernel=True)
def immediate_run_kernel():
    print("[blue]The task has run successfully in kernel[/]")
