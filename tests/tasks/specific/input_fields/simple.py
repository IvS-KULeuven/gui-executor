from gui_executor.exec import exec_task

import locale

@exec_task()
def input_float_no_default(value: float) -> float:
    # When no value was provided in the arguments panel, value will be None
    print(f"{value = }, {type(value)=}")
    if value is not None:
        print(f"{float(value) = }")
        if isinstance(value, str):
            print(f"{locale.atof(value) = }")
    return value

@exec_task()
def input_float_with_default(value: float = 3.1415) -> float:
    print(f"{value = }, {type(value)=}")
    print(f"{float(value) = }")
    if isinstance(value, str):
        print(f"{locale.atof(value) = }")
    return value
