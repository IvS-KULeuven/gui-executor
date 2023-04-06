from __future__ import annotations

import ast
import contextlib
import errno
import fcntl
import importlib
import inspect
import logging
import os
import queue
import select
import sys
import tempfile
import textwrap
import traceback
from enum import Enum
from functools import partial
from pathlib import Path
from queue import Queue
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import distro as distro
import rich
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QProcess
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
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QIntValidator
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QButtonGroup
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QDialogButtonBox
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
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from executor import ExternalCommand
from executor import ExternalCommandFailed
from rich.console import Console
from rich.markup import escape
from rich.syntax import Syntax
from rich.text import Text

from . import RUNNABLE_APP
from . import RUNNABLE_KERNEL
from . import RUNNABLE_SCRIPT
from .client import MyClient
from .exec import Argument
from .exec import ArgumentKind
from .exec import Directory
from .exec import FileName
from .exec import FilePath
from .exec import StatusType
from .exec import get_arguments
from .gui import IconLabel
from .kernel import MyKernel
from .kernel import start_qtconsole
from .model import Model
from .utils import b64decode
from .utils import capture
from .utils import combo_box_from_enum
from .utils import create_code_snippet
from .utils import create_code_snippet_renderable
from .utils import is_renderable
from .utils import select_directory
from .utils import select_file
from .utils import stringify_args
from .utils import stringify_kwargs
from .utypes import Callback
from .utypes import TypeObject
from .utypes import UQWidget

HERE = Path(__file__).parent.resolve()
DEBUG = False
LOGGER = logging.getLogger('gui-executor.view')


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


class RecurringTaskSignals(QObject):
    """
    Defines the signals available from a running recurring task thread.

    Supported signals are:

        finished
            No data

        error
            tuple (exc_type, value, traceback.format_exc() )

        result
            object data returned from processing, anything

    """
    result = pyqtSignal(object)
    finished = pyqtSignal()
    error = pyqtSignal(tuple)


