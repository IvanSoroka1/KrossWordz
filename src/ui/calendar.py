import calendar

import datetime
from PySide6.QtWidgets import QLayout, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, QSettings, Signal

from pathlib import Path

class Calendar(QWidget):
    loadPuzzle = Signal(str)
    def __init__(self):
        super().__init__()
        today = datetime.date.today()
        month = today.month
        year = today.year

        calendar_layout = QGridLayout()
        calendar_layout.setSizeConstraint(QLayout.SetFixedSize)
        counts = dict()
        for i in range(7):
            counts[i] = 1

        cal = calendar.Calendar(firstweekday=6)  
        for i, weekday in enumerate(['S', 'M', 'T', 'W', 'T', 'F', 'S']):
            calendar_layout.addWidget(QLabel(weekday), 0, i, alignment=Qt.AlignHCenter)
        for date in cal.itermonthdates(year, month):
            weekday = (date.weekday()+1)%7
            if date.month == month:# skip leading/trailing days from adjacent months
                dateBox = DateBox(month, date.day, year)
                dateBox.loadPuzzle.connect(self.loadPuzzle)
                calendar_layout.addWidget(dateBox, counts[weekday], weekday)
                counts[weekday] += 1
            else:
                 counts[weekday] += 1
        
        self.setLayout(calendar_layout)

    



class DateBox(QWidget):
    loadPuzzle =  Signal(str)
    def __init__(self, month, day, year):
        super().__init__()
        layout = QVBoxLayout()
        project_root = Path(__file__).resolve().parents[2]
        crossword_icon_path = project_root / "assets" / "icons" / "square.svg"

        self.image = QSvgWidget(str(crossword_icon_path))
        self.image.setFixedSize(32, 32)   # pick a size you like

        self.date = QLabel(str(day))
        layout.addWidget(self.image, alignment= Qt.AlignHCenter)
        layout.addWidget(self.date, alignment=Qt.AlignHCenter)

        self.setLayout(layout)

        settings = QSettings("KrossWordz", "KrossWordz")
        self.directory = settings.value("puzzles_dir")
        # how do you account for months with two digits or one? E.g what if you used 09 instead of 9 for september. (same thing for dates)
        self.file_name = "{month}:{day}:{year}".format(month=month, day=day, year=year) 


    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.loadPuzzle.emit(f"{self.directory}/{self.file_name}.ipuz")
        return super().mousePressEvent(event)





         
