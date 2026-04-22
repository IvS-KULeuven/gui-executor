from gui_executor.exec import StatusType, exec_recurring_task

ticks = 0


@exec_recurring_task(status_type=StatusType.NORMAL)
def sleep_1s():
    global ticks
    ticks += 1
    return f"Ticks: {ticks}"
