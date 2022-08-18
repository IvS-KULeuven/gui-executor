from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Callable
from typing import Dict
from typing import List

from PyQt5.QtCore import QObject
from PyQt5.QtCore import QRunnable
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QThreadPool
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QTextCursor
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from .exec import Argument
from .exec import ArgumentKind
from .exec import get_arguments
from .utils import capture
from .utils import stringify_args
from .utils import stringify_kwargs

HERE = Path(__file__).parent.resolve()


class VLine(QFrame):
    """Presents a simple Vertical Bar that can be used in e.g. the status bar."""

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.VLine | QFrame.Sunken)


class HLine(QFrame):
    """Presents a simple Horizontal Bar that can be used to separate widgets."""

    def __init__(self):
        super().__init__()
        self.setLineWidth(0)
        self.setMidLineWidth(1)
        self.setFrameShape(QFrame.HLine | QFrame.Sunken)


class FunctionThreadSignals(QObject):
    """
    Defines the signals available from a running function thread.

    Supported signals are:

    finished
        str: the function name
        bool: if the function was successfully executed, i.e. no exception was raised
    error
        str: Exception string
    data
        any object that was returned by the function
    """

    finished = pyqtSignal(str, bool)
    error = pyqtSignal(Exception)
    data = pyqtSignal(object)


class FunctionRunnable(QRunnable):
    def __init__(self, func: Callable, args: List, kwargs: Dict):
        super().__init__()
        self.signals = FunctionThreadSignals()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self):
        success = False
        self.signals.data.emit("-" * 20)
        self.signals.data.emit(
            f"Running function {self._func.__name__}({stringify_args(self._args)}{', ' if self._args else ''}"
            f"{stringify_kwargs(self._kwargs)})...")
        try:
            with capture() as out:
                response = self._func(*self._args, **self._kwargs)
            self.signals.data.emit(out.stdout)
            self.signals.data.emit(out.stderr)
            self.signals.data.emit(response)
            success = True
        except Exception as exc:
            self.signals.data.emit(out.stdout)
            self.signals.data.emit(out.stderr)
            self.signals.error.emit(exc)
            success = False
        finally:
            self.signals.finished.emit(self._func.__name__, success)

    def start(self):
        QThreadPool.globalInstance().start(self)


class ConsoleOutput(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.insertPlainText("")
        self.setMinimumSize(0, 300)

    @pyqtSlot(str)
    def append(self, text):
        self.moveCursor(QTextCursor.End)
        current = self.toPlainText()

        if current == "":
            self.insertPlainText(text)
        else:
            self.insertPlainText("\n" + text)

        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())


class IconLabel(QLabel):

    IconSize = QSize(16, 16)

    def __init__(self, icon_path: Path | str, size: QSize = IconSize):
        super().__init__()

        self.icon_path = str(icon_path)
        self.setFixedSize(size)

    def paintEvent(self, *args, **kwargs):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        renderer = QSvgRenderer()
        renderer.load(self.icon_path)
        renderer.render(painter)

        painter.end()


class DynamicButton(QWidget):

    IconSize = QSize(30, 30)
    HorizontalSpacing = 2

    def __init__(self, label: str, func: Callable,
                 icon_path: Path | str = None, final_stretch=True, size: QSize = IconSize):
        super().__init__()
        self._function = func
        self._label = label
        self._icon = None

        self.icon_path = str(icon_path or HERE / "icons/023-evaluate.svg")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        label_icon = IconLabel(icon_path=self.icon_path, size=size)
        label_text = QLabel(label)

        layout.addWidget(label_icon)
        layout.addSpacing(self.HorizontalSpacing)
        layout.addWidget(label_text)

        if final_stretch:
            layout.addStretch()

    @property
    def function(self) -> Callable:
        return self._function

    @property
    def label(self) -> str:
        return self._label

    def __repr__(self):
        return f"DynamicButton(\"{self.label}\", {self.function})"


