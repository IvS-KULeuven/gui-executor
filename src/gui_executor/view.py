from __future__ import annotations

import errno
import fcntl
import os
import select
import sys
import tempfile
import textwrap
import time
from functools import partial
from pathlib import Path
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from PyQt5.QtCore import QObject
from PyQt5.QtCore import QRunnable
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QThreadPool
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QIntValidator
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QTextCursor
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from executor import ExternalCommand
from executor import ExternalCommandFailed
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text

from .exec import Argument
from .exec import ArgumentKind
from .exec import get_arguments
from .kernel import MyKernel
from .kernel import start_qtconsole
from .utils import capture
from .utils import create_code_snippet
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


# Helper function to add the O_NONBLOCK flag to a file descriptor
def make_async(fd):
    fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)


# Helper function to read some data from a file descriptor, ignoring EAGAIN errors
def read_async(fd):
    try:
        return fd.read()
    except IOError as exc:
        if exc.errno != errno.EAGAIN:
            raise exc
        else:
            return b''


class FunctionRunnable(QRunnable):
    def __init__(self, func: Callable, args: List, kwargs: Dict):
        super().__init__()
        self.signals = FunctionThreadSignals()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._check_for_input = False
        self._input_patterns = []

    def check_for_input(self, patterns: Tuple):
        self._check_for_input = True
        self._input_patterns = [pattern.rstrip() for pattern in patterns]

    def run(self):
        # We can in the future decide based on exec_ui arguments in how to run the function
        # self.run_in_current_interpreter()
        # self.run_in_kernel()
        # self.run_in_qprocess()
        self.run_in_external_command()

    def run_in_current_interpreter(self):
        # This runs the function within the current Python interpreter. This might be a security risk
        # if you allow to run functions that are not under your control.
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

    def run_in_kernel(self):
        ...

    def run_in_qprocess(self):
        ...

    def run_in_external_command(self):
        tmp = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmp.write(create_code_snippet(self._func, self._args, self._kwargs))
        tmp.close()

        self.signals.data.emit("-" * 20)

        options = dict(capture=True, capture_stderr=True, asynchronous=True, buffered=False, input=True)
        try:
            # We could actually just use SubProcess here to with the correct settings
            with ExternalCommand(f"{sys.executable} {tmp.name}", **options) as cmd:
                make_async(cmd.stdout)
                make_async(cmd.stderr)

                while True:
                    # Wait for data to become available
                    out, *_ = select.select([cmd.stdout, cmd.stderr], [], [])

                    # Try reading some data from each
                    line_out = read_async(cmd.stdout)
                    line_err = read_async(cmd.stderr)

                    if line_out:
                        self.signals.data.emit(line := line_out.decode(cmd.encoding).rstrip())
                        # Try to detect when the process is requesting input.
                        # TODO: request input from user through QLineEdit field...
                        if self._check_for_input and any(pattern in line for pattern in self._input_patterns):
                            time.sleep(1.0)
                            cmd.subprocess.stdin.write(b'Y\n')
                    if line_err:
                        self.signals.data.emit(line := line_err.decode(cmd.encoding).rstrip())

                    if cmd.subprocess.poll() is not None:
                        break

                # Previous attempts that didn't work as expected. Need to document this....

                # while cmd.is_running:
                #     if cmd.stdout.readable():
                #         out = cmd.stdout.readline().decode(cmd.encoding)
                #         self.signals.data.emit(out.rstrip())
                #     if cmd.stderr.readable():
                #         err = cmd.stderr.readline().decode(cmd.encoding)
                #         self.signals.data.emit(err.rstrip())

                # for out, err in itertools.zip_longest(
                #         # iter(lambda: cmd.stdout.readline().decode(cmd.encoding), u''),
                #         # iter(lambda: cmd.stderr.readline().decode(cmd.encoding), u'')
                #         iter(lambda: cmd.stdout.readline().decode(cmd.encoding), u''),
                #         iter(lambda: cmd.stderr.readline().decode(cmd.encoding), u'')
                # ):
                #     out and self.signals.data.emit(out.rstrip())
                #     err and self.signals.data.emit(err.rstrip())

            cmd.wait()

        except ExternalCommandFailed as exc:
            # self._console_panel.append(cmd.error_message)
            # This error message is also available in the decoded_stderr.
            self.signals.error.emit(exc)

        # if out := cmd.decoded_stdout:
        #     self._console_panel.append(out)
        if err := cmd.decoded_stderr:
            self.signals.data.emit(err)

        if cmd.is_finished:
            if cmd.failed:
                self.signals.finished.emit(self._func.__name__, False)
            else:
                self.signals.finished.emit(self._func.__name__, True)

        # print(f"{tmp.name = }")
        os.unlink(tmp.name)

    def start(self):
        QThreadPool.globalInstance().start(self)


