from __future__ import annotations

import binascii
import contextlib
import inspect
import logging
import os
import re
import sys
import textwrap
import time
from enum import Enum
from io import StringIO
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Tuple

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QFileDialog
from rich import box
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.tree import Tree


def replace_environment_variable(input_string: str) -> str:
    """Returns the `input_string` with all occurrences of ENV['var'] expanded.

    >>> replace_environment_variable("ENV['HOME']/data/CSL")
    '/Users/rik/data/CSL'

    Args:
        input_string (str): the string to replace
    Returns:
        The input string with the ENV['var'] replaced, or None when the environment variable
        doesn't exist.
    """

    match = re.search(r"(.*)ENV\[['\"](\w+)['\"]\](.*)", input_string)
    if not match:
        return input_string
    pre_match, var, post_match = match[1], match[2], match[3]

    result = os.getenv(var, None)

    return pre_match + result + post_match if result else None


def walk_dict_tree(dictionary: dict, tree: Tree, text_style: str = "green"):
    """
    Walk recursively through the dictionary and add all nodes to the given tree.
    The tree is a Rich Tree object.
    """
    for k, v in dictionary.items():
        if isinstance(v, dict):
            branch = tree.add(f"[purple]{k}", style="", guide_style="dim")
            walk_dict_tree(v, branch, text_style=text_style)
        else:
            text = Text.assemble((str(k), "medium_purple1"), ": ", (str(v), text_style))
            tree.add(text)


def expand_path(path: Path | str) -> Path:
    """
    Returns the expanded absolute path.

    Args:
        path: a string representing a path segment or a Path

    Returns:
        An absolute path.
    """
    path = replace_environment_variable(str(path))
    path = Path(path).expanduser()

    return path.resolve()


def get_file_path(path: str | Path, name: str) -> Path:
    full_path = expand_path(path)
    if not full_path.exists():
        raise ValueError(f"The path '{full_path}' was expanded into '{path}' which doesn't exist.")

    filepath = full_path / name
    if not filepath.exists():
        raise ValueError(f"The generated filepath '{filepath}' doesn't exit for command script {name}")

    return filepath


def remove_ansi_escape(line):
    """
    Returns a new line where all ANSI escape sequences are removed.
    """
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', line)


def get_required_args(code: List | str) -> List[Tuple[str, str | None]]:
    """
    Returns a list of required arguments and their type.

    Args:
        code:

    Returns:

    """
    if isinstance(code, str):
        code = code.split('\n')

    required_args = []
    for line in code:
        if matches := re.findall(r"<<([:\w]+)>>", line):
            print(f"{matches = }")
            for match in matches:
                name, expected_type = match.split(':') if ':' in match else (match, None)
                required_args.append((name, expected_type))

    return required_args


def replace_required_args(code: List | str, args: List) -> List | str:

    code_lines = code.split('\n') if isinstance(code, str) else code

    new_code_lines = []
    for line in code_lines:
        if matches := re.findall(r"<<([:\w]+)>>", line):
            for match in matches:
                print(f"{match = }")
                name, expected_type = match.split(':') if ':' in match else (match, None)
                line = line.replace(f"<<{match}>>", f"****")
        new_code_lines.append(line)
    return new_code_lines


def var_exists(var_name: str):
    frame = inspect.currentframe()

    try:
        return var_name in frame.f_back.f_locals or var_name in frame.f_back.f_globals
    finally:
        del frame


@contextlib.contextmanager
def sys_path(path: Path | str):
    """Context manager that temporarily prepends the `sys.path` with the given argument."""
    import sys

    try:
        sys.path.insert(0, str(path))
        yield
    finally:
        sys.path.pop(0)


class Data(object):
    pass


@contextlib.contextmanager
def capture():
    stdout = sys.stdout
    stderr = sys.stderr
    out = StringIO()
    err = StringIO()
    sys.stdout = out
    sys.stderr = err
    data = Data()
    try:
        yield data
    finally:
        sys.stdout = stdout
        sys.stderr = stderr
        data.stdout = out.getvalue()
        data.stderr = err.getvalue()


def custom_repr(arg: Any):
    """
    This function checks if the argument is an Enum and then returns a proper repr value for it.
    """
    if not isinstance(arg, Enum):
        return repr(arg)

    m = re.fullmatch(r"<([\w.]+): (.*)>", repr(arg))

    return m[1]


def stringify_args(args):
    return ", ".join([custom_repr(arg) for arg in args])


def stringify_kwargs(kwargs):
    return ", ".join([f"{k}={custom_repr(v)}" for k, v in kwargs.items()])


def stringify_imports(args, kwargs):
    return "\n".join(
        f"from {arg.__module__} import {arg.__class__.__name__}"
        for arg in (*args, *kwargs.values())
        if isinstance(arg, Enum)
    )


def create_code_snippet(func: Callable, args: List, kwargs: Dict, call_func: bool = True):

    # Check if one of the args/kwargs is an Enum
    #   * import the proper Enum class
    #   *

    # [3405691582] magic number is defined in gui_executor.transforms

    return textwrap.dedent(
        f"""\
            # [3405691582]
            from rich import print
            from {func.__ui_module__} import {func.__name__}
            from pathlib import Path, PurePath, PosixPath  # might be used by argument types
            {stringify_imports(args, kwargs)}
            
            def main():
                response = {func.__name__}({stringify_args(args)}{', ' if args else ''}{stringify_kwargs(kwargs)})  # [3405691582]
                if response is not None:
                    print(response)
                return response
                    
            {"response = main()" if call_func else ''}
        """
    )


