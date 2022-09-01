from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget

from gui_executor.utils import select_directory


def test_select_directory():

    app = QApplication(['-platform', 'offscreen'])

    widget = QWidget()
    widget.show()

    print()
    print(select_directory("/Users/rik/Desktop/plot.png"), flush=True)

    # QTimer.singleShot(1000, app.exit)

    app.exec()