class ConsoleOutput(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.insertPlainText("")
        self.setMinimumSize(600, 300)
        monospaced_font = QFont("Courier New")
        monospaced_font.setStyleHint(QFont.Monospace)
        monospaced_font.setPointSize(14)  # TODO: should be a setting
        self.setFont(monospaced_font)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__contextMenu)

    @pyqtSlot(str)
    def append(self, text):
        self.moveCursor(QTextCursor.End)

        console = Console(record=True, force_terminal=False, force_jupyter=False)
        with console.capture():
            console.print(text)

        exported_html = console.export_html(
            inline_styles=True,
            code_format="<pre style=\"font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace\">{code}\n</pre>"
        )

        self.insertHtml(exported_html)

        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())

    def __contextMenu(self):
        self._normalMenu = self.createStandardContextMenu()
        self._addCustomMenuItems(self._normalMenu)
        self._normalMenu.exec_(QCursor.pos())

    def _addCustomMenuItems(self, menu):
        menu.addSeparator()
        menu.addAction(u'Clear', self.clear)


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


class SourceCodeWindow(QWidget):
    def __init__(self, func: Callable):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0,)
        try:
            source_code_filename = func.__wrapped__.__code__.co_filename
            source_line = func.__wrapped__.__code__.co_firstlineno
        except AttributeError:
            source_code_filename = func.__code__.co_filename
            source_line = func.__code__.co_firstlineno
        source_code = Path(source_code_filename).read_text()

        text_edit = QTextEdit()

        console = Console(record=True, width=1200)
        syntax = Syntax(source_code, "python", theme='default')

        with console.capture():
            console.print(syntax)

        exported_html = console.export_html(
            inline_styles=True,
            code_format="<pre style=\"font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace\">{code}\n</pre>"
        )

        text_edit.setFontFamily('Courier')
        text_edit.insertHtml(exported_html)

        document = text_edit.document()
        cursor = QTextCursor(document)
        cursor.setPosition(source_line)
        # cursor.movePosition()
        text_edit.setTextCursor(cursor)
        layout.addWidget(text_edit)

        self.setMinimumSize(1200, 600)
        self.setGeometry(100, 100, 1200, 600)
        self.setLayout(layout)


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

        self.setToolTip(func.__doc__)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        context_menu = QMenu(self)

        view_source_action = context_menu.addAction("View source ...")
        view_source_action.triggered.connect(self.view_source)

        context_menu.exec_(event.globalPos())

    def view_source(self):
        self.source_code_window = SourceCodeWindow(self.function)
        self.source_code_window.show()

    @property
    def function(self) -> Callable:
        return self._function

    @property
    def module_name(self) -> str:
        """Returns the name of the module where the function resides."""
        return self._function.__ui_module__

    @property
    def label(self) -> str:
        return self._label

    def __repr__(self):
        return f"DynamicButton(\"{self.label}\", {self.function})"


