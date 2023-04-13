from gui_executor.exec import exec_task


@exec_task()
def raise_an_exception(value: float):
    _ = 1 / value
