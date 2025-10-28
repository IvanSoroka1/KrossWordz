from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
    QTextEdit,
)


class CluesTextEdit(QTextEdit):
    """Text edit styled for clues that forwards navigation keys to the parent."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMinimumSize(400, 250)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def keyPressEvent(self, event):  # noqa: N802 (Qt interface)
        if event.key() in (
            Qt.Key_Left,
            Qt.Key_Right,
            Qt.Key_Up,
            Qt.Key_Down,
            Qt.Key_Space,
            Qt.Key_Tab,
        ):
            event.ignore()
        else:
            super().keyPressEvent(event)


class CluesPanel(QWidget):
    """Container showing across and down clues side by side."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #d0d0d0; border: 1px solid #999999;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.across_text_edit = self._create_section(layout, "ACROSS")
        self.down_text_edit = self._create_section(layout, "DOWN")

    def _create_section(self, parent_layout: QHBoxLayout, title: str) -> CluesTextEdit:
        container = QWidget(self)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        section_layout = QVBoxLayout(container)

        label = QLabel(title)
        label.setFont(QFont("Arial", 11, QFont.Bold))
        section_layout.addWidget(label)

        text_edit = CluesTextEdit(container)
        section_layout.addWidget(text_edit)

        parent_layout.addWidget(container)
        return text_edit

    def set_across_text(self, text: str) -> None:
        self.across_text_edit.setText(text)

    def set_down_text(self, text: str) -> None:
        self.down_text_edit.setText(text)

    def clear(self) -> None:
        self.across_text_edit.clear()
        self.down_text_edit.clear()
