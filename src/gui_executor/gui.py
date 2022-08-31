from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QLabel


class IconLabel(QLabel):

    icon_size = QSize(16, 16)

    def __init__(self, icon_path: Path | str, size: QSize = icon_size):
        super().__init__()

        self.icon_path = str(icon_path)
        self.setFixedSize(size)

    def set_icon_path(self, icon_path: Path | str):
        self.icon_path = str(icon_path)

    def paintEvent(self, *args, **kwargs):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        renderer = QSvgRenderer()
        renderer.load(self.icon_path)
        renderer.render(painter)

        painter.end()
