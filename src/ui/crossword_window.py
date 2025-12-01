
import json
from pathlib import Path
from ui.check_and_reveal import Check_and_Reveal
from ui.SelectableLabel import SelectableLabel
from ui.current_clue_widget import Current_Clue_Widget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QColor
from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)
from ui.clues_panel import CluesPanel
from ui.crossword_widget import KrossWordWidget
from shiboken6 import isValid


def timer_row(window):
    # Timer display above current clue

    if window.left_panel and isValid(window.left_panel):
        return

    window.left_panel = QWidget()
    window.left_layout = QVBoxLayout(window.left_panel)
    window.left_layout.setSpacing(-1)
    window.left_layout.setContentsMargins(-1, -1, -1, -1)
    window.layout.addWidget(window.left_panel)

    window.timer_row = QHBoxLayout()
    window.timer_row.setAlignment(Qt.AlignVCenter)
    window.timer_row.setContentsMargins(-1, -1, -1, -1)
    window.timer_row.setSpacing(-1)

    icon_size = QSize(24, 24)

    window.back_button = QPushButton()
    project_root = Path(__file__).resolve().parents[2]
    back_icon_path = project_root / "assets" / "icons" / "calendar-icon.svg"
    back_icon = window._create_colored_icon(QIcon(str(back_icon_path)), QColor(Qt.white), icon_size)
    window.back_button.setIcon(back_icon)
    window.back_button.setFixedSize(36, 36)
    window.back_button.setToolTip("Go to calendar")
    window.back_button.setEnabled(False)
    window.back_button.setVisible(False)
    window.back_button.clicked.connect(window.back_to_calendar)
    window._style_icon_button(window.back_button)
    window.timer_row.addWidget(window.back_button)


    window.timer_label = QLabel("00:00")
    window.timer_label.setFont(QFont("Arial", 12, QFont.Bold))
    window.timer_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
    window.timer_row.addWidget(window.timer_label)


    window.pause_button = QPushButton()
    pause_icon = window._create_colored_icon(
        window.style().standardIcon(QStyle.SP_MediaPause), QColor(Qt.white), icon_size
    )
    window.pause_button.setIcon(pause_icon)
    window.pause_button.setFixedSize(36, 36)
    window.pause_button.setToolTip("Pause timer")
    window.pause_button.setEnabled(False)
    window.pause_button.setVisible(False)
    window.pause_button.clicked.connect(window.pause_puzzle_timer)
    window._style_icon_button(window.pause_button)
    window.timer_row.addWidget(window.pause_button)

    window.resume_button = QPushButton()
    resume_icon = window._create_colored_icon(
        window.style().standardIcon(QStyle.SP_MediaPlay), QColor(Qt.white), icon_size
    )
    window.resume_button.setIcon(resume_icon)
    window.resume_button.setFixedSize(36, 36)
    window.resume_button.setToolTip("Resume timer")
    window.resume_button.setEnabled(False)
    window.resume_button.setVisible(False)
    window.resume_button.clicked.connect(window.resume_puzzle_timer)
    window._style_icon_button(window.resume_button)
    window.timer_row.addWidget(window.resume_button)

    window.pencil_button= QPushButton()
    project_root = Path(__file__).resolve().parents[2]
    pencil_icon_path = project_root / "assets" / "icons" / "mdi--pencil.svg"
    pencil_icon = window._create_colored_icon(
        QIcon(str(pencil_icon_path)), QColor(Qt.white), icon_size
    )

    window.pencil_button.setIcon(pencil_icon)
    window.pencil_button.setFixedSize(36, 36)
    window.pencil_button.setToolTip("Enable/disable pencil mode")
    window.pencil_button.setEnabled(False)
    window.pencil_button.setVisible(False)
    window.pencil_button.clicked.connect(window.set_pencil_mode)
    window._style_icon_button(window.pencil_button)
    window.timer_row.addWidget(window.pencil_button)

    window.cells_filled = QLabel()
    window.cells_filled.setToolTip("Ratio of cells filled")
    window.cells_filled.setVisible(False)
    window.timer_row.addWidget(window.cells_filled)

    window.timer_row.addStretch()
    window.left_layout.addLayout(window.timer_row)


