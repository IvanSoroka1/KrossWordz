from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QScrollArea
from openai import OpenAI

from PySide6.QtCore import QSettings, QThread, Signal, QObject, Slot 

import google.generativeai as genai




class ai_window(QWidget):
    def __init__(self):
        super().__init__()
        self.jobs = {}
        self._labels: list[QLabel] = []

        settings = QSettings("KrossWordz", "KrossWordz")
        self.gemini_model = None
        if settings.value("gemini_api_key") !=  None:
            genai.configure(api_key = settings.value("gemini_api_key"))
            self.initialized = True
            self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()        
        self.layout = QVBoxLayout(content_widget)

        scroll_area.setWidget(content_widget)

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll_area)

        self.setLayout(outer_layout)
    



    def explain_clue(self, clue, answer):
        if self.gemini_model == None:
            self.layout.addWidget(self._create_label("No API key found. Please set one in preferences"))
        else:
            thread = QThread(self)
            thread.setObjectName("ExplanationThread")
            worker = ClueExplanationWorker(clue, answer, self.gemini_model)
            label = self._create_label(f'Explaining clue "{clue}" with answer "{answer}"…')
            self.layout.addWidget(label)
            self.jobs[worker] = (thread, label)
            worker.moveToThread(thread)
            thread.started.connect(worker.process)
            worker.finished.connect(self.onWorkerFinished)
            thread.start()

    def onWorkerFinished(self, output):
        worker = self.sender()
        thread, label = self.jobs.pop(worker)
        label.setText(output)
        worker.deleteLater()
        thread.finished.connect(thread.deleteLater)
        thread.quit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_label_widths()

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self._labels.append(label)
        self._constrain_label_width(label)
        return label

    def _update_label_widths(self) -> None:
        for label in self._labels:
            self._constrain_label_width(label)

    def _constrain_label_width(self, label: QLabel) -> None:
        available_width = self.contentsRect().width()
        if available_width <= 0:
            available_width = self.width()
        if available_width > 0:
            label.setMaximumWidth(available_width)
        

        

        
class ClueExplanationWorker(QObject):
    finished = Signal(str)

    def __init__(self, clue, answer, gemini_model):
        super().__init__()
        self.clue = clue
        self.answer = answer
        self.gemini_model = gemini_model     

    @Slot()
    def process(self):
        try:
            prompt =  f'''Please explain this American crossword clue to me. The clue is "{self.clue}" and the answer is "{self.answer}"'''
            # response = self.client.chat.completions.create(
            #     model="gpt-5-mini",
            #     messages=[{"role": "user", "content": prompt}]
            # )
            #self.layout.addWidget(QLabel(response.choices[0].message.content))
            response = self.gemini_model.generate_content(prompt) 
            self.finished.emit(response.text)
        except:
            self.finished.emit("Error")






