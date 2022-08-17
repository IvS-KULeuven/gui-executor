from functools import partial
from typing import Callable
from typing import Dict
from typing import List

from PyQt5.QtCore import QMetaObject
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QRunnable
from PyQt5.QtCore import QThreadPool
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from .exec import get_arguments
from .exec import Argument
from .exec import ArgumentKind


class FunctionThreadSignals(QObject):
    """
    Defines the signals available from a running function thread.

    Supported signals are:

    finished
        No data
    error
        `str` Exception string
    data
        any object that was returned by the function
    """

    finished = pyqtSignal()
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
        try:
            response = self._func(*self._args, **self._kwargs)
            self.signals.data.emit(response)
        except Exception as exc:
            self.signals.error.emit(exc)
        finally:
            self.signals.finished.emit()

    def start(self):
        QThreadPool.globalInstance().start(self)


class DynamicButton(QPushButton):
    def __init__(self, label: str, func: Callable):
        super().__init__(label)
        self._function = func
        self._label = label

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

        # self.setGeometry(300, 300, 300, 200)

        # The main frame in which all the other frames are located, the outer Application frame

        self.app_frame = QFrame()
        self.app_frame.setObjectName("AppFrame")

        self._layout_panels = QVBoxLayout()
        self._layout_buttons = QVBoxLayout()

        self._layout_panels.addLayout(self._layout_buttons)
        self._current_args_panel: QWidget = None

        self.app_frame.setLayout(self._layout_panels)

        self.setCentralWidget(self.app_frame)

    def run_function(self, func: Callable, args: List, kwargs: Dict):
        self.function_thread = worker = FunctionRunnable(func, args, kwargs)
        self.function_thread.start()

        worker.signals.data.connect(self.function_output)
        worker.signals.finished.connect(self.function_complete)
        worker.signals.error.connect(self.function_error)

    def add_function_button(self, func: Callable):
        print(f"Creating a button for {func.__name__ = }")

        button = DynamicButton(func.__name__, func)
        button.clicked.connect(partial(self.the_button_was_clicked, button))

        self._buttons.append(button)
        self._layout_buttons.addWidget(button)

    def the_button_was_clicked(self, button: DynamicButton, *args, **kwargs):

        print(f"{button = }, {args = }, {kwargs = }")

        # TODO
        #   This should be done from the control or model and probably in the background?

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
        print(data)

    @pyqtSlot()
    def function_complete(self):
        ...

    @pyqtSlot(Exception)
    def function_error(self, msg: Exception):
        print(msg)