class RecurringTask(QRunnable):
    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self.signals = RecurringTaskSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self._func(*self._args, **self._kwargs)
        except Exception:
            traceback.print_exc()
            exc_type, value = sys.exc_info()[:2]
            self.signals.error.emit((exc_type, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class FunctionThreadSignals(QObject):
    """
    Defines the signals available from a running function thread.

    Supported signals are:

    finished
        object: the reference for the runnable, i.e. self
        str: the function name
        bool: if the function was successfully executed, i.e. no exception was raised
    error
        str: Exception string
    data
        any object that was returned by the function
    input:
        input request from sub-process
    """

    finished = pyqtSignal(object, str, bool)
    error = pyqtSignal(Exception)
    data = pyqtSignal(object)
    html = pyqtSignal(str)
    png = pyqtSignal(str)
    input = pyqtSignal(str)


class FunctionRunnable(QRunnable):
    def __init__(self, func: Callable, args: List, kwargs: Dict, input_queue: Queue):
        super().__init__()
        self.signals = FunctionThreadSignals()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._check_for_input = False
        self._input_patterns = []
        self._input_queue: Queue = input_queue

    def check_for_input(self, patterns: Tuple):
        if patterns is not None:
            self._check_for_input = True
            self._input_patterns = [pattern.rstrip() for pattern in patterns]

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
            self.signals.finished.emit(self, self._func.__name__, success)

    def start(self):
        QThreadPool.globalInstance().start(self)

    def handle_input_request(self, message: str = None) -> str:
        self.signals.input.emit(message)

        response = self._input_queue.get()
        self._input_queue.task_done()

        return response

    @property
    def func_name(self):
        return self._func.__name__


class FunctionRunnableExternalCommand(FunctionRunnable):
    def __init__(self, func: Callable, args: List, kwargs: Dict, input_queue: Queue):
        super().__init__(func, args, kwargs, input_queue)

    def run(self):
        tmp = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmp.write(create_code_snippet(self._func, self._args, self._kwargs, call_func=True))
        tmp.close()

        self.signals.data.emit(f"----- Starting ExternalCommand running {self.func_name}")

        options = dict(capture=True, capture_stderr=True, asynchronous=True, buffered=False, input=True)
        try:
            # We could actually just use SubProcess here to with the correct settings
            with ExternalCommand(f"{sys.executable} {tmp.name}", **options) as cmd:
                self.make_async(cmd.stdout)
                self.make_async(cmd.stderr)

                while True:
                    # Wait for data to become available
                    out, *_ = select.select([cmd.stdout, cmd.stderr], [], [])

                    # Try reading some data from each
                    line_out = self.read_async(cmd.stdout)
                    line_err = self.read_async(cmd.stderr)

                    if line_out:
                        self.signals.data.emit(line := line_out.decode(cmd.encoding).rstrip())
                        # print(f"{line = }")
                        # Try to detect when the process is requesting input.
                        # TODO: request input from user through QLineEdit field...
                        if self._check_for_input and any(pattern in line for pattern in self._input_patterns):
                            response = self.handle_input_request(line_out.decode())
                            cmd.subprocess.stdin.write(bytes(f'{response}\n'.encode()))
                    if line_err:
                        self.signals.data.emit(line := line_err.decode(cmd.encoding).rstrip())

                    if cmd.subprocess.poll() is not None:
                        break

            cmd.wait()

        except ExternalCommandFailed as exc:
            # self._console_panel.append(cmd.error_message)
            # This error message is also available in the decoded_stderr.
            self.signals.error.emit(exc)
        finally:
            # print(f"{tmp.name = }")
            os.unlink(tmp.name)

        # if out := cmd.decoded_stdout:
        #     self._console_panel.append(out)
        if err := cmd.decoded_stderr:
            self.signals.data.emit(err)

        if cmd.is_finished:
            if cmd.failed:
                self.signals.finished.emit(self, self._func.__name__, False)
            else:
                self.signals.finished.emit(self, self._func.__name__, True)
        else:
            self.signals.error.emit(RuntimeError(f"Command {self._func.__name__} should have been finished!"))

    @staticmethod
    def make_async(fd):
        # Helper function to add the O_NONBLOCK flag to a file descriptor
        fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)

    @staticmethod
    def read_async(fd) -> bytes:
        # Helper function to read some data from a file descriptor, ignoring EAGAIN errors
        try:
            return fd.read()
        except IOError as exc:
            if exc.errno != errno.EAGAIN:
                raise exc
            else:
                return b''


class FunctionRunnableKernel(FunctionRunnable):
    def __init__(self, kernel: MyKernel, func: Callable, args: List, kwargs: Dict, input_queue: Queue):
        super().__init__(func, args, kwargs, input_queue)
        self.kernel: MyKernel = kernel
        self.startup_timeout = 60  # seconds
        self.console = Console(record=True, width=120)
        self.running = False

    def is_running(self):
        return self.running

    def run(self):

        self.running = True

        self.signals.data.emit(f"----- Running script '{self.func_name}' in kernel")

        snippet = create_code_snippet(self._func, self._args, self._kwargs)

        self.signals.data.emit("The code snippet:")
        self.signals.data.emit(create_code_snippet_renderable(self._func, self._args, self._kwargs))
        self.signals.data.emit("")

        client = MyClient(self.kernel, startup_timeout=self.startup_timeout)
        try:
            client.connect()
        except RuntimeError as exc:
            self.signals.error.emit(exc)
            return

        msg_id = client.execute(snippet, allow_stdin=True)

        DEBUG and LOGGER.debug(f"{id(client)}: {msg_id = }")

        while True:
            try:
                io_msg = client.get_iopub_msg(msg_id, timeout=1.0)

                if io_msg['parent_header']['msg_id'] != msg_id:
                    DEBUG and LOGGER.debug(f"{id(client)}: Skipping {io_msg = }")
                    continue

                io_msg_type = io_msg['msg_type']
                io_msg_content = io_msg['content']

                DEBUG and LOGGER.debug(f"{id(client)}: {io_msg = }")

                if io_msg_type == 'stream':
                    if 'text' in io_msg_content:
                        text = io_msg_content['text'].rstrip()
                        self.signals.data.emit(text)
                elif io_msg_type == 'status':
                    if io_msg_content['execution_state'] == 'idle':
                        # self.signals.data.emit("Execution State is Idle, terminating...")
                        DEBUG and LOGGER.debug(f"{id(client)}: Execution State is Idle, terminating...")
                        self.collect_response_payload(client, msg_id, timeout=1.0)
                        break
                    elif io_msg_content['execution_state'] == 'busy':
                        # self.signals.data.emit("Execution State is busy...")
                        DEBUG and LOGGER.debug(f"{id(client)}: Execution State is busy...")
                        continue
                    elif io_msg_content['execution_state'] == 'starting':
                        # self.signals.data.emit("Execution State is starting...")
                        DEBUG and LOGGER.debug(f"{id(client)}: Execution State is starting...")
                        continue
                elif io_msg_type == 'display_data':
                    if 'data' in io_msg_content:
                        if 'text/html' in io_msg_content['data']:
                            text = io_msg_content['data']['text/html'].rstrip()
                            self.signals.html.emit(text)
                        elif 'image/png' in io_msg_content['data']:
                            data = io_msg_content['data']['image/png']
                            self.signals.png.emit(data)
                        elif 'text/plain' in io_msg_content['data']:
                            text = io_msg_content['data']['text/plain'].rstrip()
                            self.signals.data.emit(text)
                elif io_msg_type == 'execute_input':
                    ...  # ignore this message type
                    #     self.signals.data.emit("The code snippet:")
                    #     source_code = io_msg_content['code']
                    #     syntax = Syntax(source_code, "python", theme='default')
                    #     self.signals.data.emit(syntax)
                elif io_msg_type == 'error':
                    if 'traceback' in io_msg_content:
                        traceback = io_msg_content['traceback']
                        self.signals.data.emit(Text.from_ansi('\n'.join(traceback)))
                else:
                    self.signals.error.emit(RuntimeError(f"Unknown io_msg_type: {io_msg_type}"))

            except queue.Empty:
                DEBUG and LOGGER.debug(f"{id(client)}: Catching on empty queue -----------")
                # We fall through here when no output is received from the kernel. This can mean that the kernel
                # is waiting for input and therefore this is a good opportunity to check for stdin messages.
                with contextlib.suppress(queue.Empty):
                    in_msg = client.get_stdin_msg(timeout=0.1)

                    DEBUG and LOGGER.debug(f"{id(client)}: {in_msg = }")

                    if in_msg['msg_type'] == 'input_request':
                        prompt = in_msg['content']['prompt']
                        response = self.handle_input_request(prompt)
                        client.input(response)
            except Exception as exc:
                # We come here after a kernel interrupt that leads to incomplete
                LOGGER.error(f"{id(client)}: Caught Exception: {exc}", exc_info=True)
                self.signals.data.emit(exc)

        client.disconnect()
        self.running = False
        self.signals.finished.emit(self, self.func_name, True)

    def handle_input_request(self, prompt: str = None) -> str:
        """
        This function is called when a stdin message is received from the kernel.

        Args:
            prompt: the text that was given as a prompt to the user

        Returns:
            A string that will be sent to the kernel as a reply.
        """
        if prompt:
            if self._check_for_input and all(pattern not in prompt for pattern in self._input_patterns):
                self.signals.data.emit(
                    textwrap.dedent(
                        f"""\
                        [red][bold]ERROR: [/]The input request prompt message doesn't match any of the expected prompt messages.[/]
                        [default]→ input prompt='{escape(prompt)}'[/]
                        [default]→ expected=({", ".join(f"'{escape(x)}'" for x in self._input_patterns)})[/]
                        
                        [blue]Ask the developer of the task to match up the input request patterns and the prompt.[/]
                        """
                    )
                )

            self.signals.data.emit(escape(prompt))
            self.signals.input.emit(prompt)

            response = self._input_queue.get()
            self._input_queue.task_done()
            return response
        else:
            # The input() function had no prompt argument
            self.signals.data.emit(
                textwrap.dedent(
                    f"""\
                    [red][bold]ERROR: [/]No prompt was given to the input request function.[/]
                    An input request was detected from the Jupyter kernel, but no message was given to describe the 
                    request. Ask the developer of the task to pass a proper message to the input request.
                    
                    [blue]An empty string will be returned to the kernel.[/]
                    """
                )
            )
            return ''

    def collect_response_payload(self, client, msg_id, timeout: float):
        try:
            shell_msg = client.get_shell_msg(msg_id, timeout=timeout)
        except queue.Empty:
            DEBUG and LOGGER.debug(f"{id(client)}: No shell message available for {timeout}s....")
            self.signals.data.emit(
                "[red]No result received from kernel, this might happen when kernel is interrupted.[/]")
            return

        msg_type = shell_msg["msg_type"]
        msg_content = shell_msg["content"]

        DEBUG and LOGGER.debug(f"{id(client)}: {shell_msg = }")

        if msg_type == "execute_reply":
            status = msg_content['status']
            if status == 'error' and 'traceback' in msg_content:
                # We are not sending this traceback anymore to the Console output
                # as it was already handled in the context of the io_pub_msg.
                self.signals.data.emit(f"{status = }")
                traceback = msg_content['traceback']
                self.signals.data.emit(Text.from_ansi('\n'.join(traceback)))


class FunctionRunnableQProcess(FunctionRunnable):
    def __init__(self, func: Callable, args: List, kwargs: Dict, input_queue: Queue):
        super().__init__(func, args, kwargs, input_queue)

        self._process = None

    def run(self):
        tmp = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmp.write(create_code_snippet(self._func, self._args, self._kwargs, call_func=False))
        tmp.close()

        self.signals.data.emit("----- Starting QProcess running script_app")

        try:
            self._process = QProcess()
            self._process.readyReadStandardOutput.connect(self.handle_stdout)
            self._process.readyReadStandardError.connect(self.handle_stderr)
            # use this if you want to monitor the Process progress
            # self._process.stateChanged.connect(self.handle_state)
            self._process.finished.connect(self.process_finished)
            self._process.start(f"{sys.executable}", [f"{HERE/'script_app.py'}", "--script", f"{tmp.name}"])

            # waitForFinished() has a 30s timeout by default. Use -1 to disable the timeout, otherwise the result
            # will be a: QProcess: Destroyed while process ("...venv/bin/python") is still running. .. after 30 seconds.
            self._process.waitForFinished(-1)

        except Exception as exc:
            self.signals.error.emit(exc)
        finally:
            self.signals.finished.emit(self, self._func.__name__, True)
            # print(f"{tmp.name = }")
            os.unlink(tmp.name)

    def handle_stdout(self):
        data = self._process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.signals.data.emit(stdout)

        if self._check_for_input and any(pattern in stdout for pattern in self._input_patterns):
            response = self.handle_input_request(stdout)
            self._process.write(bytes(f'{response}\n'.encode()))

    def handle_stderr(self):
        data = self._process.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        self.signals.data.emit(stderr)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        self.signals.data.emit(f"State changed: {state_name}")

    def process_finished(self):
        self._process = None


class ConsoleOutput(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)
        # self.insertPlainText("")
        # self.insertHtml("<br>")
        self.setAcceptRichText(True)
        self.setUndoRedoEnabled(False)
        self.document().setDocumentMargin(4.0)  # this is also the default
        self.setMinimumSize(600, 100)
        monospaced_font = QFont("Courier New")
        monospaced_font.setStyleHint(QFont.Monospace)
        monospaced_font.setPointSize(12)  # TODO: should be a setting
        self.setFont(monospaced_font)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__contextMenu)

    @pyqtSlot(str)
    def append(self, text):

        # import builtins
        # builtins.print(f"{text = }")

        console = Console(record=True)

        with console.capture() as cap:
            console.print(text)

        # builtins.print(f"{cap.get() = }")

        exported_html = console.export_html(
            inline_styles=True,
            # code_format="<pre style=\"font-family:'Courier New',Menlo,'DejaVu Sans Mono'\">\n{code}\n</pre>",
            # code_format="<pre style=\"font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace\">{code}</pre>",
            # code_format="<code><pre style=\"font-family:Menlo,\'DejaVu Sans Mono\',consolas,\'Courier New\',monospace\">{code}\n</pre>\n</code>\n",
            code_format="<pre>{code}</pre>",
        )

        self.append_html(exported_html)

    @pyqtSlot(str)
    def append_html(self, text):

        # import builtins
        # builtins.print(f"{text = }")

        self.setUpdatesEnabled(False)
        self.moveCursor(QTextCursor.End)
        self.insertHtml(text)
        self.insertHtml("<br>")
        self.moveCursor(QTextCursor.End)
        self.setUpdatesEnabled(True)

        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())

    def __contextMenu(self):
        self._normalMenu = self.createStandardContextMenu()
        self._addCustomMenuItems(self._normalMenu)
        self._normalMenu.exec_(QCursor.pos())

    def _addCustomMenuItems(self, menu):
        menu.addSeparator()
        menu.addAction(u'Clear', self.clear)


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
        syntax = Syntax(source_code, "python", theme='default', line_numbers=True)

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

    icon_size = QSize(30, 30)
    horizontal_spacing = 2

    def __init__(self, label: str, func: Callable,
                 icon_path: Path | str = None,
                 icon_selected_path: Path | str = None,
                 final_stretch=True,
                 icon_size: QSize = icon_size):
        super().__init__()
        self.source_code_window = None
        self._function = func
        self._label = label
        self._icon = None

        # Icons defined by the function itself take precedence, then the
        # arguments passed as icon_path, and finally a default icon is used.

        try:
            self.icon_path = self._function.__ui_icons__[0]
            self.icon_selected_path = self._function.__ui_icons__[1]
        except (AttributeError, IndexError, TypeError, ValueError):
            self.icon_path = str(icon_path or HERE / "icons/script-function.svg")
            self.icon_selected_path = str(icon_selected_path or HERE / "icons/script-function-selected.svg")

        if not Path(self.icon_path).exists() or not Path(self.icon_selected_path).exists():
            raise ValueError(f"Invalid path given for icons for function '{self._function.__name__}'")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.label_icon = IconLabel(icon_path=self.icon_path, size=icon_size)
        label_text = QLabel(self.function_display_name)
        if self._function.__ui_immediate_run__:
            # This style will draw a 2 pixel horizontal line under the label
            label_text.setStyleSheet(textwrap.dedent(
                """\
                    padding: 0px; 
                    border-bottom-width: 0px;  /* set to 1 or 2 if you need a bottom line */
                    border-bottom-style: solid; 
                    border-bottom-color: blue;
                    border-radius: 0px;
                    color: blue;
                """)
            )

        layout.addWidget(self.label_icon)
        layout.addSpacing(self.horizontal_spacing)
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

    def select(self):
        self.label_icon.set_icon_path(self.icon_selected_path)
        self.label_icon.repaint()

    def deselect(self):
        self.label_icon.set_icon_path(self.icon_path)
        self.label_icon.repaint()

    @property
    def function(self) -> Callable:
        return self._function

    @property
    def module_name(self) -> str:
        """Returns the name of the module where the function resides."""
        return self._function.__ui_module__

    @property
    def module_display_name(self) -> str:
        try:
            try:
                # This attribute is given to the function when copying the function object
                # to be used in a different TAB with another display name
                return self._function.__ui_module_display_name__
            except AttributeError:
                return sys.modules[self._function.__ui_module__].UI_MODULE_DISPLAY_NAME
        except (AttributeError, KeyError):
            return self.module_name.rsplit(".", 1)[-1]

    @property
    def function_display_name(self) -> str:
        name = self._function.__ui_display_name__ or self.label or self._function.__name__

        # The following line will put the display_name within triangles: ▶︎ name ◀︎
        # when the immediate_run flag is True
        # name = f"\u25B6 {name} \u25C0" if self._function.__ui_immediate_run__ else name

        return name

    @property
    def label(self) -> str:
        return self._label

    def immediate_run(self):
        return self.function.__ui_immediate_run__

    def __repr__(self):
        return f"DynamicButton(\"{self.label}\", {self.function})"


