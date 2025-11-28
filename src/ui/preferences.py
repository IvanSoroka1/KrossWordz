from PySide6.QtWidgets import QWidget, QVBoxLayout,QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog 
from PySide6.QtCore import QSettings, QDir

class preferences(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.gemini_api_key = None 
        self.settings= QSettings("KrossWordz", "KrossWordz")
        self.gemini_key_input = QVBoxLayout()
        self.gemini_api_key_label = QLabel("Gemini API Key")
        self.gemini_api_key_input = QLineEdit()
        if self.settings.value("gemini_api_key"):
            self.gemini_api_key_input.setText(self.settings.value("gemini_api_key"))

        self.gemini_key_input.addWidget(self.gemini_api_key_label)
        self.gemini_key_input.addWidget(self.gemini_api_key_input)
        self.layout.addLayout(self.gemini_key_input)

        self.directory_input = QVBoxLayout()
        self.puzzles_dir_label = QLabel("Puzzles Directory")

        row = QHBoxLayout()
        browse_btn = QPushButton("Browse... ")
        browse_btn.clicked.connect(self.pick_puzzles_dir)

        self.puzzles_dir_input = QLineEdit()
        row.addWidget(self.puzzles_dir_input)
        row.addWidget(browse_btn)

        if self.settings.value("puzzles_dir"):
            self.puzzles_dir_input.setText(self.settings.value("puzzles_dir"))

        self.directory_input.addWidget(self.puzzles_dir_label)
        self.directory_input.addLayout(row)

        self.layout.addLayout(self.directory_input)

        self.apply_button = QPushButton("Apply")
        #self.apply_button.clicked.connect(lambda: self._save_api_key(self.gemini_api_key_input.text()))
        self.apply_button.clicked.connect(self._save_settings)
        self.layout.addWidget(self.apply_button)

    def pick_puzzles_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory", self.settings.value("puzzles_dir") or QDir.homePath())
        if path:
            self.puzzles_dir_input.setText(path)

    def _save_settings(self): 
        self.settings.setValue("gemini_api_key", self.gemini_api_key_input.text())
        self.settings.setValue("puzzles_dir", self.puzzles_dir_input.text())
