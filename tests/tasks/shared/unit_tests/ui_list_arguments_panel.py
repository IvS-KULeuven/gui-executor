import rich

from gui_executor.utypes import DropdownList, FixedList
from gui_executor.utypes import ListList
from gui_executor.exec import exec_ui, exec_task

UI_MODULE_DISPLAY_NAME = "Arguments Panel"


@exec_ui(display_name="ListList")
def list_of_lists(x_list: ListList([int, str, str])):
    rich.print("x_list = ", x_list)
    return x_list


@exec_ui(display_name="ListList with Defaults")
def list_of_lists_with_defaults(
    x_list: ListList([int, float, str], [42, 2.54, "Test data"], name="list of lists"),
):
    rich.print("x_list = ", x_list)
    return x_list


@exec_ui()
def tuple_list_argument(
    x_tuple: tuple = (1, 2, 3, 4),
    # x_list: list = None  # don't provide a mutable default!
    x_list: list = [1, 2, 3, 4],  # don't provide a mutable default!
):
    rich.print("x_tuple = ", x_tuple)
    rich.print("x_list = ", x_list)
    return x_tuple, x_list


@exec_ui()
def list_of_lists_with_bool(
    x_list: ListList([int, bool, float, str, str], [123, True, 0.13, "CSL", "CSL EM Final"]),
):
    rich.print("x_list = ", x_list)
    return x_list


@exec_ui()
def fixed_list(x_list: FixedList([int, int, str, float])):
    rich.print("x_list = ", x_list)
    return x_list


@exec_ui()
def fixed_list_with_defaults(x_list: FixedList([int, int, str, float], [3, 42])):
    """
    Use a FixedList type hint for arguments. The type of each of the fields is given as the first argument,
    the second argument is a list with defaults, and a third argument is the name to be displayed in the
    arguments panel.

    Synopsis:
         arg: FixedList(literals: List, defaults: List, name: str)
    """
    rich.print("x_list = ", x_list)
    return x_list


@exec_ui()
def fixed_list_with_name(x_list: FixedList([int, int], [3, 42], name="X, Y")):
    rich.print("x_list = ", x_list)
    return x_list


@exec_ui(display_name="list → Numpy Array")
def list_to_array(angles: list):
    """
    Example of a task that takes a list as an argument and converts it to a numpy array.

    The list is expected to be a list of lists, where each inner list has two elements: [theta, phi].
    """
    import numpy as np

    if isinstance(angles, list):
        angles = np.array(angles)

    thetas, phis = angles[:, 0], angles[:, 1]

    print(f"{thetas = }, {phis= }")


@exec_task(display_name="List of drop-down menus")
def list_of_dropdowns(options: DropdownList(["Option 1", "Option 2", "Option 3"], name="Pick an option")):
    rich.print("options = ", options)
    return options


@exec_task(display_name="List of drop-down menus with defaults")
def list_of_dropdowns_defaults(
    options: DropdownList(
        ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"],
        defaults=["Option 2", "Option 3"],
        name="Pick an option",
    ),
):
    rich.print("options = ", options)
    return options
