from gui_executor.exec import exec_task
from gui_executor.utypes import VariableName


@exec_task()
def input_variable_name(a_float: float, model: VariableName("model")) -> str:
    # When no value was provided in the arguments panel, value will be None
    print(f"{a_float = }, {type(a_float)=}, {model = }, {type(model)=}")
    return f"{model = }, {type(model)=}"
