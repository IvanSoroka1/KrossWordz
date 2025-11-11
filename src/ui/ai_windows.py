from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from openai import OpenAI

from PySide6.QtCore import QSettings

import google.generativeai as genai



class ai_window(QWidget):
    def __init__(self):
        super().__init__()
        self.initialized = False
        settings = QSettings("KrossWordz", "KrossWordz")
        if settings.value("gemini_api_key") !=  None:
            genai.configure(api_key = settings.value("gemini_api_key"))
            self.initialized = True

        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")

        self.layout = QVBoxLayout() 
        self.setLayout(self.layout)
        self.show()

    def explain_clue(self, clue, answer):
        if not self.initialized:
            self.layout.addWidget(QLabel("No API key found. Please set one in preferences"))
        else:
            prompt =  f'''Please explain this crossword clue to me. The clue is "{clue}" and the answer is "{answer}"'''
            # response = self.client.chat.completions.create(
            #     model="gpt-5-mini",
            #     messages=[{"role": "user", "content": prompt}]
            # )
            #self.layout.addWidget(QLabel(response.choices[0].message.content))
            response = self.gemini_model.generate_content(prompt) 
            self.layout.addWidget(QLabel(response.text))
        