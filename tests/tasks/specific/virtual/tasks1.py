from gui_executor.utils import copy_func

# Import all the tasks that you want to gather in this TAB

from tasks.specific.third_tab.first_row import immediate_run, immediate_run_kernel

UI_MODULE_DISPLAY_NAME = "01 - Immediate Functions"

# Make sure all imported tasks are copied and named

immediate_run = copy_func(immediate_run, UI_MODULE_DISPLAY_NAME)
immediate_run_kernel = copy_func(immediate_run_kernel, UI_MODULE_DISPLAY_NAME)
