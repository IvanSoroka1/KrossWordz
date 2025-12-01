import calendar

import datetime
import json
from PySide6.QtWidgets import QLayout, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, QGraphicsColorizeEffect
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, QSettings, Signal, QFileSystemWatcher
from PySide6.QtGui import QColor

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
        yearCombo.currentTextChanged.connect(lambda text: self.dateChanged(calendar.month_name[self.month], text))

        self.watcher = QFileSystemWatcher(self)
        settings = QSettings("KrossWordz", "KrossWordz")
        self.watcher.addPath(settings.value("puzzles_dir"))

        self.watcher.directoryChanged.connect(lambda path: self.dateChanged(calendar.month_name[self.month], self.year))
    
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
        calendar_layout.setVerticalSpacing(0)
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

        # how do you account for months with two digits or one? E.g what if you used 09 instead of 9 for september. (same thing for dates)
        self.file = f"{self.directory}/{month}:{day}:{year}.ipuz".format(month=month, day=day, year=year) 

        self.image = QSvgWidget(str(crossword_icon_path))
        self.image.setFixedSize(32, 32)   # pick a size you like

        if not Path(self.file).exists():
            effect = QGraphicsColorizeEffect(self.image)
            effect.setColor(QColor("gray"))   # tint color
            effect.setStrength(0.8)           # 0..1 intensity
            self.image.setGraphicsEffect(effect) 
            self.image.setCursor(Qt.CursorShape.ForbiddenCursor)
            self.clickable = False
        else:
            self.image.setCursor(Qt.CursorShape.PointingHandCursor)
            self.clickable = True
    
        self.date = QLabel(str(day))
        self.date.setStyleSheet("font-weight: bold")
        layout.addWidget(self.image, alignment= Qt.AlignHCenter)
        layout.addWidget(self.date, alignment=Qt.AlignHCenter)
        progressFile = Path(self.file).with_suffix(".json")

        percent_label = QLabel(alignment=Qt.AlignHCenter)
        time_label = QLabel(alignment=Qt.AlignHCenter)
        time_label.setStyleSheet(f"font-size: 8pt;")
        time_label.setContentsMargins(0, 0, 0, 0)
        percent_label.setStyleSheet(f"font-size: 8pt;")
        percent_label.setContentsMargins(0, 0, 0, 0)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)

        if progressFile.exists():
            with open(progressFile, "r") as f:
                progress = json.load(f)
                time_label.setText(progress["current_timer"])
                percent_label.setText(f"{progress["percent_accomplished"]*100: .2f} %")
                solved = progress["puzzle_solved"]
                color = "" if not solved else "color: green;"
                percent_label.setStyleSheet(f"font-size: 8pt;{color}")

        info_layout.addWidget(percent_label)
        info_layout.addWidget(time_label)

        layout.addLayout(info_layout)


        self.setLayout(layout)
    
    
    def mousePressEvent(self, event):
        # Only treat clicks on the icon itself as a valid click
        if self.clickable and event.button() == Qt.LeftButton and self.image.geometry().contains(event.position().toPoint()):
            self.loadPuzzle.emit(self.file)
        return super().mousePressEvent(event)





         
