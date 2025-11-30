import datetime
import json
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout
from PySide6.QtCore import QSettings
import calendar
from pathlib import Path

class stats_tab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.average_time_all_time = QLabel()
        # averages_times[0] would be your average for mondays
        self.average_times_labels = [QLabel() for _ in range(7)] 
        average_times_layout = QGridLayout()
        for i, name in enumerate(list(calendar.day_name)):
            average_times_layout.addWidget(QLabel(name), 0, i)
            average_times_layout.addWidget(self.average_times_labels[i], 1, i)
        self.puzzles_completed = QLabel()
        self.puzzles_started_but_not_completed = QLabel()
        self.not_attempted = QLabel()
        self.number_of_puzzles = QLabel()
        self.getStats()

        layout.addWidget(self.average_time_all_time)
        layout.addLayout(average_times_layout)
        layout.addWidget(self.puzzles_completed)
        layout.addWidget(self.number_of_puzzles)
        layout.addWidget(self.puzzles_started_but_not_completed)
        layout.addWidget(self.not_attempted)

        self.setLayout(layout)
    
    def getStats(self):
        settings = QSettings("KrossWordz", "KrossWordz")
        directory = Path( settings.value("puzzles_dir") )
        puzzles_completed = 0
        started_but_not_completed = 0
        number_of_puzzles = 0
        average_time_all_time = 0
        count = 1
        average_times = [0 for _ in range(7)]
        counts = [1 for _ in range(7)]
        for file in directory.iterdir():
            if file.name.endswith(".ipuz"):
                number_of_puzzles += 1
            elif file.name.endswith(".json"):
                puzzle_info = json.loads(file.read_text())
                if puzzle_info.get("puzzle_solved"):
                    puzzles_completed += 1
                    dt = datetime.datetime.strptime(file.name.split('.')[0], "%m:%d:%Y").date()
                    time = int(puzzle_info["current_timer"].split(":")[0]) * 60 + int(puzzle_info["current_timer"].split(":")[1])
                    average_times[dt.weekday()] += (1/(counts[dt.weekday()])) * (time - average_times[dt.weekday()])
                    average_time_all_time += ( 1/count ) * (time - average_time_all_time)
                    count += 1
                    counts[dt.weekday()] += 1
                else:
                    started_but_not_completed += 1
        not_attempted = number_of_puzzles - puzzles_completed - started_but_not_completed

        self.puzzles_completed.setText(f"Puzzles completed: {puzzles_completed}")
        self.puzzles_started_but_not_completed.setText(f"Puzzles started but not completed: {started_but_not_completed}")
        self.not_attempted.setText(f"Not attempted: {not_attempted}")
        self.number_of_puzzles.setText(f"Number of puzzles: {number_of_puzzles}")
        for i in range(7):
            #self.average_times_labels[i].setText("{:.2f}".format(average_times[i]))
            self.average_times_labels[i].setText(str(datetime.timedelta(seconds=average_times[i])))
        #self.average_time_all_time.setText("Average time among all puzzles: {:.2f}".format(average_time_all_time))
        self.average_time_all_time.setText("Average time among all puzzles: {}".format(str(datetime.timedelta(seconds=average_time_all_time))))
