"""
The user types are class objects that are used as type hints for arguments in a functions that is decorated with the
`exec_ui`/`exec_task` decorator. Use these types if you need more control over input values for arguments to your
functions.

User types can of course be provided as part of your own package.

The user types provided by this module are:

  * CallBack: used when allowed values and defaults needs to be determined at run time
  * FixedList: a simple fixed list of values
  * ListList: a list of lists with the outer list expandable

"""
from __future__ import annotations

import inspect
import itertools
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Callable
from typing import List
from typing import Tuple
from typing import Union

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from .gui import IconLabel
from .utils import combo_box_from_enum
from .utils import combo_box_from_list

HERE = Path(__file__).parent.resolve()


class TypeObject:
    def __init__(self, name: str = None):
        self.name = name

    @property
    def __name__(self):
        return self.name or self.__class__.__name__

    def get_widget(self):
        raise NotImplementedError


class UQWidget(QWidget):
    def __init__(self):
        super().__init__()

    def get_value(self):
        raise NotImplementedError

    def _cast_arg(self, field: QLineEdit | QCheckBox, literal: str | Callable):
        if literal is bool:
            return field.checkState() == Qt.Checked

        if not (value := field.displayText() or field.placeholderText()):
            return None

        try:
            return literal(value)
        except (ValueError, TypeError) as exc:
            print(f"Exception caught: {exc}")
            return value


class Callback(TypeObject):
    """
    A user type that can be used as a type hint in the arguments list of an `exec_ui` function. Use a call back when
    allowed values and defaults need to be determined when the button is clicked to generate the arguments panel
    instead of at import time.

    Args:
         func: the function/object to call that determines the type and values of this argument
         default: the function/object to call that determines the default value(s)
         name: the string to be displayed in the arguments panel. This is usually the type of the argument.
    """
    def __init__(self, func: Callable, default: Callable = None, name: str = None):
        super().__init__(name=name)
        self.func = func
        self.default_func = default

    def get_widget(self):
        return CallbackWidget(self.func, self.default_func)


class CallbackWidget(UQWidget):
    def __init__(self, func: Callable, default_func: Callable):
        super().__init__()

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)

        self.func_rc = func()

        if isinstance(self.func_rc, (list, tuple)):
            self.widget:QComboBox = combo_box_from_list(self.func_rc)
            if default_func is not None:
                self.widget.setCurrentText(str(default_func()))
        elif inspect.isclass(self.func_rc) and issubclass(self.func_rc, Enum):
            self.widget: QComboBox = combo_box_from_enum(self.func_rc)
            if default_func is not None:
                self.widget.setCurrentText(default_func().name)
        else:
            self.widget = QLineEdit()
            self.widget.setPlaceholderText(str(self.func_rc))

        hbox.addWidget(self.widget)

        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hbox)

    def get_value(self):
        if not isinstance(self.widget, QComboBox):
            return self.widget.displayText() or self.widget.placeholderText()

        if isinstance(self.func_rc, (list, tuple)):
            return self.func_rc[self.widget.currentIndex()]
        else:
            return self.func_rc[self.widget.currentText()]


class FixedList(TypeObject):
    """
    A user type for a simple List of fixed size.

    Args:
        literals: the types for each of the values in the list
        defaults: defaults for each of the values in the list
        name: the string to be used in the arguments panel to display the type or a description
    """
    def __init__(self, literals: List[Union[str, Callable]], defaults: List = None, name: str = None):
        super().__init__(name=name or "List")
        self._literals = literals
        self._defaults = defaults or []

    def __repr__(self):
        return f"List({self._literals} = {self._defaults})"

    def __iter__(self):
        return iter(itertools.zip_longest(self._literals, self._defaults))

    def get_widget(self):
        return FixedListWidget(self)


