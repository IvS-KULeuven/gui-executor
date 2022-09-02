from __future__ import annotations

import importlib
import inspect
import textwrap
import warnings
from enum import IntEnum
from functools import wraps
from pathlib import Path
from pathlib import PosixPath
from pathlib import PurePath
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Tuple
from typing import TypeVar

from . import RUNNABLE_APP
from . import RUNNABLE_KERNEL
from . import RUNNABLE_SCRIPT

"""
The following TypeVars can be used to distinguish between a file and a folder when annotating a function
argument as a Path. The GUI can make the distinction as follows, based on the annotation:

    def func(x: FileName):
        ...

    sig = inspect.signature(func)
    pars = sig.parameters
    par_x = pars['x']
    par_x.annotation is Filename  <-- True

"""

FileName = TypeVar('FileName', bound=Path)
"""A FileName type is the name of a file including the extension, but not it's full path."""
FilePath = TypeVar('FilePath', bound=Path)
"""A FilePath is the absolute or relative path for a file, including filename and extension."""
Directory = TypeVar('Directory', bound=Path)
"A Directory is the location where the file resides."


class Kind(IntEnum):
    BUTTON = 0b00000001
    """Identifies a function to be called after a clicked event on a button in the GUI."""


class ArgumentKind(IntEnum):
    POSITIONAL_ONLY = 0
    POSITIONAL_OR_KEYWORD = 1
    VAR_POSITIONAL = 2
    KEYWORD_ONLY = 3
    VAR_KEYWORD = 4


class Argument:
    def __init__(self, name: str, kind: int, annotation: Any, default: Any):
        self.name = name
        self.kind: ArgumentKind = ArgumentKind(kind)
        self.annotation = annotation
        self.default = default


def exec_ui(
        kind: Kind = Kind.BUTTON,
        description: str = None,
        display_name: str = None,
        input_request: Tuple[str, ...] = ("Continue? [Y/n]", "Abort? [Y/n]"),
        use_kernel: bool = False,
        use_gui_app: bool = False,
        use_script_app: bool = False,
        icons: Tuple[str | Path, ...] = None,
):
    """
    Decorates the function as an Exec UI function. We have different kinds of UI functions. By default,
    the function is decorated as a UI Button which will appear in the UI as a button to execute the function.

    Args:
        kind: identifies the function and what it can be used for [default = BUTTON]
        description: short function description intended to be used as tooltip or similar
        display_name: the string to use for the button name [default = function name]
        input_request: a tuple contain the string to detect when input is asked for
        use_kernel: use the Jupyter kernel when running this function
        use_gui_app: run the script in a GUI app (enables showing plots and table etc.
        use_script_app: run the script as a plain Python script [this is the default if none is specified]
        icons: icons to be used for the button of this function

    Returns:
        The wrapper function object.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # you can put extra code to be run here, based on the arguments to exec_ui
            response = func(*args, **kwargs)
            # or here
            return response
        wrapper.__ui_kind__ = kind
        wrapper.__ui_description__ = description
        wrapper.__ui_display_name__ = display_name
        wrapper.__ui_file__ = func.__code__.co_filename
        wrapper.__ui_module__ = func.__module__
        wrapper.__ui_input_request__ = input_request
        wrapper.__ui_icons__ = icons
        if use_script_app:
            wrapper.__ui_runnable__ = RUNNABLE_SCRIPT
        elif use_kernel:
            wrapper.__ui_runnable__ = RUNNABLE_KERNEL
        elif use_gui_app:
            wrapper.__ui_runnable__ = RUNNABLE_APP
        else:
            wrapper.__ui_runnable__ = RUNNABLE_SCRIPT

        return wrapper

    return decorator


def find_ui_button_functions(module_path: str) -> Dict[str, Callable]:
    """
    Returns a dictionary with function names as keys and the callable function as their value.
    The functions are intended to be used as UI button callable, i.e. a GUI can automatically
    identify these functions and assign them to a `clicked` action of a button.

    Args:
        module_path: string containing a fully qualified module name
    """
    return find_ui_functions(
        module_path,
        lambda x: x.__ui_kind__ & Kind.BUTTON
    )


def find_ui_functions(module_path: str, predicate: Callable = None) -> Dict[str, Callable]:
    """
    Returns a dictionary with function names as keys and the callable function as their value.
    The predicate is a function that returns True or False depending on some required conditions
    for the functions that are returned.

    Args:
        module_path: string containing a fully qualified module name
        predicate: condition to select and return the function
    """
    predicate = predicate if predicate is not None else lambda x: True
    mod = importlib.import_module(module_path)

    return {
        name: member
        for name, member in inspect.getmembers(mod)
        if inspect.isfunction(member) and hasattr(member, "__ui_kind__") and predicate(member)
    }


def find_modules(module_path: str) -> Dict[str, Any]:
    """
    Finds Python modules and scripts in the given module path (non recursively). The modules will not be
    imported, instead their module path will be returned. The idea is that the caller can decide which
    modules to import.

    Args:
        module_path: the module path where the Python modules and scripts are located

    Returns:
        A dictionary with module names as keys and their paths as values.
    """
    mod = importlib.import_module(module_path)

    if hasattr(mod, "__path__") and getattr(mod, "__file__", None) is None:
        warnings.warn(
            textwrap.dedent(f"""
                The module '{mod.__name__}' is a namespace package, i.e. a package without an '__init__.py' file.
                Please, properly define your module and add an '__init__.py' file. The file can be empty.
                Your package is located at {set(mod.__path__)}.
                """)
        )

        paths: List[str] = list(set(mod.__path__))
        location = Path(paths[0])
    else:
        location = Path(mod.__file__).parent

    if not location.is_dir():
        raise ValueError(f"Expected a folder, instead got {str(location)}")

    return {
        item.stem: f"{module_path}.{item.stem}"
        for item in location.glob("*.py")
        if item.name not in ["__init__.py"]
    }


def get_script_module(script_location: str, exec_module: bool = True) -> Dict[str, Any]:
    script_path = Path(script_location).resolve()

    loader = importlib.machinery.SourceFileLoader(script_path.stem, str(script_path))
    spec = importlib.util.spec_from_loader(script_path.stem, loader)
    script = importlib.util.module_from_spec(spec)

    if exec_module:
        loader.exec_module(script)

    return {script_path.stem: script}


# Why I use my own class Arguments instead of just inspect.Parameter?
# * because I don't want to be dependent on inspect.Parameter.empty in my apps
# * because Argument might get more info from the exec_ui decorator, like e.g. units
#   or a description of the argument
def get_arguments(func: Callable) -> Dict[str, Argument]:
    """
    Determines the signature of the function and returns a dictionary with keys the name of the arguments
    and values the Argument object for the arguments.

    Args:
        func: a function callable

    Returns:
        A dictionary with all arguments.
    """
    sig = inspect.signature(func)
    pars = sig.parameters
    return {
        k: Argument(
            k,
            int(v.kind),
            None if v.annotation == inspect.Parameter.empty else v.annotation,
            None if v.default == inspect.Parameter.empty else v.default
        )
        for k, v in pars.items()
    }
