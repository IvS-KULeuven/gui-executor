from typing import Any
from typing import Callable
from typing import Dict

from .exec import find_modules
from .exec import find_ui_button_functions


class Model:
    def __init__(self, module_path: str):
        self._module_path = module_path

    def reload_functions(self, mod):
        ...

    def get_ui_buttons_functions(self, mod: str) -> Dict[str, Callable]:
        return find_ui_button_functions(mod)

    def get_ui_modules(self) -> Dict[str, Any]:
        return find_modules(self._module_path)
