from gui_executor.utils import copy_func

# Import all the tasks that you want to gather in this TAB

from tasks.specific.first_tab.sys_path import print_sys_version
from tasks.specific.first_tab.sys_path import print_sys_path
from tasks.specific.second_tab.print_this import print_this
from tasks.specific.third_tab.second_row import print_args
from tasks.specific.third_tab.first_row import immediate_run, immediate_run_kernel

# Make sure all imported tasks are copied and named

name = "Print Functions"

print_sys_version = copy_func(print_sys_version, name)
print_sys_path = copy_func(print_sys_path, name)
print_this = copy_func(print_this, name, "Import this")
print_args = copy_func(print_args, name)

name = "Immediate Functions"

immediate_run = copy_func(immediate_run, name)
immediate_run_kernel = copy_func(immediate_run_kernel, name)
