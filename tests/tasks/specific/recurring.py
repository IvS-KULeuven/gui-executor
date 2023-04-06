from gui_executor.exec import exec_recurring_task

ticks = 0


@exec_recurring_task()
def sleep_1s():
    global ticks
    ticks += 1
    return f"Ticks: {ticks}"
