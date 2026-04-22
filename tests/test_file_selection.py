from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget

from gui_executor.utils import select_directory


def test_select_directory():
    app = QApplication(["-platform", "offscreen"])

    widget = QWidget()
    widget.show()

    print()
    directory = select_directory(str(Path("~/Desktop/").expanduser()))
    assert directory is not None
    assert directory == str(Path("~/Desktop/").expanduser())
    assert Path(directory).exists()

    QTimer.singleShot(1000, app.exit)  # Exit the app after 1 second

    app.exec()
