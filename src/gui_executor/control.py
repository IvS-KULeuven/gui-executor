import rich

from .model import Model
from .view import View


class Control:
    def __init__(self, view: View, model: Model):
        self._view = view
        self._model = model

        modules = self._model.get_ui_modules()

        for _, mod in modules.items():
            try:
                funcs = self._model.get_ui_buttons_functions(mod)

                # Our functions are all decorated functions, decorated with the @exec_ui.
                # Since we have used functools.wraps(), all our functions have the attribute __wrapped__
                # which points to the original function. What we need is the first line of the function
                # in the module file, because we want the functions to be sorted in the order they appear
                # in the source code file and not alphabetically.

                for name, func in sorted(funcs.items(), key=lambda x: x[1].__wrapped__.__code__.co_firstlineno):
                    # print(f"{func.__name__} -> {func.__wrapped__.__code__.co_firstlineno = }")
                    self._view.add_function_button(func)
            except ModuleNotFoundError as exc:
                rich.print(f"[red]{exc.__class__.__name__}: {exc}[/]")
                rich.print(f"Skipping '{mod}'...")