class ArgumentsPanel(QGroupBox):
    def __init__(self, button: DynamicButton, ui_args: Dict[str, Argument]):
        super().__init__(button.label)

        self._button = button
        self._ui_args = ui_args
        self._args_fields = {}
        self._kwargs_fields = {}

        # The arguments panel is a Widget with an input text field for each of the arguments.
        # The text field is pre-filled with the default value if available.

        vbox = QVBoxLayout()
        grid = QGridLayout()

        for idx, (name, arg) in enumerate(ui_args.items()):
            if arg.annotation is bool:
                input_field = QCheckBox("")
                input_field.setCheckState(Qt.Checked if arg.default else Qt.Unchecked)
            else:
                input_field = QLineEdit()
                input_field.setObjectName(name)
                input_field.setPlaceholderText(str(arg.default) if arg.default else "")
                if arg.annotation is not None:
                    input_field.setToolTip(f"The expected type is {arg.annotation.__name__}.")
                else:
                    input_field.setToolTip("No type has been specified..")
                if arg.annotation is int:
                    input_field.setValidator(QIntValidator())
                elif arg.annotation is float:
                    input_field.setValidator(QDoubleValidator())

            if arg.kind == ArgumentKind.POSITIONAL_ONLY:
                self._args_fields[name] = input_field
            elif arg.kind in [ArgumentKind.POSITIONAL_OR_KEYWORD, ArgumentKind.KEYWORD_ONLY]:
                self._kwargs_fields[name] = input_field
            else:
                print("ERROR: Only POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, and KEYWORD_ONLY arguments are supported!")

            label = QLabel(name)
            type_hint = QLabel(f"[{arg.annotation.__name__}]" if arg.annotation is not None else None)
            type_hint.setStyleSheet("color: gray")

            # Stretch the middle column of the grid. That is needed when there is only one argument and it's a bool
            # i.e. a CheckBox. If we do not stretch, the checkbox will be centered.
            grid.setColumnStretch(1, 1)
            grid.addWidget(label, idx, 0)
            grid.addWidget(input_field, idx, 1)
            grid.addWidget(type_hint, idx, 2)

        vbox.addLayout(grid)

        hbox = QHBoxLayout()
        self.kernel_checkbox = QCheckBox("run in kernel")
        self.kernel_checkbox.setCheckState(Qt.Checked if self.function.__ui_use_kernel__ else Qt.Unchecked)
        self.run_button = QPushButton("run")
        hbox.addWidget(self.kernel_checkbox)
        hbox.addStretch()
        hbox.addWidget(self.run_button)

        vbox.addLayout(hbox)

        self.setLayout(vbox)

    @property
    def function(self):
        return self._button.function

    @property
    def args(self):
        return [
            self._cast_arg(name, field)
            for name, field in self._args_fields.items()
        ]

    @property
    def kwargs(self):
        return {
            name: self._cast_arg(name, field)
            for name, field in self._kwargs_fields.items()
        }

    @property
    def use_kernel(self):
        return self.kernel_checkbox.checkState() == Qt.Checked

    def _cast_arg(self, name: str, field: QLineEdit | QCheckBox):
        arg = self._ui_args[name]

        if arg.annotation is bool:
            return field.checkState() == Qt.Checked

        value = field.displayText() or field.placeholderText()

        try:
            return arg.annotation(value)
        except (ValueError, TypeError):
            return value


class FunctionButtonsPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.n_cols = 4  # This must be a setting or configuration option

        # The modules are arranged in a vertical layout and each of the functions in that module is arranged in a
        # horizontal layout. Modules are added when a new button is added for a not yet existing module.

        self.modules: Dict[str, QGridLayout] = {}
        self.buttons: Dict[str, int] = {}
        self.module_layout = QVBoxLayout()

        self.setLayout(self.module_layout)

    def add_button(self, button: DynamicButton):
        module_name = button.module_name
        if module_name not in self.modules:
            grid = QGridLayout()
            # Make sure all columns have equal width
            for idx in range(self.n_cols):
                grid.setColumnStretch(idx, 1)
            gbox = QGroupBox(module_name.rsplit(".", 1)[-1])
            gbox.setLayout(grid)
            gbox.setStyleSheet(textwrap.dedent("""
                QGroupBox
                {
                    font-size: 14px;
                    font-weight: light;
                    color: grey;
                }
            """))
            self.module_layout.addWidget(gbox)
            self.modules[module_name] = grid
            self.buttons[module_name] = 0

        self.buttons[module_name] += 1
        button_count = self.buttons[module_name]

        row = (button_count - 1) // self.n_cols
        col = (button_count - 1) % self.n_cols
        self.modules[module_name].addWidget(button, row, col)


class KernelPanel(QWidget):
    def __init__(self):
        super().__init__()

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)

        kernel_specs = list(MyKernel.get_kernel_specs())
        try:
            idx = kernel_specs.index("python3")
        except ValueError:
            idx = 0
        self.kernel_list = QComboBox()
        self.kernel_list.addItems(list(kernel_specs))
        self.kernel_list.setCurrentIndex(idx)

        hbox.addStretch(1)
        hbox.addWidget(QLabel("available kernels"))
        hbox.addWidget(self.kernel_list)

        self.setLayout(hbox)

    @property
    def selected_kernel(self) -> str:
        return self.kernel_list.currentText()