class TextInputField(QLineEdit):
    def __init__(self, name: str, default: Any, placeholder_text: str = None):
        super().__init__()
        self._name = name
        DEBUG and LOGGER.debug(f"{default = }, {type(default)=}")
        self._default = None if default is None else str(default)
        self._placeholder_text = placeholder_text
        self.setObjectName(name)
        self.setPlaceholderText(self._placeholder_text or self._default)

        if default is None:
            return

        # Create a context menu entry to set the default value

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__contextMenu)

        # Use the copy icon to set the default value in the text field

        icon = QApplication.instance().style().standardIcon(QtWidgets.QStyle.SP_TitleBarNormalButton)
        action = self.addAction(icon, self.TrailingPosition)
        action.triggered.connect(self.set_default)
        action.setToolTip("Set the default value.")

    def __contextMenu(self):
        self._normalMenu = self.createStandardContextMenu()
        self._addCustomMenuItems(self._normalMenu)
        self._normalMenu.exec_(QCursor.pos())

    def _addCustomMenuItems(self, menu):
        menu.addSeparator()
        menu.addAction(u'Set default', self.set_default)

    def set_default(self):
        self.setText(self._default)


class ArgumentsPanel(QScrollArea):
    def __init__(self, button: DynamicButton, ui_args: Dict[str, Argument]):
        super().__init__()

        self.setWidgetResizable(True)

        widget = QWidget()

        widget.setStyleSheet(textwrap.dedent(
            """
                QGroupBox {
                    font-size: 16px;
                    font-weight: light;
                    color: grey;
                    /* margin-top: 25px; */
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 10px;
                    /* padding-top: 5px; */
                    /* padding-bottom: 0px */
                }
            """)
        )
        widget.setContentsMargins(0, 5, 0, 0)

        main_layout = QHBoxLayout()

        self.group_box = QGroupBox(f"arguments for '{button.function_display_name}'")

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
            elif isinstance(arg.annotation, (TypeObject, Callback)):
                input_field: QWidget = arg.annotation.get_widget()
            elif inspect.isclass(arg.annotation) and issubclass(arg.annotation, Enum):
                input_field: QComboBox = combo_box_from_enum(arg.annotation)
                if arg.default is not None:
                    input_field.setCurrentText(arg.default.name)
            else:
                input_field: TextInputField = TextInputField(name=name, default=arg.default)
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

            if arg.annotation is Directory:
                folder_button = IconLabel(icon_path=HERE / "icons/folder.svg", size=QSize(20, 20))
                folder_button.mousePressEvent = partial(self.select_folder, input_field)
            elif arg.annotation is FileName:
                folder_button = IconLabel(icon_path=HERE / "icons/filename.svg", size=QSize(20, 20))
                folder_button.mousePressEvent = partial(self.select_file, input_field, full_path=False)
            elif arg.annotation in (Path, FilePath):
                folder_button = IconLabel(icon_path=HERE / "icons/filepath.svg", size=QSize(20, 20))
                folder_button.mousePressEvent = partial(self.select_file, input_field, full_path=True)
            else:
                folder_button = None

            # label.setStyleSheet("border:1px solid #111111; ")
            # input_field.setStyleSheet("border:1px solid #111111; ")
            # type_hint.setStyleSheet("border:1px solid #111111; ")

            # Stretch the middle column of the grid. That is needed when there is only one argument and it's a bool
            # i.e. a CheckBox. If we do not stretch, the checkbox will be centered.
            grid.setColumnStretch(1, 1)
            grid.addWidget(label, idx, 0, alignment=Qt.AlignVCenter)
            grid.addWidget(input_field, idx, 1, alignment=Qt.AlignVCenter)
            if folder_button is not None:
                grid.addWidget(folder_button, idx, 2)
            else:
                grid.addWidget(type_hint, idx, 2, alignment=Qt.AlignVCenter)

        vbox.addLayout(grid)

        hbox = QHBoxLayout()
        button_group = QButtonGroup()

        self.kernel_rb = QRadioButton("Run in kernel")
        self.kernel_rb.clicked.connect(partial(self.runnable_clicked, RUNNABLE_KERNEL))
        self.kernel_rb.setChecked(self.function.__ui_runnable__ == RUNNABLE_KERNEL)

        self.app_rb = QRadioButton("Run in GUI App")
        self.kernel_rb.clicked.connect(partial(self.runnable_clicked, RUNNABLE_APP))
        self.app_rb.setChecked(self.function.__ui_runnable__ == RUNNABLE_APP)

        self.script_rb = QRadioButton("Run as script")
        self.kernel_rb.clicked.connect(partial(self.runnable_clicked, RUNNABLE_SCRIPT))
        self.script_rb.setChecked(self.function.__ui_runnable__ == RUNNABLE_SCRIPT)

        button_group.addButton(self.kernel_rb, RUNNABLE_KERNEL)
        button_group.addButton(self.app_rb, RUNNABLE_APP)
        button_group.addButton(self.script_rb, RUNNABLE_SCRIPT)

        self.run_button = QPushButton("run")
        self.close_button = QPushButton("close")
        hbox.addWidget(self.kernel_rb)
        hbox.addWidget(self.app_rb)
        hbox.addWidget(self.script_rb)
        hbox.addStretch()
        hbox.addWidget(self.close_button)
        hbox.addWidget(self.run_button)

        vbox.addStretch()
        vbox.addLayout(hbox)

        self.group_box.setLayout(vbox)
        # self.group_box.setStyleSheet("background-color: #5fd7ff; margin:0px; border:1px solid #0000d7; ")  # for debugging

        main_layout.addWidget(self.group_box)
        widget.setLayout(main_layout)
        self.setWidget(widget)

        # self.setStyleSheet("border:1px solid rgb(0, 0, 0); ")

    @staticmethod
    def select_folder(input_field: QLineEdit, *args):

        input_dir = input_field.displayText() or input_field.placeholderText()
        if dir_name := select_directory(directory=input_dir):
            input_field.setText(dir_name)

    @staticmethod
    def select_file(input_field: QLineEdit, *args, full_path: bool = True):

        input_file = input_field.displayText() or input_field.placeholderText()
        if filename := select_file(filename=input_file):
            filename = filename if full_path else Path(filename).name
            input_field.setText(filename)

    def runnable_clicked(self, runnable: int):
        self.function.__ui_runnable__ = runnable

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
    def runnable(self):
        if self.kernel_rb.isChecked():
            return RUNNABLE_KERNEL
        elif self.app_rb.isChecked():
            return RUNNABLE_APP
        elif self.script_rb.isChecked():
            return RUNNABLE_SCRIPT
        else:
            # If non is selected, automatically select plain script
            self.script_rb.setChecked(True)
            return RUNNABLE_SCRIPT

    def _cast_arg(self, name: str, field: QLineEdit | QCheckBox | QComboBox | UQWidget):
        arg = self._ui_args[name]

        if arg.annotation is bool:
            return field.checkState() == Qt.Checked
        elif isinstance(arg.annotation, TypeObject):
            return field.get_value()
        elif inspect.isclass(arg.annotation) and issubclass(arg.annotation, Enum):
            return arg.annotation[field.currentText()]
        else:

            if not (value := field.displayText() or field.placeholderText()):
                return None
            try:
                if arg.annotation is tuple or arg.annotation is list:
                    return ast.literal_eval(value) if value else arg.annotation()
                elif arg.annotation in (Path, Directory, FileName, FilePath):
                    return Path(value)
                return arg.annotation(value)
            except (ValueError, TypeError, SyntaxError):
                return value


