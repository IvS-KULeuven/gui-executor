from gui_executor.exec import exec_task
from gui_executor.utypes import FixedList, ListList, DropdownList


@exec_task()
def save_observation(
    coordinates: FixedList([float, float], name="lat, long"),
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
    targets: ListList([int, float, str], [1, 0.0, "target-A"], name="id, angle, label"),
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
    ),
):
    """
    Select one or more filters to apply.

    Args:
        filters: list of selected filter names
    """
    print(f"{filters = }")
    return filters
