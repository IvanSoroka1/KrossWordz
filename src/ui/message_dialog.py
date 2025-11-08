"""Custom modal dialog that dims the parent window while it is visible."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QEvent, QPropertyAnimation, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ShadeOverlay(QWidget):
    """Full-window translucent overlay used to dim the background."""

    def __init__(self, parent: Optional[QWidget] = None, color: Optional[QColor] = None):
        super().__init__(parent)
        self._color = color or QColor(0, 0, 0, 150)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(False)
        if parent is not None:
            parent.installEventFilter(self)
            self._sync_to_parent()
        self._apply_stylesheet()
        self.hide()

    def set_color(self, color: QColor) -> None:
        """Allow callers to change the dimming color."""
        self._color = color
        self._apply_stylesheet()

    def show_with_fade(self, duration_ms: int = 150) -> None:
        """Show the overlay with a quick fade animation."""
        self._sync_to_parent()
        self.setWindowOpacity(0.0)
        self.show()
        animation = QPropertyAnimation(self, b"windowOpacity", self)
        animation.setDuration(duration_ms)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def hide_with_fade(self, duration_ms: int = 150) -> None:
        """Hide the overlay with a fade-out."""
        animation = QPropertyAnimation(self, b"windowOpacity", self)
        animation.setDuration(duration_ms)
        animation.setStartValue(self.windowOpacity())
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def _finalize():
            self.hide()
            animation.deleteLater()

        animation.finished.connect(_finalize)
        animation.start()

    def eventFilter(self, watched, event):  # noqa: D401 - Qt override
        if watched is self.parentWidget() and event.type() in (QEvent.Resize, QEvent.Move, QEvent.Show):
            self._sync_to_parent()
        return super().eventFilter(watched, event)

    def _sync_to_parent(self) -> None:
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())
            self.raise_()

    def _apply_stylesheet(self) -> None:
        rgba = f"rgba({self._color.red()}, {self._color.green()}, {self._color.blue()}, {self._color.alpha()})"
        self.setStyleSheet(f"background-color: {rgba};")


class MessageDialog(QDialog):
    """Frameless dialog that presents text while the overlay dims the parent."""

    def __init__(self, text: str, parent: Optional[QWidget] = None, button_text: str = "OK"):
        super().__init__(parent)
        self._overlay = ShadeOverlay(parent)

        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        panel = QFrame(self)
        panel.setObjectName("messagePanel")
        panel.setStyleSheet(
            "#messagePanel { background-color: white; border-radius: 16px; padding: 16px; }"
            "QLabel { color: #111; font-size: 16px; }"
        )

        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel(text, panel))

        button = QPushButton(button_text, panel)
        button.clicked.connect(self.accept)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)

        shadow = QGraphicsDropShadowEffect(panel)
        shadow.setBlurRadius(35)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 60))
        panel.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(panel)

    def showEvent(self, event):  # noqa: D401 - Qt override
        self._overlay.raise_()
        self._overlay.show_with_fade()
        super().showEvent(event)
        self.raise_()

    def hideEvent(self, event):  # noqa: D401 - Qt override
        self._overlay.hide_with_fade()
        super().hideEvent(event)


def show_message(parent: QWidget, correct: bool, button_text: str = "OK") -> int:
    """Convenience helper to display the dialog and run it modally."""
    text = "You have solved the puzzle" if correct else "You have made one or more mistakes."
    dialog = MessageDialog(text, parent=parent, button_text=button_text)
    return dialog.exec()
