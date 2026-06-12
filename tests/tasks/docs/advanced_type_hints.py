from enum import IntEnum

from gui_executor.exec import exec_task, exec_ui
from gui_executor.utypes import Callback, DropdownList, FixedList, ListList


@exec_task()
def save_observation(
    coordinates: FixedList([float, float], name="lat, long"),  # type: ignore
    time: str,
    bird_name: str,
):
    """
    Saves the observation into the database.

    Args:
        coordinates (list): the longitude and latitude coordinates of the observation (decimal degrees)
        time (str): the time of the observation [YYYY/MM/DD HH:MM:SS]
        bird_name (str): the name of the bird

    """
    print(f"A {bird_name} was spotted at [{coordinates[0]:.6f}, {coordinates[1]:.6f}]")


@exec_task()
def save_targets(
    targets: ListList([int, float, str], [1, 0.0, "target-A"], name="id, angle, label"),  # type: ignore
):
    """
    Save a dynamic number of target definitions.

    Args:
        targets: list of [id, angle, label]
    """
    print(f"{targets = }")
    return targets


@exec_task()
def choose_filters(
    filters: DropdownList(
        ["none", "bias", "dark", "flat"],
        defaults=["bias", "dark"],
        name="Image filters",
    ),  # type: ignore
):
    """
    Select one or more filters to apply.

    Args:
        filters: list of selected filter names
    """
    print(f"{filters = }")
    return filters


class Digit(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3


def available_digits():
    return Digit


def default_digit():
    return Digit.TWO


@exec_task()
def select_digit(digit: Callback(available_digits, name="digit", default=default_digit)):  # type: ignore
    """Select a digit from values determined at runtime."""
    print(f"{digit = }")


@exec_ui()
def select_mode(mode: Callback(lambda: ["full", "fast"], name="mode")):  # type: ignore
    print(f"{mode = }")


@exec_ui()
def use_calibration(enabled: Callback(lambda: True, name="calibration")):  # type: ignore
    print(f"{enabled = }")
