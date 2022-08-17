from .model import Model
from .view import View


class Control:
    def __init__(self, view: View, model: Model):
        self._view = view
        self._model = model

        modules = self._model.get_ui_modules()

        for _, mod in modules.items():
            funcs = self._model.get_ui_buttons_functions(mod)
            for name, func in funcs.items():
                self._view.add_function_button(func)