class FunctionButtonsPanel(QScrollArea):
    def __init__(self):
        super().__init__()

        self.setWidgetResizable(True)
        self.setMinimumSize(600, 100)

        widget = QWidget()

        widget.setStyleSheet(textwrap.dedent(
            """
                QGroupBox {
                    font-size: 16px;
                    font-weight: light;
                    color: grey;
                    /* margin-top: 25px; */
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 10px;
                    /* padding-top: 5px; */
                    /* padding-bottom: 0px */
                }
            """)
        )

        self.n_cols = 4  # This must be a setting or configuration option

        # The modules are arranged in a vertical layout and each of the functions in that module is arranged in a
        # horizontal layout. Modules are added when a new button is added for a not yet existing module.

        self.modules: Dict[str, QGridLayout] = {}
        self.buttons: Dict[str, int] = {}
        self.module_layout = QVBoxLayout()
        self.module_layout.setSpacing(10 if distro.id().lower() == 'ubuntu' else 25)
        self.module_layout.addStretch(1)

        widget.setLayout(self.module_layout)

        self.setWidget(widget)

    def add_button(self, button: DynamicButton):
        module_name = button.module_display_name
        if module_name not in self.modules:
            grid = QGridLayout()
            # Make sure all columns have equal width
            for idx in range(self.n_cols):
                grid.setColumnStretch(idx, 1)
            gbox = QGroupBox(module_name)
            gbox.setLayout(grid)
            gbox.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
            # self.module_layout.addWidget(gbox)
            self.module_layout.insertWidget(self.module_layout.count()-1, gbox)
            self.modules[module_name] = grid
            self.buttons[module_name] = 0

        self.buttons[module_name] += 1
        button_count = self.buttons[module_name]

        row = (button_count - 1) // self.n_cols
        col = (button_count - 1) % self.n_cols
        self.modules[module_name].addWidget(button, row, col)