def create_code_snippet_renderable(func: Callable, args: List, kwargs: Dict):

    snippet = f"response = {func.__name__}({stringify_args(args)}{', ' if args else ''}{stringify_kwargs(kwargs)})"

    return Panel(Syntax(snippet, "python", theme='default', word_wrap=True), box=box.HORIZONTALS)


def select_directory(directory: str = None) -> str:
    dialog = QFileDialog()
    dialog.setOption(QFileDialog.ShowDirsOnly, True)
    dialog.setOption(QFileDialog.ReadOnly, True)
    dialog.setOption(QFileDialog.HideNameFilterDetails, True)
    dialog.setDirectory(directory)
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setViewMode(QFileDialog.Detail)
    dialog.setAcceptMode(QFileDialog.AcceptOpen)

    filenames = dialog.selectedFiles() if dialog.exec() else None

    return filenames[0] if filenames is not None else ''


def select_file(filename: str = None, full_path: bool = True) -> str:

    dialog = QFileDialog()
    dialog.setDirectory(filename)
    dialog.setOption(QFileDialog.ReadOnly, True)
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setViewMode(QFileDialog.Detail)
    dialog.setAcceptMode(QFileDialog.AcceptOpen)

    filenames = dialog.selectedFiles() if dialog.exec() else None

    return filenames[0] if filenames is not None else ''


def combo_box_from_enum(enumeration: Enum) -> QComboBox:
    cb = QComboBox()
    cb.addItems([x.name for x in enumeration])
    return cb


def combo_box_from_list(values: List) -> QComboBox:
    cb = QComboBox()
    cb.addItems(str(x) for x in values)
    return cb


def is_renderable(check_object: Any) -> bool:
    """Check if an object may be rendered by Rich, but ignore plain strings."""
    return (
        hasattr(check_object, "__rich__")
        or hasattr(check_object, "__rich_console__")
    )


class Timer(object):
    """
    Context manager to benchmark some lines of code.

    When the context exits, the elapsed time is sent to the default logger (level=INFO).

    Elapsed time can be logged with the `log_elapsed()` method and requested in fractional seconds
    by calling the class instance. When the contexts goes out of scope, the elapsed time will not
    increase anymore.

    Log messages are sent to the logger (including egse_logger for egse.system) and the logging
    level can be passed in as an optional argument. Default logging level is INFO.

    Examples:
        >>> with Timer("Some calculation") as timer:
        ...     # do some calculations
        ...     timer.log_elapsed()
        ...     # do some more calculations
        ...     print(f"Elapsed seconds: {timer()}")  # doctest: +ELLIPSIS
        Elapsed seconds: ...

    Args:
        name (str): a name for the Timer, will be printed in the logging message
        precision (int): the precision for the presentation of the elapsed time
            (number of digits behind the comma ;)
        log_level (int): the log level to report the timing [default=INFO]

    Returns:
        a context manager class that records the elapsed time.
    """

    def __init__(self, name="Timer", precision=3, log_level=logging.INFO):
        self.name = name
        self.precision = precision
        self.log_level = log_level

    def __enter__(self):
        # start is a value containing the start time in fractional seconds
        # end is a function which returns the time in fractional seconds
        self.start = time.perf_counter()
        self.end = time.perf_counter
        return self

    def __exit__(self, ty, val, tb):
        # The context goes out of scope here and we fix the elapsed time
        self._total_elapsed = time.perf_counter()

        # Overwrite self.end() so that it always returns the fixed end time
        self.end = self._end

        logging.log(self.log_level,
                   f"{self.name}: {self.end() - self.start:0.{self.precision}f} seconds")
        return False

    def __call__(self):
        return self.end() - self.start

    def log_elapsed(self):
        """Sends the elapsed time info to the default logger."""
        logging.log(self.log_level,
                   f"{self.name}: {self.end() - self.start:0.{self.precision}f} seconds elapsed")

    def _end(self):
        return self._total_elapsed


bytes_types = (bytes, bytearray)  # Types acceptable as binary data


def _bytes_from_decode_data(s):
    if isinstance(s, str):
        try:
            return s.encode('ascii')
        except UnicodeEncodeError:
            raise ValueError('string argument should contain only ASCII characters')
    if isinstance(s, bytes_types):
        return s
    try:
        return memoryview(s).tobytes()
    except TypeError:
        raise TypeError("argument should be a bytes-like object or ASCII "
                        "string, not %r" % s.__class__.__name__) from None


def b64decode(s, altchars=None, validate=False):
    """Decode the Base64 encoded bytes-like object or ASCII string s.

    Optional altchars must be a bytes-like object or ASCII string of length 2
    which specifies the alternative alphabet used instead of the '+' and '/'
    characters.

    The result is returned as a bytes object.  A binascii.Error is raised if
    s is incorrectly padded.

    If validate is False (the default), characters that are neither in the
    normal base-64 alphabet nor the alternative alphabet are discarded prior
    to the padding check.  If validate is True, these non-alphabet characters
    in the input result in a binascii.Error.
    """
    s = _bytes_from_decode_data(s)
    if altchars is not None:
        altchars = _bytes_from_decode_data(altchars)
        assert len(altchars) == 2, repr(altchars)
        s = s.translate(bytes.maketrans(altchars, b'+/'))
    if validate and not re.fullmatch(b'[A-Za-z0-9+/]*={0,2}', s):
        raise binascii.Error('Non-base64 digit found')
    return binascii.a2b_base64(s)


def print_system_info():
    import sys
    import rich
    import distro

    rich.print(f"distro: {distro.name()}, {distro.version(pretty=True)}")
    rich.print("sys.executable = ", sys.executable)
    rich.print("sys.path = ", sys.path)
