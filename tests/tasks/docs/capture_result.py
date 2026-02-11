from gui_executor.exec import exec_task

UI_MODULE_DISPLAY_NAME = "Capturing function responses"


@exec_task(capture_response=("model", "_", "hexhw"))
def generate_model(name: str = "LDO -> CSL"):
    print(f"Generating model: {name}")

    model = "This is a model"
    s = "an unused return value..."
    hexhw = "this is a reference to a hardware device"

    return model, s, hexhw
