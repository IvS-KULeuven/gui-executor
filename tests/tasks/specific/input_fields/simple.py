from typing import Optional

from gui_executor.exec import exec_task

import locale


@exec_task()
def input_float_no_default(value: float, opt_val: Optional[int]) -> float:
    # When no value was provided in the arguments panel, value will be None
    print(f"{value = }, {type(value)=}, {opt_val = }")
    if value is not None:
        print(f"{float(value) = }")
        if isinstance(value, str):
            print(f"{locale.atof(value) = }")
    return value


@exec_task()
def input_float_with_default(value: float = 3.1415) -> float:
    # When no value was provided in the arguments panel, value will be the default
    print(f"{value = }, {type(value)=}")
    print(f"{float(value) = }")
    if isinstance(value, str):
        print(f"{locale.atof(value) = }")
    return value


@exec_task()
def input_float_with_optional_default(value: Optional[float] = 3.1415) -> float:
    # When no value was provided in the arguments panel, value will be the default
    print(f"{value = }, {type(value)=}")
    print(f"{value = }" if value is None else f"{float(value) = }")
    if isinstance(value, str):
        print(f"{locale.atof(value) = }")
    return value


@exec_task()
def input_int_no_default(value: int) -> int:
    # When no value was provided in the arguments panel, value will be None
    print(f"{value = }, {type(value)=}")
    if value is not None:
        print(f"{int(value) = }")
        if isinstance(value, str):
            print(f"{locale.atoi(value) = }")
    else:
        print(f"{value = }")

    return value


@exec_task()
def input_int_with_default(value: int = 0) -> int:
    # When no value was provided in the arguments panel, value will be the default
    print(f"{value = }, {type(value)=}")
    print(f"{int(value) = }")
    if isinstance(value, str):
        print(f"{locale.atoi(value) = }")

    return value


@exec_task()
def input_int_with_optional_default(value: Optional[int] = 0) -> int:
    # When no value was provided in the arguments panel, value will be the default
    print(f"{value = }, {type(value)=}")
    print(f"{value = }" if value is None else f"{int(value) = }")
    if isinstance(value, str):
        print(f"{locale.atoi(value) = }")

    return value


@exec_task()
def input_str_no_default(value: str) -> str:
    # When no value was provided in the arguments panel, value will be None
    print(f"{value = }, {type(value)=}")

    return value


@exec_task()
def input_str_with_default(value: str = "Hello, World!") -> str:
    # When no value was provided in the arguments panel, value will be the default
    print(f"{value = }, {type(value)=}")

    return value


@exec_task()
def input_str_with_optional_default(value: Optional[str] = None) -> str:
    # When no value was provided in the arguments panel, value will be the default
    print(f"{value = }, {type(value)=}")

    return value
