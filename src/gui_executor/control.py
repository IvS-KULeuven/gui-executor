from .model import Model
from .view import View


class Control:
    def __init__(self, view: View, model: Model):
        self._view = view
        self._model = model

        self._modules = self._model.get_ui_modules()

        self._funcs = self._model.get_ui_buttons_functions(self._modules["ui_test_script"])

        for name, func in self._funcs.items():
            self._view.add_function_button(func)
