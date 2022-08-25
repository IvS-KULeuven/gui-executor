import rich

from gui_executor.utypes import ListList
from gui_executor.exec import exec_ui


@exec_ui()
def list_of_lists(
        x_list: ListList([int, str, str])
):

    rich.print("x_list = ", x_list)
    return x_list


@exec_ui()
def list_of_lists_with_defaults(
        x_list: ListList([int, float, str], [42, 2.54, "Test data"])
):
    rich.print("x_list = ", x_list)
    return x_list


@exec_ui()
def tuple_list_argument(
        x_tuple: tuple = (1, 2, 3, 4),
        x_list: list = None  # don't provide a mutable default!
):
    rich.print("x_tuple = ", x_tuple)
    rich.print("x_list = ", x_list)
    return x_tuple, x_list


@exec_ui()
def list_of_lists_with_bool(
        x_list: ListList([int, bool, float, str, str], [123, True, 0.13, 'CSL', 'CSL EM Final'])
):

    rich.print("x_list = ", x_list)
    return x_list
