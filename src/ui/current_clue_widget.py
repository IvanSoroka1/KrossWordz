from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget

from ui.SelectableLabel import SelectableLabel

class Current_Clue_Widget(QWidget):
    def __init__(self, width = None):
        super().__init__()
        shared_bg = "#47c8ff"

        # self.container widget paints the background; spacing inherits its color.

        self.container = QWidget(self)
        self.container.setAutoFillBackground(True)
        self.container.setStyleSheet(f"background-color: {shared_bg};")
        if width:
            self.container.setFixedWidth(width)

        self.current_clue_label = SelectableLabel(self.container, text="Select a cell to see clue")
        self.current_clue_label.setTextFormat(Qt.RichText)
        self.current_clue_label.setFont(QFont("Arial", 12))
        self.current_clue_label.setWordWrap(True)
        self.current_clue_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.current_clue_label.setMinimumHeight(50)

        # this is necessary to set so that the color of the menu on right click is also the same color
        self.current_clue_label.setStyleSheet(f"background-color: {shared_bg};")

        self.number_label = QLabel()
        self.number_label.setFixedWidth(20)
        font = QFont("Arial", 12)
        font.setBold(True)
        self.number_label.setFont(font)
        self.number_label.setStyleSheet(f"background-color: transparent;")

        row_layout = QHBoxLayout(self.container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addSpacing(12)
        row_layout.addWidget(self.number_label)
        row_layout.addSpacing(12)
        row_layout.addWidget(self.current_clue_label)
        self.container.setLayout(row_layout)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.container)
        self.setLayout(outer_layout)


    def set_clue(self, clue):
        #self.current_clue_label.setText(f"<b>{clue.number}{'A' if clue.direction == 'across' else 'D'}</b><span style='margin-left:12px'></span>{clue.text}")
        self.number_label.setText(f"{clue.number}{'A' if clue.direction == 'across' else 'D'}")
        self.current_clue_label.setText(f"{clue.text}")
    
    def resize(self, width):
        self.container.setFixedWidth(width)
