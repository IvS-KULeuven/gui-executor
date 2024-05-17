from gui_executor.utils import copy_func

# Import all the tasks that you want to gather in this TAB

from tasks.specific.first_tab.sys_path import print_sys_version
from tasks.specific.first_tab.sys_path import print_sys_path
from tasks.specific.second_tab.print_this import print_this
from tasks.specific.third_tab.second_row import print_args

UI_MODULE_DISPLAY_NAME = "02 - Print Functions"

# Make sure all imported tasks are copied and named

print_sys_version = copy_func(print_sys_version, UI_MODULE_DISPLAY_NAME)
print_sys_path = copy_func(print_sys_path, UI_MODULE_DISPLAY_NAME)
print_this = copy_func(print_this, UI_MODULE_DISPLAY_NAME, "Import this")
print_args = copy_func(print_args, UI_MODULE_DISPLAY_NAME)
