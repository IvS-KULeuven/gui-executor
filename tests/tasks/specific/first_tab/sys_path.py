from gui_executor.exec import exec_task


@exec_task(immediate_run=True)
def print_sys_path():
    import sys
    print(sys.path)
