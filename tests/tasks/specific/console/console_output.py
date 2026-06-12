import logging
import rich

from gui_executor.exec import exec_task

_LOGGER = logging.getLogger(__name__)


@exec_task()
def console_output(message: str) -> str:
    # This task is to test a problem with rendering a string that contains text between square brackets.
    #
    # If you remove the blank after the opening bracket, the GUI will crash!

    msg = f"Console output: {message}"

    print("-----")

    print("Console output using plain print")
    print(msg)
    print(f"Console output with f-string: {msg}")

    print("-----")

    rich.print("Console output using rich print")
    rich.print(msg)
    rich.print(f"Console output with f-string: {msg}")

    print("-----")

    _LOGGER.info(msg)

    return msg


@exec_task()
def print_numpy_output(rich_output: bool) -> str:
    import numpy as np

    arr = np.array([[1, 2, 3], [4, 5, 6]])

    if rich_output:
        print = rich.print
    else:
        import builtins

        print = builtins.print

    print(
        f"The numpy array is printed twice with '{'rich.print' if rich_output else 'builtins.print'}', "
        f"first with a comma and then with an f-string. The GUI should render both correctly without crashing."
    )

    print("-----")

    print("Numpy array:\n", arr)
    print(f"Numpy array:\n{arr}")

    print("-----")

    arr_str = "[0., 1., 2.]"

    print("Numpy array as string:", arr_str)
    print(f"Numpy array as string: {arr_str}")

    print("-----")

    arr_str = "[np.float64(0.0), np.float64(0.0), np.float64(0.0), np.float64(0.0), np.float64(-0.0), np.float64(0.0)]"

    print("Numpy array as string:", arr_str)
    print(f"Numpy array as string: {arr_str}")

    print("-----")

    _LOGGER.info(f"Numpy array: {arr}")

    return "Numpy array printed to console"
