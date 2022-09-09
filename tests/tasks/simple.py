from gui_executor.exec import exec_ui


@exec_ui(immediate_run=True)
def immediate_run():
    print("[blue]The task has run successfully[/]")