class View(QMainWindow):
    def __init__(self, app_name: str = None):
        super().__init__()

        self._qt_console: Optional[ExternalCommand] = None
        self._kernel: Optional[MyKernel] = None
        self._buttons = []
        self.function_thread: FunctionRunnable

        self.setWindowTitle(app_name or "GUI Executor")

        # self.setGeometry(300, 300, 500, 200)

        # The main frame in which all the other frames are located, the outer Application frame

        self.app_frame = QFrame()
        self.app_frame.setObjectName("AppFrame")

        # We don't want this QFrame to shrink below 500 pixels, therefore set a minimum horizontal size
        # and set the policy such that it can still expand from this minimum size. This will be used
        # when we use adjustSize after replacing the arguments panel.

        self.app_frame.setMinimumSize(500, 0)  # TODO: should be a setting
        sp = self.app_frame.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.MinimumExpanding)
        self.app_frame.setSizePolicy(sp)

        self._layout_panels = QVBoxLayout()
        self._layout_buttons = FunctionButtonsPanel()

        self._layout_panels.addWidget(self._layout_buttons)
        self._layout_panels.addWidget(HLine())
        self._current_args_panel: QWidget = QWidget()
        self._current_args_panel.hide()
        self._layout_panels.addWidget(self._current_args_panel)
        self._console_panel = ConsoleOutput()
        self._layout_panels.addWidget(HLine())
        self._layout_panels.addWidget(self._console_panel)

        self.app_frame.setLayout(self._layout_panels)

        self.setCentralWidget(self.app_frame)

        QTimer.singleShot(500, self.start_kernel)

        self._rich_console = Console(force_terminal=False, force_jupyter=False)

        self._toolbar = QToolBar()
        self._toolbar.setIconSize(QSize(40, 40))
        self.addToolBar(self._toolbar)

        # Add a button to the toolbar to restart the kernel

        kernel_button = QAction(QIcon(str(HERE / "icons/reload-kernel.svg")), "Restart the Jupyter kernel", self)
        kernel_button.setStatusTip("Restart the Jupyter kernel")
        kernel_button.triggered.connect(partial(self.start_kernel, False))
        kernel_button.setCheckable(False)
        self._toolbar.addAction(kernel_button)

        # Add a button to the toolbar to start the qtconsole

        qtconsole_button = QAction(QIcon(str(HERE / "icons/command.svg")), "Start Qt Console", self)
        qtconsole_button.setStatusTip("Start the QT Console")
        qtconsole_button.triggered.connect(self.start_qt_console)
        qtconsole_button.setCheckable(False)
        self._toolbar.addAction(qtconsole_button)
        self.kernel_panel = KernelPanel()
        self._toolbar.addWidget(self.kernel_panel)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._kernel:
            self._kernel.shutdown()

    def start_kernel(self, force: bool = False) -> MyKernel:

        # Starting the kernel will need a proper PYTHONPATH for importing the packages

        if force or self._kernel is None:
            self._start_new_kernel()
        else:
            button = QMessageBox.question(
                self,
                "Restart Jupyter kernel", "A kernel is running, should a new kernel be started?"
            )
            if button == QMessageBox.Yes:
                self._console_panel.append('-' * 50)
                self._start_new_kernel()
        return self._kernel

    def _start_new_kernel(self):
        name = self.kernel_panel.selected_kernel
        self._kernel = MyKernel(name)
        self._console_panel.append(f"New kernel '{name}' started...")
        info = self._kernel.get_kernel_info()
        if 'banner' in info['content']:
            self._console_panel.append(info['content']['banner'])

    def start_qt_console(self):
        if self._qt_console is not None and self._qt_console.is_running:
            dialog = QMessageBox.information(self, "Qt Console", "There is already a Qt Console running.")
        else:
            self._qt_console = start_qtconsole(self._kernel or self.start_kernel())

    def run_function(self, func: Callable, args: List, kwargs: Dict, use_kernel: bool):
        if use_kernel:
            # remember kernel setting for this function
            func.__ui_use_kernel__ = True
            self.run_function_in_kernel(func, args, kwargs)
        else:
            self.run_function_in_thread(func, args, kwargs)

    def run_function_in_thread(self, func: Callable, args: List, kwargs: Dict):

        # TODO:
        #  * disable run button (should be activate again in function_complete?)

        self.function_thread = worker = FunctionRunnable(func, args, kwargs)
        self.function_thread.check_for_input(func.__ui_input_request__)
        self.function_thread.start()

        worker.signals.data.connect(self.function_output)
        worker.signals.finished.connect(self.function_complete)
        worker.signals.error.connect(self.function_error)

    def run_function_in_kernel(self, func: Callable, args: List, kwargs: Dict):
        self._kernel = self._kernel or MyKernel()

        self.function_output("-" * 20)

        snippet = create_code_snippet(func, args, kwargs)

        if response := self._kernel.run_snippet(snippet):
            self.function_output(response)

        self.function_complete(func.__name__, True)

    def add_function_button(self, func: Callable):

        button = DynamicButton(func.__name__, func)
        button.mouseReleaseEvent = partial(self.the_button_was_clicked, button)
        # button.clicked.connect(partial(self.the_button_was_clicked, button))

        self._buttons.append(button)
        self._layout_buttons.add_button(button)

    def the_button_was_clicked(self, button: DynamicButton, *args, **kwargs):

        # TODO
        #   * This should be done from the control or model and probably in the background?
        #   * Add ArgumentsPanel in a tabbed widget? When should it be removed from the tabbed widget? ...

        ui_args = get_arguments(button.function)

        args_panel = ArgumentsPanel(button, ui_args)
        args_panel.run_button.clicked.connect(
            lambda checked: self.run_function(args_panel.function, args_panel.args, args_panel.kwargs, args_panel.use_kernel)
        )

        if self._current_args_panel:
            self._layout_panels.replaceWidget(self._current_args_panel, args_panel)
            self._current_args_panel.setParent(None)
        else:
            self._layout_panels.addWidget(args_panel)

        self._current_args_panel = args_panel
        # self.app_frame.adjustSize()
        # self.adjustSize()

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
        text = Text.styled(f"{msg.__class__.__name__}: {msg}", style="bold red")
        self._console_panel.append(msg)
