from typing import Tuple

from gui_executor.exec import exec_task, FileName, FilePath, Directory

UI_MODULE_DISPLAY_NAME = "02 – Capture Responses"


@exec_task()
def return_a_float(value: float = 0.0) -> float:
    return value


@exec_task(capture_response=("idx", "val"))
def return_int_and_float(idx: int = 0, value: float = 0.0) -> Tuple[int, float]:
    """
    Function that returns its arguments. This tasks is to showcase the possibility for the developer
    to specify variable names for return values. The values returned by the function will then be
    captured in these variables and will be available in the kernel after the task has run.
    If the developer didn't specify any variable names, the returned values will be captured in the
    variable 'response'.

    Args:
        idx: an integer number
        value:  a floating point number

    Returns:
        The tuple (idx, val) with the given values from the arguments.
    """
    return idx, value


@exec_task(capture_response=("model", "_", "hexhw"))
def generate_model():
    model = "This is a model"
    s = "an unused return value..."
    hexhw = "this is a reference to a hardware device"
    return model, s, hexhw
