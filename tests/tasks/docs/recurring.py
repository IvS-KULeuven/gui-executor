from gui_executor.exec import exec_recurring_task
from gui_executor.exec import StatusType


@exec_recurring_task(status_type=StatusType.PERMANENT)
def show_time():
    import time
    return time.strftime("%H:%M:%S")
