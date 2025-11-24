import calendar

import datetime
from PySide6.QtWidgets import QLayout, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, QSettings, Signal

from pathlib import Path

class Calendar(QWidget):
    loadPuzzle = Signal(str)
    def __init__(self):
        super().__init__()
        today = datetime.date.today()
        self.month = today.month
        self.year = today.year

        monthCombo = QComboBox()
        monthCombo.addItems(month for month in calendar.month_name if month)
        yearCombo = QComboBox()
        yearCombo.addItems(str(year) for year in range(self.year, 1940-1, -1))


        idx = monthCombo.findText(calendar.month_name[self.month])
        if idx != -1:
            monthCombo.setCurrentIndex(idx)

        combo_layout = QHBoxLayout()
        combo_layout.addWidget(monthCombo)
        combo_layout.addWidget(yearCombo)

        self.mainlayout = QVBoxLayout()
        self.mainlayout.addLayout(combo_layout)
        self.calendarLayout = self.getCalendarLayout()
        self.mainlayout.addLayout(self.calendarLayout)
        self.setLayout(self.mainlayout)

        monthCombo.currentTextChanged.connect(lambda text: self.dateChanged( text, self.year))
        yearCombo.currentTextChanged.connect(lambda text: self.dateChanged( self.month, text))
    
    def dateChanged(self, month, year):
        self.mainlayout.removeItem(self.calendarLayout)
        self.calendarLayout.setParent(None)
        while self.calendarLayout.count():
            item = self.calendarLayout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)  # or w.deleteLater()

        self.month = list(calendar.month_name).index(month)
        self.year = int(year)
        self.calendarLayout = self.getCalendarLayout()
        self.mainlayout.addLayout(self.calendarLayout)

    def getCalendarLayout(self):
        calendar_layout = QGridLayout()
        calendar_layout.setSizeConstraint(QLayout.SetFixedSize)
        counts = dict()
        for i in range(7):
            counts[i] = 1

        cal = calendar.Calendar(firstweekday=6)  
        for i, weekday in enumerate(['S', 'M', 'T', 'W', 'T', 'F', 'S']):
            calendar_layout.addWidget(QLabel(weekday), 0, i, alignment=Qt.AlignHCenter)
        for date in cal.itermonthdates(self.year, self.month):
            weekday = (date.weekday()+1)%7
            if date.month == self.month:# skip leading/trailing days from adjacent months
                dateBox = DateBox(self.month, date.day, self.year)
                dateBox.loadPuzzle.connect(self.loadPuzzle)
                calendar_layout.addWidget(dateBox, counts[weekday], weekday)
                counts[weekday] += 1
            else:
                 counts[weekday] += 1
        
        return calendar_layout



class DateBox(QWidget):
    loadPuzzle =  Signal(str)
    def __init__(self, month, day, year):
        super().__init__()
        layout = QVBoxLayout()
        
        project_root = Path(__file__).resolve().parents[2]
        crossword_icon_path = project_root / "assets" / "icons" / "square.svg"

        settings = QSettings("KrossWordz", "KrossWordz")
        self.directory = settings.value("puzzles_dir")
        
        
        self.image = QSvgWidget(str(crossword_icon_path))
        self.image.setFixedSize(32, 32)   # pick a size you like

        self.date = QLabel(str(day))
        layout.addWidget(self.image, alignment= Qt.AlignHCenter)
        layout.addWidget(self.date, alignment=Qt.AlignHCenter)

        self.setLayout(layout)

        # how do you account for months with two digits or one? E.g what if you used 09 instead of 9 for september. (same thing for dates)
        self.file_name = "{month}:{day}:{year}".format(month=month, day=day, year=year) 

    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.loadPuzzle.emit(f"{self.directory}/{self.file_name}.ipuz")
        return super().mousePressEvent(event)





         
