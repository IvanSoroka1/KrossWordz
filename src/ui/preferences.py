from PySide6.QtWidgets import QWidget, QVBoxLayout,QHBoxLayout, QLabel, QLineEdit, QPushButton 
from PySide6.QtCore import QSettings
class preferences(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.gemini_api_key = None 
        self.settings= QSettings("KrossWordz", "KrossWordz")
        self.hlayout = QHBoxLayout()
        self.gemini_api_key_label = QLabel("Gemini API Key")
        self.gemini_api_key_input = QLineEdit()
        if self.settings.value("gemini_api_key"):
            self.gemini_api_key_input.setText(self.settings.value("gemini_api_key"))

        self.hlayout.addWidget(self.gemini_api_key_label)
        self.hlayout.addWidget(self.gemini_api_key_input)
        self.layout.addLayout(self.hlayout)
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(lambda: self._save_api_key(self.gemini_api_key_input.text()))
        self.layout.addWidget(self.apply_button)

    def hideEvent(self, event):
        self._save_api_key(self.gemini_api_key_input.text())
        super().hideEvent(event)

    def _save_api_key(self, api_key): 
        self.settings.setValue("gemini_api_key", api_key)