class KernelPanel(QWidget):
    def __init__(self, name: str = "python3"):
        super().__init__()

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)

        kernel_specs = list(MyKernel.get_kernel_specs())
        try:
            idx = kernel_specs.index(name)
        except ValueError:
            idx = kernel_specs.index("python3")
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
    def __init__(self, model: Model, app_name: str = None, cmd_log: str = None, verbosity: int = 0, kernel_name: str = "python3"):
        super().__init__()

        self._model = model

        self._qt_console: Optional[ExternalCommand] = None

        self._kernel: Optional[MyKernel] = None
        """The Jupyter kernel we are running, can be None, created using start_kernel(). """

        self.input_queue: Queue = Queue()
        self.previous_selected_button: Optional[DynamicButton] = None
        self.verbosity = verbosity

        self.kernel_name = kernel_name
        """The name of the kernel that shall be started, defaults to 'python3'."""

        self.cmd_log = cmd_log
        """The location of the command log files, provided as an argument."""

        self.question_dialog: YesNoQuestion | None = None
        """A half-modal dialog to answer questions from the runnable."""

        # Keep a record of the GUI Apps, because if their reference is garbage collected they will crash

        self._gui_apps = []
        self._recurring_tasks = []

        self.setWindowTitle(app_name or "GUI Executor")

        desktop_widget = QApplication.desktop()
        desktop_screen = desktop_widget.screenNumber(self)
        desktop_geometry = desktop_widget.availableGeometry(screen=desktop_screen)
        LOGGER.debug(f"{desktop_screen = }, {desktop_geometry = }")

        # Not sure anymore why I put this line in, but it restricts the size of the main window to the size of the
        # main desktop screen, which might be smaller than e.g. an external screens that is attached.
        # self.setMaximumSize(desktop_geometry.width(), desktop_geometry.height())

        self.setGeometry(300, 300, 600, 800)

        # The main frame in which all the other frames are located, the outer Application frame

        self.app_frame = QFrame()
        self.app_frame.setObjectName("AppFrame")
        self.app_frame.setMinimumSize(600, 0)  # TODO: should be a setting

        # We don't want this QFrame to shrink below 500 pixels, therefore set a minimum horizontal size
        # and set the policy such that it can still expand from this minimum size. This will be used
        # when we use adjustSize after replacing the arguments panel.

        self.app_frame.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)

        vbox = QVBoxLayout()

        self._splitter = QSplitter(Qt.Vertical)
        self._splitter.setChildrenCollapsible(False)

        self._buttons_panels = self.create_button_panels()

        self._args_panel: QWidget = None
        self._console_panel = ConsoleOutput()

        if len(self._buttons_panels) == 1:
            # If there is only one buttons panel, we do not create a TabWidget, but use that panel directly.
            # We do not know the name (key) that was given in the returned dict, so we take the first item.
            self._buttons_widget = list(self._buttons_panels.values())[0]
        else:
            self._buttons_widget = QTabWidget()
            for name, widget in self._buttons_panels.items():
                self._buttons_widget.addTab(widget, name)
            self._buttons_widget.setCurrentIndex(0)
            self._buttons_widget.currentChanged.connect(self.close_args_panel)

        self._splitter.addWidget(self._buttons_widget)
        # we do not yet add the args_panel -> see 'the_button_was_clicked()'
        self._splitter.addWidget(self._console_panel)

        self._splitter.setSizes([300, 120, 300])

        vbox.addWidget(self._splitter)

        self.app_frame.setLayout(vbox)

        self.setCentralWidget(self.app_frame)

        QTimer.singleShot(500, self.start_kernel)

        self._rich_console = Console(force_terminal=False, force_jupyter=False)

        self._toolbar = QToolBar()
        self._toolbar.setIconSize(QSize(40, 40))
        self.addToolBar(self._toolbar)

        self._status_bar_fixed_widget = QLabel("")
        self._status_bar = self.statusBar()
        self._status_bar.addPermanentWidget(self._status_bar_fixed_widget)

        # Add a button to the toolbar to restart the kernel

        kernel_button = QAction(QIcon(str(HERE / "icons/reload-kernel.svg")), "Restart the Jupyter kernel", self)
        kernel_button.setStatusTip("Restart the Jupyter kernel")
        kernel_button.triggered.connect(partial(self.start_kernel, False))
        kernel_button.setCheckable(False)
        self._toolbar.addAction(kernel_button)

        # Add a button to the toolbar to start the qtconsole

        qtconsole_button = QAction(QIcon(str(HERE / "icons/command.svg")), "Start Python Console", self)
        qtconsole_button.setStatusTip("Start the QT Console")
        qtconsole_button.triggered.connect(self.start_qt_console)
        qtconsole_button.setCheckable(False)
        self._toolbar.addAction(qtconsole_button)

        # Add a button to the toolbar to interrupt the kernel

        interrupt_button = QAction(QIcon(str(HERE / "icons/traffic-light-red.svg")), "Interrupt the Jupyter Kernel", self)
        interrupt_button.setStatusTip("Interrupt the Jupyter Kernel")
        interrupt_button.triggered.connect(self.interrupt_kernel)
        interrupt_button.setCheckable(False)
        self._toolbar.addAction(interrupt_button)

        self.kernel_panel = KernelPanel(self.kernel_name)
        self._toolbar.addWidget(self.kernel_panel)

        self.threadpool = QThreadPool()
        # print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self._timer = QTimer()
        self._timer.setInterval(1000)  # This interval shall be in the settings
        self._timer.timeout.connect(self.run_recurring_tasks)
        self._timer.start()

    def closeEvent(self, event: QCloseEvent) -> None:

        question = QMessageBox()
        question.setIcon(QMessageBox.Warning)
        question.setWindowTitle("Closing GUI and Kernel?")
        close_button = question.addButton("Close GUI and Kernel", QMessageBox.YesRole)
        cancel_button = question.addButton("Cancel", QMessageBox.NoRole)
        cancel_button.setDefault(True)
        cancel_button.setAutoDefault(True)
        question.setText("You are about to close the Task GUI and kill the running kernel.")
        question.setInformativeText("This will permanently delete all data in the Jupyter kernel.")

        question.exec()
        button_pressed = question.clickedButton()
        if button_pressed == cancel_button:
            event.ignore()
            return

        if self._kernel:
            print("Shutting down Jupyter kernel.")
            self._kernel.shutdown()

        event.accept()

        print("Waiting for recurring tasks to end.", end='', flush=True)
        while not self.threadpool.waitForDone(100):
            print(".", end='', flush=True)
        print(flush=True)

    def start_recurring_task(self, task: Callable):
        # Pass the function to execute
        worker = RecurringTask(task)  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(partial(self.update_status, task))
        worker.signals.finished.connect(self.end_recurring_task)

        # Execute
        self.threadpool.start(worker)

    def end_recurring_task(self):
        pass

    def run_recurring_tasks(self):
        for func in self._recurring_tasks:
            self.start_recurring_task(func)

    def update_status(self, func: Callable, msg: str):
        if func.__ui_status_type__ == StatusType.NORMAL:
            self._status_bar.showMessage(msg)
        else:
            self._status_bar_fixed_widget.setText(msg)

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

        if self._kernel is not None:
            self._kernel.shutdown()

        name = self.kernel_panel.selected_kernel
        LOGGER.info(f"Starting new kernel {name}...")
        self._kernel = MyKernel(name)
        self._console_panel.append(f"New kernel '{name}' started...")

        with MyClient(self._kernel) as client:

            info = client.get_kernel_info()
            if 'banner' in info:
                self._console_panel.append(info['banner'])

            # make sure the user doesn't by accident quit the kernel
            client.run_snippet("del quit, exit")

            # If there is a startup script, run it now
            try:
                startup = os.environ["PYTHONSTARTUP"]
                self._console_panel.append(f"Loading Python startup file from {startup}.")
                client.run_snippet(
                    textwrap.dedent("""\
                        import os
                        import runpy
                        
                        try:
                            startup = os.environ["PYTHONSTARTUP"]
                            runpy.run_path(path_name=startup)
                        except KeyError:
                            raise Warning("Couldn't load startup script, PYTHONSTARTUP not defined.")
                        """
                    )
                )
            except KeyError:
                self._console_panel.append("Couldn't load startup script, PYTHONSTARTUP not defined.")

            if self.cmd_log:
                self._console_panel.append(
                    f"Loading [blue]gui_executor.transforms[/] extension...log file in '{self.cmd_log}'")
                client.run_snippet(
                    textwrap.dedent(
                        f"""\
                        from gui_executor import transforms
                        transforms.set_log_file_location("{self.cmd_log}")
                        %load_ext gui_executor.transforms
                        """
                    )
                )

    def interrupt_kernel(self):
        self._kernel.interrupt_kernel()
        for runnable in self._gui_apps:
            LOGGER.warning(
                f"Function {runnable.func_name} from the list of threads is "
                f"{'STILL' if runnable.is_running() else 'NOT'} running."
            )
        # self._gui_apps.clear()


    def start_qt_console(self):
        if self._qt_console is not None and self._qt_console.is_running:
            dialog = QMessageBox.information(self, "Qt Console", "There is already a Qt Console running.")
        else:
            self._qt_console = start_qtconsole(self._kernel or self.start_kernel(), verbosity=self.verbosity)

    def run_function(self, func: Callable, args: List, kwargs: Dict, runnable_type: int):

        # TODO:
        #  * disable run button (should be activate again in function_complete?)

        runnable = {
            RUNNABLE_KERNEL: partial(FunctionRunnableKernel, self._kernel),
            RUNNABLE_APP: FunctionRunnableQProcess,
            RUNNABLE_SCRIPT: FunctionRunnableExternalCommand,
        }

        worker = runnable[runnable_type](func, args, kwargs, self.input_queue)
        worker.check_for_input(func.__ui_input_request__)
        worker.start()

        worker.signals.data.connect(self.function_output)
        worker.signals.html.connect(self.function_output_html)
        worker.signals.png.connect(self.function_output_png)
        worker.signals.finished.connect(self.function_complete)
        worker.signals.error.connect(self.function_error)
        worker.signals.input.connect(self.input_request)

        DEBUG and self._console_panel.append(f"[blue]Added '{worker.func_name}' to list of runnable threads.[/blue]")
        self._gui_apps.append(worker)

    def run_function_in_kernel(self, func: Callable, args: List, kwargs: Dict):
        self._kernel = self._kernel or MyKernel()

        self.function_output("-" * 20)

        snippet = create_code_snippet(func, args, kwargs)

        if response := self._kernel.run_snippet(snippet):
            self.function_output(response)

        self.function_complete(func.__name__, True)

    def create_button_panels(self) -> Dict:
        module_path_list: List = self._model.module_path_list

        buttons_panels = {}

        for module_path in module_path_list:
            mod = importlib.import_module(module_path)
            tab_order: List = getattr(mod, "UI_TAB_ORDER", None)

            # If we do not have sub packages, we will not create tabs, and we also only need one
            # FunctionButtonsPanel which will be called "Main".

            panel = FunctionButtonsPanel()
            if self.add_buttons_to_panel(panel, module_path=module_path):
                tab_name = getattr(mod, "UI_TAB_DISPLAY_NAME", "Main")
                buttons_panels[tab_name] = panel

            if subpackages := self._model.get_ui_subpackages(module_path_list=[module_path]):
                if tab_order is None:
                    # Here we sort in display_name
                    sorted_subpackages = sorted(subpackages.items(), key=lambda x: x[1][0])
                else:
                    # sorted_subpackages = sorted(subpackages.items(), key=lambda x: tab_order.index(x[0]))
                    # This way seems to be faster: see https://stackoverflow.com/a/21773891/4609203
                    sorted_subpackages = [(name, subpackages[name]) for name in tab_order if name in subpackages]
                for name, (display_name, _) in sorted_subpackages:
                    panel = FunctionButtonsPanel()
                    self.add_buttons_to_panel(panel, module_path=f"{module_path}.{name}")
                    buttons_panels[display_name] = panel

        return buttons_panels

    def add_buttons_to_panel(self, panel: FunctionButtonsPanel, module_path: str = None) -> int:
        """

        Args:
            panel:
            module_path:

        Returns:
            The number of buttons added.
        """
        modules = self._model.get_ui_modules(module_path_list=[module_path])
        number_of_buttons = 0

        for _, mod in sorted(modules.values()):
            try:
                funcs = self._model.get_ui_buttons_functions(mod)

                # Our functions are all decorated functions, decorated with the @exec_ui or @exec_task.
                # Since we have used functools.wraps(), all our functions have the attribute __wrapped__
                # which points to the original function. What we need is the first line of the function
                # in the module file, because we want the functions to be sorted in the order they appear
                # in the source code file and not alphabetically.

                for name, func in sorted(funcs.items(), key=lambda x: x[1].__wrapped__.__code__.co_firstlineno):
                    # print(f"{func.__name__} -> {func.__wrapped__.__code__.co_firstlineno = }")
                    button = DynamicButton(func.__name__, func)
                    button.mousePressEvent = partial(self.the_button_was_pressed, button, panel)
                    # button.mouseDoubleClickEvent = self.the_button_was_double_clicked

                    panel.add_button(button)
                    number_of_buttons += 1

                recurring_funcs = self._model.get_ui_recurring_functions(mod)

                for name, func in sorted(recurring_funcs.items(), key=lambda x: x[1].__wrapped__.__code__.co_firstlineno):
                    self.add_recurring_function(func)

            except ModuleNotFoundError as exc:
                rich.print(f"[red]{exc.__class__.__name__}: {exc}[/]")
                rich.print(f"Skipping '{mod}'...")

        return number_of_buttons

    def add_recurring_function(self, func: Callable):
        self._recurring_tasks.append(func)

    def the_button_was_double_clicked(self, *args, **kwargs):
        DEBUG and LOGGER.debug(f"The button was double clicked {args=}, {kwargs=}.")

    def the_button_was_pressed(self, button: DynamicButton, panel, *args, **kwargs):
        DEBUG and LOGGER.debug(f"The button was pressed {button=}, {panel=}, {args=}, {kwargs=}.")

        if button.immediate_run():
            if button.function.__ui_allow_kernel_interrupt__:
                self.interrupt_kernel()

            self.run_function(button.function, [], {}, button.function.__ui_runnable__)

            # Remove any existing arguments panel from a previous button

            if self._args_panel:
                self._args_panel.hide()
                self._args_panel = None

            # Deselect the previously selected button

            if self.previous_selected_button is not None:
                self.previous_selected_button.deselect()
                self.previous_selected_button = None

            return

        # TODO
        #   * This should be done from the control or model and probably in the background?
        #   * Add ArgumentsPanel in a tabbed widget? When should it be removed from the tabbed widget? ...

        ui_args = get_arguments(button.function)

        args_panel = ArgumentsPanel(button, ui_args)
        args_panel.run_button.clicked.connect(
            lambda checked: self.run_function(
                args_panel.function, args_panel.args, args_panel.kwargs, args_panel.runnable
            )
        )
        args_panel.close_button.clicked.connect(self.close_args_panel)
        args_panel.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        if self._args_panel is None:
            self._splitter.insertWidget(1, args_panel)
        else:
            self._splitter.replaceWidget(1, args_panel)

        self._args_panel = args_panel

        if self.previous_selected_button is not None:
            self.previous_selected_button.deselect()

        button.select()
        self.previous_selected_button = button

        # This scrolls the buttons panel to make the selected button is still visible
        # after the Arguments panel appeared.

        panel.ensureWidgetVisible(button)

    def close_args_panel(self):
        if self._args_panel is not None:
            self._args_panel.hide()
            self._args_panel = None
        if self.previous_selected_button is not None:
            self.previous_selected_button.deselect()

    @pyqtSlot(object)
    def function_output(self, data: object):
        self._console_panel.append(data if is_renderable(data) else str(data))

    @pyqtSlot(str)
    def function_output_html(self, data: str):
        self._console_panel.append_html(data)

    @pyqtSlot(str)
    def function_output_png(self, data: str):
        image = QImage()
        if not image.loadFromData(b64decode(data), 'PNG'):
            print("Could not convert image/png to QImage")

        width = 800
        self.png_widget = QWidget()
        self.png_widget.setMinimumSize(width, int(width/16*9))
        pixmap = QPixmap()
        if not pixmap.loadFromData(b64decode(data), 'PNG'):
            print("Could not convert image/png data to QPixmap")
            pixmap.fromImage(image)
        label = QLabel()
        label.setPixmap(pixmap)

        layout = QHBoxLayout()
        layout.addWidget(label)

        self.png_widget.setLayout(layout)
        self.png_widget.show()

    @pyqtSlot(object, str, bool)
    def function_complete(self, runnable: FunctionRunnable, name: str, success: bool):
        if success:
            self._console_panel.append(f"----- function '{name}' execution finished.")
        else:
            self._console_panel.append(f"----- function '{name}' raised an Exception.")

        try:
            self._gui_apps.remove(runnable)
            DEBUG and self._console_panel.append(
                f"[green]Removed '{runnable.func_name}' from list of runnable threads.[/green]")
        except ValueError:
            self._console_panel.append(f"[red]Couldn't find '{runnable.func_name}' on list of runnable threads..[/red]")

    @pyqtSlot(Exception)
    def function_error(self, msg: Exception):
        text = Text.styled(f"{msg.__class__.__name__}: {msg}", style="bold red")
        self._console_panel.append(msg)

    @pyqtSlot(str)
    def input_request(self, msg: str):
        message = textwrap.dedent(
            """\
            Input Request from Script\n\n
            There was an input request from the running script.
            The question is in the output console of the main GUI.\n\n
            Please answer the question with Yes or No.
            """
        )

        self.question_dialog = YesNoQuestion(message)

        self._buttons_widget.setDisabled(True)
        if self._args_panel is not None:
            self._args_panel.setDisabled(True)

        self.question_dialog.show()
        self.question_dialog.button_box.accepted.connect(partial(self.answer, "Y"))
        self.question_dialog.button_box.rejected.connect(partial(self.answer, "N"))

    def answer(self, msg: str, *args, **kwargs):
        self.input_queue.put(msg)
        # print(f"answer -> {msg=}, {args=}, {kwargs=}")
        self.question_dialog.close()
        self.question_dialog = None

        self._buttons_widget.setDisabled(False)
        if self._args_panel is not None:
            self._args_panel.setDisabled(False)


class YesNoQuestion(QDialog):
    def __init__(self, message: str, title: str = None, buttons=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title or "Reply to Question from Console")

        if buttons is None:
            buttons = QDialogButtonBox.Yes | QDialogButtonBox.No

        self.button_box = QDialogButtonBox(buttons)

        self.layout = QVBoxLayout()
        message = QLabel(message)
        self.layout.addWidget(message)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
