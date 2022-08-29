import pathlib
from gui_executor.exec import exec_ui

UI_MODULE_DISPLAY_NAME = "Console Output"


@exec_ui(display_name="Returns output")
def generates_a_lot_of_return(n_paragraphs: int = 10):

    from lorem_text import lorem

    out1 = lorem.paragraphs(n_paragraphs)
    out2 = pathlib.Path(__file__).read_text()

    return out1, out2


@exec_ui(display_name="Prints output")
def generates_a_lot_of_output(n_paragraphs: int = 10):

    from lorem_text import lorem

    print(lorem.paragraphs(n_paragraphs), flush=True)
    print()
    print(pathlib.Path(__file__).read_text(), flush=True)