class ArgumentsPanel(QGroupBox):
    def __init__(self, button: DynamicButton, ui_args: Dict[str, Argument]):
        super().__init__(button.label)

        self._button = button
        self._args_fields = []
        self._kwargs_fields = {}

        # The arguments panel is a Widget with an input text field for each of the arguments.
        # The text field is pre-filled with the default value if available.

        vbox = QVBoxLayout()

        for name, arg in ui_args.items():
            input_field = QLineEdit()
            input_field.setObjectName(name)
            input_field.setPlaceholderText(str(arg.default) if arg.default else "")
            if arg.kind == ArgumentKind.POSITIONAL_ONLY:
                self._args_fields.append(input_field)
            elif arg.kind in [ArgumentKind.POSITIONAL_OR_KEYWORD, ArgumentKind.KEYWORD_ONLY]:
                self._kwargs_fields[name] = input_field
            else:
                print("ERROR: Only POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, and KEYWORD_ONLY arguments are supported!")
            label = QLabel(name)
            hbox = QHBoxLayout()
            hbox.addWidget(label)
            hbox.addWidget(input_field)
            vbox.addLayout(hbox)

        self.run_button = QPushButton("run")
        vbox.addWidget(self.run_button, alignment=Qt.AlignRight)

        self.setLayout(vbox)

    @property
    def function(self):
        return self._button.function

    @property
    def args(self):
        return [
            arg.displayText()
            for arg in self._args_fields
        ]

    @property
    def kwargs(self):
        return {
            name: arg.displayText() or arg.placeholderText()
            for name, arg in self._kwargs_fields.items()
        }


class View(QMainWindow):
    def __init__(self):
        super().__init__()

        self._buttons = []
        self.function_thread: FunctionRunnable

        self.setWindowTitle("Contingency GUI")

        # self.setGeometry(300, 300, 500, 200)

        # The main frame in which all the other frames are located, the outer Application frame

        self.app_frame = QFrame()
        self.app_frame.setObjectName("AppFrame")

        # We don't want this QFrame to shrink below 500 pixels, therefore set a minimum horizontal size
        # and set the policy such that it can still expand from this minimum size. This will be used
        # when we use adjustSize after replacing the arguments panel.

        self.app_frame.setMinimumSize(500, 0)
        sp = self.app_frame.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.MinimumExpanding)
        self.app_frame.setSizePolicy(sp)

        self._layout_panels = QVBoxLayout()
        self._layout_buttons = QVBoxLayout()

        self._layout_panels.addLayout(self._layout_buttons)
        self._layout_panels.addWidget(HLine())
        self._current_args_panel: QWidget = QWidget()
        self._current_args_panel.hide()
        self._layout_panels.addWidget(self._current_args_panel)
        self._console_panel = ConsoleOutput()
        self._layout_panels.addWidget(HLine())
        self._layout_panels.addWidget(self._console_panel)

        self.app_frame.setLayout(self._layout_panels)

        self.setCentralWidget(self.app_frame)

    def run_function(self, func: Callable, args: List, kwargs: Dict):

        # TODO:
        #  * disable run button (should be activate again in function_complete?)

        self.function_thread = worker = FunctionRunnable(func, args, kwargs)
        self.function_thread.start()

        worker.signals.data.connect(self.function_output)
        worker.signals.finished.connect(self.function_complete)
        worker.signals.error.connect(self.function_error)

    def add_function_button(self, func: Callable):

        button = DynamicButton(func.__name__, func)
        button.mouseReleaseEvent = partial(self.the_button_was_clicked, button)
        # button.clicked.connect(partial(self.the_button_was_clicked, button))

        self._buttons.append(button)
        self._layout_buttons.addWidget(button)

    def the_button_was_clicked(self, button: DynamicButton, *args, **kwargs):

        # TODO
        #   * This should be done from the control or model and probably in the background?
        #   * Add ArgumentsPanel in a tabbed widget? When should it be removed from the tabbed widget? ...

        ui_args = get_arguments(button.function)

        args_panel = ArgumentsPanel(button, ui_args)
        args_panel.run_button.clicked.connect(
            lambda checked: self.run_function(args_panel.function, args_panel.args, args_panel.kwargs)
        )

        if self._current_args_panel:
            self._layout_panels.replaceWidget(self._current_args_panel, args_panel)
            self._current_args_panel.setParent(None)
        else:
            self._layout_panels.addWidget(args_panel)

        self._current_args_panel = args_panel
        self.app_frame.adjustSize()
        self.adjustSize()

    @pyqtSlot(object)
    def function_output(self, data: object):
        self._console_panel.append(str(data))

    @pyqtSlot(str, bool)
    def function_complete(self, name: str, success: bool):
        if success:
            self._console_panel.append(f"function '{name}' execution finished.")
        else:
            self._console_panel.append(f"function '{name}' raised an Exception.")

    @pyqtSlot(Exception)
    def function_error(self, msg: Exception):
        self._console_panel.append(f"{msg.__class__.__name__}: {msg}")
