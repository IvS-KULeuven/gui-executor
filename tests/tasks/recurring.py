import time

from gui_executor.exec import exec_recurring_task

ticks = 0


@exec_recurring_task()
def sleep_1s():
    global ticks
    # time.sleep(10.0)
    ticks += 1
    return f"Ticks: {ticks}"
