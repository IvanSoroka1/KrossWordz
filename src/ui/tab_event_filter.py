from PySide6.QtCore import QObject, Qt


class TabEventFilter(QObject):
    """Global event filter to capture Tab navigation for the crossword widget."""

    def __init__(self, crossword_widget):
        super().__init__()
        self._crossword_widget = crossword_widget

    def eventFilter(self, obj, event):  # noqa: N802 (Qt interface)
        if event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
                print(f"DEBUG: Global event filter caught tab key from: {obj}")
                self._crossword_widget.handle_global_navigation(event.key())
                return True
        return False