def load_puzzle(window, normalized_path: str):
    window.current_puzzle = window.file_loader_service.load_ipuz_file(normalized_path)
    window.current_puzzle_path = normalized_path
    
    if not window.current_clue_widget or not isValid(window.current_clue_widget):
        window.current_clue_widget = Current_Clue_Widget()
        window.left_layout.addWidget(window.current_clue_widget)

    if not window.crossword_widget or not isValid(window.crossword_widget):
        window.crossword_widget = KrossWordWidget()
        # Crossword grid
        window.crossword_widget.cell_selected.connect(window.on_cell_selected)
        window.crossword_widget.value_changed.connect(window.raise_updated_signal)
        window.crossword_widget.display_message.connect(window.display_message)
        window.crossword_widget.cell_count_changed.connect(window.on_cell_count_changed)
        window.crossword_widget.request_clue_explanation.connect(window.ai_page.explain_clue)
        window.crossword_widget.resize_current_clue.connect(window.current_clue_widget.resize)

        window.crossword_widget.pencil_mode_toggle_requested.connect(window.set_pencil_mode)
        window.crossword_widget.setFocusPolicy(Qt.StrongFocus)  # Make sure it can receive key events
        window.left_layout.addWidget(window.crossword_widget)
        window.left_layout.setStretchFactor(window.crossword_widget, 1)

    window.crossword_widget.set_puzzle(window.current_puzzle)

    window.check_and_reveal = Check_and_Reveal(window.crossword_widget, window.current_puzzle)
    
    window.check_letter_action.triggered.connect(window.check_and_reveal.check_current_letter) 
    window.check_letter_action.setEnabled(True)

    window.check_word_action.triggered.connect(window.check_and_reveal.check_current_word)
    window.check_word_action.setEnabled(True)

    window.check_puzzle_action.triggered.connect(window.check_and_reveal.check_answers)
    window.check_puzzle_action.setEnabled(True)

    window.reveal_letter_action.triggered.connect(window.check_and_reveal.reveal_current_letter)
    window.reveal_letter_action.setEnabled(True)

    window.reveal_word_action.triggered.connect(window.check_and_reveal.reveal_current_word)
    window.reveal_word_action.setEnabled(True)

    window.reveal_puzzle_action.triggered.connect(window.check_and_reveal.reveal_answers)
    window.reveal_puzzle_action.setEnabled(True)

    if window.right_panel and isValid(window.right_panel):
        window.layout.removeWidget(window.right_panel)
        window.right_panel.setParent(None)
        window.right_panel.deleteLater()

    window.right_panel = QWidget()
    right_layout = QVBoxLayout()
    right_layout.setSpacing(-1)
    right_layout.setContentsMargins(-1, -1, -1, -1)
    window.right_panel.setLayout(right_layout)
    
    window.title_layout = QHBoxLayout()
    right_layout.addLayout(window.title_layout)

    window.title_label = QLabel("No puzzle loaded")
    window.title_label.setFont(QFont("Arial", 16, QFont.Bold))
    window.title_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

    window.date_label = QLabel("")
    window.date_label.setFont(QFont("Arial", 11))
    window.date_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
    window.date_label.setStyleSheet("color: grey;")

    window.title_layout.addWidget(window.title_label)
    window.title_layout.addSpacing(5)
    window.title_layout.addWidget(window.date_label)
    window.title_layout.setAlignment(window.date_label, Qt.AlignBottom)

    window.title_layout.addStretch()

    info_layout = QHBoxLayout()
    right_layout.addLayout(info_layout)
    window.author_label = QLabel("")
    window.author_label.setFont(QFont("Arial", 11))
    window.author_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

    window.editor_label = QLabel("")
    window.editor_label.setFont(QFont("Arial", 11))
    window.editor_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

    info_layout.setSpacing(0)
    info_layout.addWidget(window.author_label)
    info_layout.addSpacing(5)
    circle = QLabel("\N{BLACK CIRCLE}")
    circle.setFont(QFont(circle.font().family(), 5))
    info_layout.addWidget(circle)
    info_layout.addSpacing(5)

    info_layout.addWidget(window.editor_label)
    info_layout.addStretch()
    right_layout.addSpacing(10)

    window.clues_panel = CluesPanel(window.crossword_widget.puzzle.across_clues, window.crossword_widget.puzzle.down_clues, window.right_panel)
    window.clues_panel.clue_selected.connect(window.on_clue_selected)

    right_layout.addWidget(window.clues_panel)
    right_layout.setStretchFactor(window.clues_panel, 1)

    window.check_and_reveal.grey_all_clues.connect(window.clues_panel.grey_all_clues)

    right_layout.addStretch()
    window.layout.addWidget(window.right_panel)
    
    window.pencil_button.setVisible(True)
    window.pencil_button.setEnabled(True)

    window.back_button.setVisible(True)
    window.back_button.setEnabled(True)

    window.check_word_action.setEnabled(True)
    window.check_letter_action.setEnabled(True)
    window.reveal_word_action.setEnabled(True)
    window.reveal_letter_action.setEnabled(True)

    window.check_puzzle_action.setEnabled(True)

    window.crossword_widget.cells_filled = window.current_puzzle.initial_filled_cells

    window.cells_filled.setText(f"{window.crossword_widget.cells_filled}/{window.current_puzzle.fillable_cell_count}")
    window.cells_filled.setVisible(True)

    window.update_title_label()

    window.start_puzzle_timer()

    progress = Path(normalized_path).with_suffix(".json")
    if progress.exists():
        load_previous_progress(window, window.crossword_widget, progress)

    window._update_current_clue_display(window.crossword_widget.selected_row, window.crossword_widget.selected_col)
    window._update_clues_highlight(window.crossword_widget.selected_row, window.crossword_widget.selected_col)

    window.crossword_widget.greyout_clue.connect(window.clues_panel.greyout_text)


def load_previous_progress(window, crossword_widget, normalized_path):
    with open(normalized_path, "r") as f:
        progress = json.load(f)
        crossword_widget.selected_row, crossword_widget.selected_col = progress["current_position"]
        crossword_widget.highlight_mode = progress["highlight_mode"]
        crossword_widget.puzzle_solved = progress["puzzle_solved"]
        if progress["pencil_mode"]:
            window.set_pencil_mode()

        window.timer_label.setText(progress["current_timer"])
        window.elapsed_seconds = int(progress["current_timer"].split(":")[0]) * 60 + int(progress["current_timer"].split(":")[1])
        
        if not progress["timer_running"]:
            window.pause_puzzle_timer()

        for revealed_squares in progress["revealed_coordinates"]:
            crossword_widget.puzzle.cells[revealed_squares[0]][revealed_squares[1]].revealed = True
        for corrected_squares in progress["corrected_coordinates"]:
            crossword_widget.puzzle.cells[corrected_squares[0]][corrected_squares[1]].corrected = True
        for incorrect_squares in progress["incorrect_coordinates"]:
            crossword_widget.puzzle.cells[incorrect_squares[0]][incorrect_squares[1]].incorrect = True
        for pencilled_squares in progress["pencilled_coordinates"]:
            crossword_widget.puzzle.cells[pencilled_squares[0]][pencilled_squares[1]].pencilled = True
