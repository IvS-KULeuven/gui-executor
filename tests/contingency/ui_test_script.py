import time
from typing import Dict

from gui_executor.exec import exec_ui

# The reason for the two simple functions concatenate_args and compare_args is to
# be able to test that more than the first function is found.


@exec_ui(description="button function to concat arguments")
def concatenate_args(arg1, arg2):
    """Concatenates the two arguments with the '+' operator."""
    print(f"concatenate_args({arg1=}, {arg2=})")
    return arg1 + arg2


@exec_ui()
def compare_args(arg1, arg2):
    """Compares the two arguments with the '==' operator."""
    print(f"compare_args({arg1=}, {arg2=})")
    return arg1 == arg2


@exec_ui()
def func_with_args(x: int, y: float):
    print(f"func_with_args({x=}, {y=})")
    return x, y


@exec_ui()
def func_with_only_kwargs(*, a: str, b: int = 42, c):
    print(f"func_with_only_kwargs({a=}, {b=})")
    return a, b


@exec_ui()
def long_duration_func():
    print("Sleeping for 10s..")
    time.sleep(10)
    return "Done"


@exec_ui()
def raise_a_value_error():
    raise ValueError("Exception raised as an example..")
