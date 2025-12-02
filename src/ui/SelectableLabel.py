from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtWidgets import QApplication, QLabel, QMenu
from ui.lookup import open_onelook

class SelectableLabel(QLabel):
    lookup_word = Signal(str)

    def __init__(self, parent=None, text=None):
        super().__init__(parent=parent, text=text)

        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        #self.setFocusPolicy(Qt.ClickFocus)  # needed for keyboard selection

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

    def _show_menu(self, pos: QPoint):
        menu = QMenu(self)
        copy_action = menu.addAction("Copy")
        select_all_action = menu.addAction("Select All")
        lookup_action = menu.addAction("Lookup this selection in the dictionary")
        action = menu.exec(self.mapToGlobal(pos))
        if action == copy_action and self.hasSelectedText():
            QApplication.clipboard().setText(self.selectedText())
        elif action == select_all_action:
            self.setSelection(0, len(self.text()))
        elif action == lookup_action:
            open_onelook(self.selectedText())

