import contextlib
import importlib
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import Tuple

from .exec import find_modules
from .exec import find_subpackages
from .exec import find_ui_button_functions
from .exec import find_ui_recurring_functions


class Model:
    def __init__(self, module_path: str):
        self._module_path = module_path

    @property
    def module_path(self):
        return self._module_path

    def reload_functions(self, mod):
        ...

    def get_ui_buttons_functions(self, mod: str) -> Dict[str, Callable]:
        return find_ui_button_functions(mod)

    def get_ui_recurring_functions(self, mod: str) -> Dict[str, Callable]:
        return find_ui_recurring_functions(mod)

    def get_ui_modules(self, module_path: str = None) -> Dict[str, Tuple[str, Path]]:
        module_path = module_path or self._module_path
        response = {}
        for name, path in find_modules(module_path).items():
            with contextlib.suppress(ModuleNotFoundError):
                mod = importlib.import_module(path)
                display_name = getattr(mod, "UI_MODULE_DISPLAY_NAME", name)
                response[name] = (display_name, path)
        return response

    def get_ui_subpackages(self, module_path: str = None) -> Dict[str, Tuple[str, Path]]:
        module_path = module_path or self._module_path
        response = {}
        for name, path in find_subpackages(module_path).items():
            mod = importlib.import_module(f"{module_path}.{name}")
            display_name = getattr(mod, "UI_TAB_DISPLAY_NAME", name)
            response[name] = (display_name, path)
        return response
