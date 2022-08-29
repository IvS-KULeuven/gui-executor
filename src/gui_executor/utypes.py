from __future__ import annotations

import itertools
from functools import partial
from pathlib import Path
from typing import Callable
from typing import List
from typing import Optional
from typing import Union

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from .gui import IconLabel

HERE = Path(__file__).parent.resolve()


class TypeObject:
    @property
    def __name__(self):
        return self.__class__.__name__


class ListList(TypeObject):
    """
    A TypeObject for a List of Lists.
    """
    def __init__(self, literals: List[Union[str, Callable]], defaults: List = None):
        super().__init__()
        self._literals = literals
        self._defaults = defaults or []

    def __repr__(self):
        return f"ListList({self._literals} = {self._defaults})"

    def __iter__(self):
        return iter(itertools.zip_longest(self._literals, self._defaults))

    def get_widget(self):
        return ListListWidget(self)


class UQWidget(QWidget):
    def __init__(self):
        super().__init__()

    def get_value(self):
        raise NotImplementedError


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
