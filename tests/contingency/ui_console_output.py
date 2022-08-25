import pathlib
from gui_executor.exec import exec_ui


@exec_ui()
def generate_lot_of_output(n_paragraphs: int = 10):

    from lorem_text import lorem

    out1 = lorem.paragraphs(n_paragraphs)
    out2 = pathlib.Path(__file__).read_text()

    return out1, out2
