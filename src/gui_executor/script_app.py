from __future__ import annotations

import argparse
import importlib
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import matplotlib
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from rich.protocol import is_renderable

from gui_executor.view import ConsoleOutput

matplotlib.use("Qt5Agg")

HERE = Path(__file__).parent.resolve()


class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self, fig: Figure, parent=None):
        super().__init__(fig)


class MainWindow(QMainWindow):
    def __init__(self, script: Path):
        super().__init__()

        ratio = 16 / 9
        width = 960

        self.script: Path = script

        QTimer.singleShot(500, self.run_script)

        self.figures_layout = QHBoxLayout()
        self.figures_layout.setContentsMargins(0, 0, 0, 0)

        self.text_layout = QHBoxLayout()
        self.text_layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.figures_layout)
        self.main_layout.addLayout(self.text_layout)

        self.main_widget: QWidget = QWidget()
        self.main_widget.setLayout(self.main_layout)

        self.setMinimumSize(width, int(width / ratio))
        self.setCentralWidget(self.main_widget)

        self.show()

    def run_script(self):

        loader = importlib.machinery.SourceFileLoader(self.script.stem, str(self.script))
        spec = importlib.util.spec_from_loader(self.script.stem, loader)
        script = importlib.util.module_from_spec(spec)
        loader.exec_module(script)

        response = script.main()

        if isinstance(response, tuple):
            figures = [x for x in response if isinstance(x, Figure)]
            renderables = [x for x in response if is_renderable(x)]
        else:
            figures = [response] if isinstance(response, Figure) else []
            renderables = [response] if is_renderable(response) else []

        if figures:

            hbox = QHBoxLayout()
            hbox.setContentsMargins(0, 0, 0, 0)

            for fig in figures:
                canvas_box = QVBoxLayout()
                canvas_box.setContentsMargins(0, 0, 0, 0)
                sc = PlotCanvas(fig)
                toolbar = NavigationToolbar(sc, self)
                toolbar.setIconSize(QSize(18, 18))  # TODO: this should be configurable
                canvas_box.addWidget(sc)
                canvas_box.addWidget(toolbar)
                hbox.addLayout(canvas_box)

            widget = QWidget()
            widget.setLayout(hbox)
            # widget.setMinimumSize(600, 480)

            self.figures_layout.addWidget(widget)

        if renderables:

            hbox = QHBoxLayout()
            hbox.setContentsMargins(0, 0, 0, 0)

            for text in renderables:
                text_widget = ConsoleOutput()
                text_widget.append(text)
                hbox.addWidget(text_widget)

            self.text_layout.addLayout(hbox)

        self.main_widget.adjustSize()
        self.adjustSize()


def main():
    parser = argparse.ArgumentParser(prog='script-app')
    parser.add_argument('--script', help='location of the Python script to execute')

    args = parser.parse_args()

    if args.script is None:
        print("You need to provide the --script option.")
        parser.print_help()
        return

    app = QApplication([])
    app.setWindowIcon(QIcon(str(HERE / "icons/script_app.svg")))

    main_window = MainWindow(script=Path(args.script))
    main_window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
