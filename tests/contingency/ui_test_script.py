import sys
import time

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
    print(f"{type(x) = }, {type(y) = }")
    return x, y


@exec_ui()
def func_with_only_kwargs(*, a: str, b: int = 42, c):
    print(f"func_with_only_kwargs({a=}, {b=}, {c=})")
    return a, b, c


@exec_ui()
def long_duration_func():
    print("Sleeping for 10s..")
    time.sleep(10)
    return "Done"


@exec_ui()
def raise_a_value_error():
    print("This function will raise a ValueError after 1s...")
    print("This message is sent to stderr.", file=sys.stderr)
    time.sleep(1.0)
    raise ValueError("Exception raised as an example..")


@exec_ui()
def plot_sin(png_dir: str = "/Users/rik/Desktop"):
    import matplotlib.pyplot as plt
    import math

    plt.plot([math.sin(x) for x in range(100)])
    plt.savefig(f"{png_dir}/sin.png")

    print(f"Plot 'sin.png'' saved in {png_dir}")


@exec_ui()
def output_in_several_steps(n_steps: int = 10, sleep: float = 1.0):
    """
    This function goes through 'n_steps' steps and waits 'sleep' time between the steps.
    At each step, the step number is printed, then the functions sleeps. The intended
    use is to determine if we can catch the stdout while the function is running.

    Args:
        n_steps (int): number of steps to take [default: 10]
        sleep (float): number of seconds to sleep between steps [default: 1.0]

    Returns:
        Nothing is returned.
    """
    for n in range(n_steps):
        print(f"step {n}..")
        time.sleep(sleep)
