from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget

from ui.SelectableLabel import SelectableLabel

class Current_Clue_Widget(QWidget):
    def __init__(self):
        super().__init__()
        shared_bg = "#47c8ff"

        # Container widget paints the background; spacing inherits its color.
        container = QWidget(self)
        container.setAutoFillBackground(True)
        container.setStyleSheet(f"background-color: {shared_bg};")

        self.current_clue_label = SelectableLabel(container, text="Select a cell to see clue")
        self.current_clue_label.setTextFormat(Qt.RichText)
        self.current_clue_label.setFont(QFont("Arial", 12))
        self.current_clue_label.setWordWrap(True)
        self.current_clue_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.current_clue_label.setMinimumHeight(50)
        self.current_clue_label.setStyleSheet("background-color: transparent;")

        self.number_label = QLabel()
        self.number_label.setFixedWidth(20)
        font = QFont("Arial", 12)
        font.setBold(True)
        self.number_label.setFont(font)
        self.number_label.setStyleSheet("background-color: transparent;")

        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addSpacing(12)
        row_layout.addWidget(self.number_label)
        row_layout.addSpacing(12)
        row_layout.addWidget(self.current_clue_label)
        container.setLayout(row_layout)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(container)
        self.setLayout(outer_layout)


    def set_clue(self, clue):
        #self.current_clue_label.setText(f"<b>{clue.number}{'A' if clue.direction == 'across' else 'D'}</b><span style='margin-left:12px'></span>{clue.text}")
        self.number_label.setText(f"{clue.number}{'A' if clue.direction == 'across' else 'D'}")
        self.current_clue_label.setText(f"{clue.text}")