class FixedListWidget(UQWidget):
    def __init__(self, type_object: FixedList):
        super().__init__()

        self._type_object = type_object

        row_widget, self.fields = self._row(expand_default=True)

        row_layout = QHBoxLayout()
        row_layout.addWidget(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # self.setStyleSheet("background-color: #00afff; margin:0px; border:1px solid #0000d7; ")  # for debugging

        self.setLayout(row_layout)

    def get_value(self) -> List:
        return [
            self._cast_arg(f, t)
            for f, (t, d) in zip(self.fields, self._type_object)
        ]

    def _row(self, expand_default: bool = False) -> Tuple[QWidget, List]:
        widget = QWidget()

        hbox = QHBoxLayout()

        fields = []
        for x, y in self._type_object:
            if not expand_default:
                y = None
            if x is bool:
                field = QCheckBox()
                field.setCheckState(Qt.Checked if y is not None else Qt.Unchecked)
            else:
                field = QLineEdit()
                field.setPlaceholderText(str(y) if y is not None else "")

            if x is int:
                field.setValidator(QIntValidator())
            elif x is float:
                field.setValidator(QDoubleValidator())

            fields.append(field)
            type_hint = QLabel(x if isinstance(x, str) else x.__name__)
            type_hint.setStyleSheet("color: gray")
            hbox.addWidget(field)
            hbox.addWidget(type_hint)

        hbox.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(hbox)

        return widget, fields


class ListList(TypeObject):
    """
    A user type for a list of lists. The outer list is extendable, rows can be added with a '+' button and
    removed with a 'x' button. The inner list is fixed and will be constructed from the literals and defaults.

    Args:
        literals: the types for each of the values in the inner lists
        defaults: defaults for each of the values in the first inner list
        name: the string to be used in the arguments panel to display the type or a description
    """

    def __init__(self, literals: List[Union[str, Callable]], defaults: List = None, name: str = None):
        super().__init__(name=name or "list of lists")
        self._literals = literals
        self._defaults = defaults or []

    def __repr__(self):
        return f"ListList({self._literals} = {self._defaults})"

    def __iter__(self):
        return iter(itertools.zip_longest(self._literals, self._defaults))

    def get_widget(self):
        return ListListWidget(self)


class ListListWidget(UQWidget):
    def __init__(self, type_object: ListList):
        super().__init__()

        self._type_object = type_object
        self._rows: List[List] = []
        self._rows_layout = QVBoxLayout()

        row, fields = self._row('+', expand_default=True)

        self._rows_layout.addWidget(row)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)

        self._rows.append(fields)

        self.setLayout(self._rows_layout)

    def get_value(self) -> List[List]:
        return [
            [
                self._cast_arg(f, t)
                for f, (t, d) in zip(field, self._type_object)
            ] for field in self._rows
        ]

    def _row(self, row_button: str, expand_default: bool = False):
        widget = QWidget()

        hbox = QHBoxLayout()

        fields = []
        for x, y in self._type_object:
            if not expand_default:
                y = None
            if x is bool:
                field = QCheckBox()
                field.setCheckState(Qt.Checked if y is not None else Qt.Unchecked)
            else:
                field = QLineEdit()
                field.setPlaceholderText(str(y) if y is not None else "")

            if x is int:
                field.setValidator(QIntValidator())
            elif x is float:
                field.setValidator(QDoubleValidator())

            fields.append(field)
            type_hint = QLabel(x if isinstance(x, str) else x.__name__)
            type_hint.setStyleSheet("color: gray")
            hbox.addWidget(field)
            hbox.addWidget(type_hint)

        if row_button == '+':
            button = IconLabel(icon_path=HERE / "icons/add.svg")
            button.mousePressEvent = partial(self._add_row, 'x')
        elif row_button == 'x':
            button = IconLabel(icon_path=HERE / "icons/delete.svg")
            button.mousePressEvent = partial(self._delete_row, widget, fields)
        else:
            raise ValueError(f"Unknown row_button '{row_button}', use '+' or 'x'")

        hbox.addWidget(button)
        hbox.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(hbox)

        return widget, fields

    def _add_row(self, button_type: str, *args):
        row, fields = self._row(button_type)
        self._rows_layout.addWidget(row)
        self._rows.append(fields)

    def _delete_row(self, widget: QWidget, fields: List, *args):
        self._rows_layout.removeWidget(widget)
        self._rows.remove(fields)
