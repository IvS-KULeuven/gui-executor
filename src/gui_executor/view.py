from functools import partial
from typing import Callable
from typing import Dict
from typing import List

from PyQt5.QtCore import QObject
from PyQt5.QtCore import QRunnable
from PyQt5.QtCore import QThreadPool
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout

from .exec import get_arguments


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


class View(QMainWindow):
    def __init__(self):
        super().__init__()
        self._buttons = []
        self.setWindowTitle("Contingency GUI")

        self.setGeometry(300, 300, 300, 200)

        # The main frame in which all the other frames are located, the outer Application frame

        app_frame = QFrame()
        app_frame.setObjectName("AppFrame")

        self._layout_panels = QVBoxLayout()
        self._layout_buttons = QVBoxLayout()

        self._layout_panels.addLayout(self._layout_buttons)
        self._current_args_panel = None

        app_frame.setLayout(self._layout_panels)

        self.setCentralWidget(app_frame)

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

        # args, kwargs = request_arguments(ui_args)

        args = {
            "func_with_args": ([23, 42], {}),
            "compare_args": ([75, 75], {}),
            "concatenate_args": (["hello, ", "World!"], {}),
            "func_with_only_kwargs": ([], {'a': 21, 'c': 4}),
            "long_duration_func": ([], {}),
            "raise_a_value_error": ([], {}),
        }

        filled_args = args.get(button.label)[0]
        filled_kwargs = args.get(button.label)[1]

        args_panel = QLabel(f"args[{button.label}] = {filled_args}, {filled_kwargs}")

        if self._current_args_panel is not None:
            self._layout_panels.removeWidget(self._current_args_panel)

        self._layout_panels.addWidget(args_panel)
        self._current_args_panel = args_panel

        self.function_thread = worker = FunctionRunnable(button.function, filled_args, filled_kwargs)
        self.function_thread.start()

        worker.signals.data.connect(self.function_output)
        worker.signals.finished.connect(self.function_complete)
        worker.signals.error.connect(self.function_error)

    @pyqtSlot(object)
    def function_output(self, data: object):
        print(data)

    @pyqtSlot()
    def function_complete(self):
        ...

    @pyqtSlot(Exception)
    def function_error(self, msg: Exception):
        print(msg)
