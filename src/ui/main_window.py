import os
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QAction, QFont, QIcon, QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from services.file_loader import FileLoaderService
from ui.clues_panel import CluesPanel
from ui.crossword_widget import KrossWordWidget
from ui.tab_event_filter import TabEventFilter

class MainWindow(QMainWindow):
    """Main application window"""

    _ICON_BUTTON_STYLESHEET = (
        "QPushButton { background-color: transparent; border: none; color: white; padding: 0; border-radius: 8px; }"
        "QPushButton:hover { background-color: rgba(255, 255, 255, 0.12); color: white; }"
        "QPushButton:pressed { background-color: rgba(255, 255, 255, 0.2); color: white; }"
        "QPushButton:disabled { background-color: transparent; color: rgba(255, 255, 255, 0.4); }"
    )

    _ICON_BUTTON_ACTIVE_STYLESHEET = (
        "QPushButton { background-color: rgba(255, 255, 255, 0.28); border: none; color: white; padding: 0; border-radius: 8px; }"
        "QPushButton:hover { background-color: rgba(255, 255, 255, 0.35); color: white; }"
        "QPushButton:pressed { background-color: rgba(255, 255, 255, 0.45); color: white; }"
        "QPushButton:disabled { background-color: rgba(255, 255, 255, 0.18); color: rgba(255, 255, 255, 0.6); }"
    )

    def __init__(self):
        super().__init__()
        self.file_loader_service = FileLoaderService()
        self.current_puzzle = None
        self.elapsed_seconds = 0
        self.timer_running = False
        self.init_ui()
        self.puzzle_timer = QTimer(self)
        self.puzzle_timer.setInterval(1000)
        self.puzzle_timer.timeout.connect(self._update_timer_display)
        # Create and install global event filter for tab key handling
        self.tab_event_filter = TabEventFilter(self.crossword_widget)
        QApplication.instance().installEventFilter(self.tab_event_filter)
        print("DEBUG: Global tab event filter installed")

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()

        # Create File menu
        file_menu = menubar.addMenu("File")

        load_action = QAction("Load Puzzle", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_puzzle)
        file_menu.addAction(load_action)

        save_action = QAction("Save Progress", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_progress)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Create Check menu
        check_menu = menubar.addMenu("Check")

        check_letter_action = QAction("Check Letter", self)
        check_letter_action.triggered.connect(self.check_current_letter)
        check_menu.addAction(check_letter_action)

        check_word_action = QAction("Check Word", self)
        check_word_action.triggered.connect(self.check_current_word)
        check_menu.addAction(check_word_action)

        check_puzzle_action = QAction("Check Puzzle", self)
        check_puzzle_action.triggered.connect(self.check_answers)
        check_menu.addAction(check_puzzle_action)

        reveal_menu = menubar.addMenu("Reveal")

        reveal_letter_action = QAction("Reveal Letter", self)
        reveal_letter_action.triggered.connect(self.reveal_current_letter)
        reveal_menu.addAction(reveal_letter_action)

        reveal_word_action = QAction("Reveal Word", self)
        reveal_word_action.triggered.connect(self.reveal_current_word)
        reveal_menu.addAction(reveal_word_action)

        reveal_puzzle_action = QAction("Reveal Puzzle", self)
        reveal_puzzle_action.triggered.connect(self.reveal_answers)
        reveal_menu.addAction(reveal_puzzle_action)


    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KrossWordz - Crossword Puzzle App")
        self.showMaximized() # Make window fullscreen

        # Create menu bar
        self.create_menu_bar()

        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setSpacing(-1)
        layout.setContentsMargins(-1, -1, -1, -1)

        # Left panel: Crossword and current clue
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(-1)
        left_layout.setContentsMargins(-1, -1, -1, -1)

        # Timer display above current clue
        timer_row = QHBoxLayout()
        timer_row.setAlignment(Qt.AlignVCenter)
        timer_row.setContentsMargins(-1, -1, -1, -1)
        timer_row.setSpacing(-1)
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.timer_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        timer_row.addWidget(self.timer_label)

        icon_size = QSize(24, 24)

        self.pause_button = QPushButton()
        pause_icon = self._create_colored_icon(
            self.style().standardIcon(QStyle.SP_MediaPause), QColor(Qt.white), icon_size
        )
        self.pause_button.setIcon(pause_icon)
        self.pause_button.setFixedSize(36, 36)
        self.pause_button.setToolTip("Pause timer")
        self.pause_button.setEnabled(False)
        self.pause_button.setVisible(False)
        self.pause_button.clicked.connect(self.pause_puzzle_timer)
        self._style_icon_button(self.pause_button)
        timer_row.addWidget(self.pause_button)

        self.resume_button = QPushButton()
        resume_icon = self._create_colored_icon(
            self.style().standardIcon(QStyle.SP_MediaPlay), QColor(Qt.white), icon_size
        )
        self.resume_button.setIcon(resume_icon)
        self.resume_button.setFixedSize(36, 36)
        self.resume_button.setToolTip("Resume timer")
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(False)
        self.resume_button.clicked.connect(self.resume_puzzle_timer)
        self._style_icon_button(self.resume_button)
        timer_row.addWidget(self.resume_button)

        self.pencil_button= QPushButton()
        project_root = Path(__file__).resolve().parents[2]
        pencil_icon_path = project_root / "assets" / "icons" / "mdi--pencil.svg"
        pencil_icon = self._create_colored_icon(
            QIcon(str(pencil_icon_path)), QColor(Qt.white), icon_size
        )
        self.pencil_button.setIcon(pencil_icon)
        self.pencil_button.setFixedSize(36, 36)
        self.pencil_button.setToolTip("Enable/disable pencil mode")
        self.pencil_button.setEnabled(True)
        self.pencil_button.setVisible(True)
        self.pencil_button.clicked.connect(self.set_pencil_mode)
        self._style_icon_button(self.pencil_button)
        timer_row.addWidget(self.pencil_button)



        timer_row.addStretch()
        left_layout.addLayout(timer_row)

        # Current clue display above crossword
        self.current_clue_label = QLabel("Select a cell to see clue")
        self.current_clue_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.current_clue_label.setWordWrap(True)
        self.current_clue_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        #self.current_clue_label.setMinimumHeight(30)
        left_layout.addWidget(self.current_clue_label)

        # Crossword grid
        self.crossword_widget = KrossWordWidget()
        self.crossword_widget.cell_selected.connect(self.on_cell_selected)
        self.crossword_widget.value_changed.connect(self.raise_updated_signal)
        self.crossword_widget.pencil_mode_toggle_requested.connect(self.set_pencil_mode)
        self.crossword_widget.setFocusPolicy(Qt.StrongFocus)  # Make sure it can receive key events
        left_layout.addWidget(self.crossword_widget)
        left_layout.setStretchFactor(self.crossword_widget, 1)

        # Right panel: puzzle info, clues, and actions
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(-1)
        right_layout.setContentsMargins(-1, -1, -1, -1)

        self.title_label = QLabel("No puzzle loaded")
        self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.title_label.setWordWrap(True)
        right_layout.addWidget(self.title_label)

        self.author_label = QLabel("")
        self.author_label.setFont(QFont("Arial", 11))
        self.author_label.setWordWrap(True)
        right_layout.addWidget(self.author_label)

        right_layout.addSpacing(10)

        self.clues_panel = CluesPanel()
        right_layout.addWidget(self.clues_panel)
        right_layout.setStretchFactor(self.clues_panel, 1)

        right_layout.addStretch()

        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        layout.setStretch(0, 3)
        layout.setStretch(1, 2)

    def _style_icon_button(self, button: QPushButton) -> None:
        """Apply a transparent style for icon-only buttons."""
        button.setFlat(True)
        button.setStyleSheet(self._ICON_BUTTON_STYLESHEET)
        button.setIconSize(QSize(24, 24))
        button.setContentsMargins(0, 0, 0, 0)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def _create_colored_icon(self, icon: QIcon, color: QColor, size: QSize) -> QIcon:
        """Return a tinted copy of the provided icon."""
        pixmap = icon.pixmap(size)
        if pixmap.isNull():
            return icon

        tinted_pixmap = self._tint_pixmap(pixmap, color)
        tinted_pixmap.setDevicePixelRatio(pixmap.devicePixelRatio())

        tinted_icon = QIcon()
        for mode in (QIcon.Normal, QIcon.Active, QIcon.Disabled):
            tinted_icon.addPixmap(tinted_pixmap, mode, QIcon.Off)
        return tinted_icon

    def _tint_pixmap(self, source: QPixmap, color: QColor) -> QPixmap:
        """Apply a color tint to a pixmap using source-in compositing."""
        ratio = source.devicePixelRatio()
        tinted = QPixmap(source.size())
        tinted.setDevicePixelRatio(ratio)
        tinted.fill(Qt.transparent)
        painter = QPainter(tinted)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawPixmap(0, 0, source)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), color)
        painter.end()
        return tinted

    def load_puzzle(self):
        """Load a puzzle using a file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load .ipuz Puzzle", "", "IPUZ Files (*.ipuz);;All Files (*)"
        )

        if file_path:
            self.load_puzzle_from_path(file_path)

    def load_puzzle_from_path(self, file_path: str, show_error_dialog: bool = True) -> bool:
        """Load a puzzle from an explicit filesystem path"""
        if not file_path:
            return False

        normalized_path = os.path.abspath(os.path.expanduser(file_path))

        try:
            self.current_puzzle = self.file_loader_service.load_ipuz_file(normalized_path)
            self.crossword_widget.set_puzzle(self.current_puzzle)
            self.update_clues_display()
            self.update_title_label()
            self.start_puzzle_timer()
            return True
        except Exception as e:
            if show_error_dialog:
                QMessageBox.warning(self, "Error", f"Failed to load puzzle:\n{e}")
            else:
                print(f"Failed to load puzzle from {normalized_path}: {e}")
            return False

    def save_progress(self):
        """Save current progress"""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "No puzzle loaded to save")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Progress", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                # Convert to serializable format
                puzzle_data = {
                    'title': self.current_puzzle.title,
                    'author': self.current_puzzle.author,
                    'grid': []
                }

                for row in self.current_puzzle.cells:
                    row_data = []
                    for cell in row:
                        if cell.is_black:
                            row_data.append('#')
                        else:
                            cell_data = {'solution': cell.solution, 'user_input': cell.user_input}
                            if cell.clue_number:
                                cell_data['number'] = cell.clue_number
                            row_data.append(cell_data)
                    puzzle_data['grid'].append(row_data)

                import json
                with open(file_path, 'w') as f:
                    json.dump(puzzle_data, f, indent=2)

            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save progress: {e}")

    def reveal_answers(self):
        """Reveal current answers"""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "No puzzle loaded to reveal")
            return
        for row in self.current_puzzle.cells:
            for cell in row:
                if not cell.is_black and cell.solution:
                    cell.reveal()
        self.crossword_widget.update()

    def set_pencil_mode(self):
        """Toggle pencil mode and update button styling."""
        pencil_mode = self.crossword_widget.set_pencil_mode()
        stylesheet = (
            self._ICON_BUTTON_ACTIVE_STYLESHEET
            if pencil_mode
            else self._ICON_BUTTON_STYLESHEET
        )
        self.pencil_button.setStyleSheet(stylesheet)

    def start_puzzle_timer(self):
        """Start or restart the elapsed time display."""
        if self.puzzle_timer.isActive():
            self.puzzle_timer.stop()
        self.elapsed_seconds = 0
        self.timer_label.setText("00:00")
        self.puzzle_timer.start()
        self.timer_running = True
        self.pause_button.setEnabled(True)
        self.pause_button.setVisible(True)
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(False)

    def stop_puzzle_timer(self, reset_display: bool = False):
        """Stop the elapsed time display."""
        self.puzzle_timer.stop()
        self.timer_running = False
        self.pause_button.setEnabled(False)
        self.pause_button.setVisible(False)
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(False)
        if reset_display:
            self.elapsed_seconds = 0
            self.timer_label.setText("00:00")

    def _update_timer_display(self):
        """Advance the timer label each second while active."""
        self.elapsed_seconds += 1
        minutes, seconds = divmod(self.elapsed_seconds, 60)
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def pause_puzzle_timer(self):
        """Pause the puzzle timer without resetting elapsed time."""
        if not self.timer_running:
            return
        self.puzzle_timer.stop()
        self.timer_running = False
        self.pause_button.setEnabled(False)
        self.pause_button.setVisible(False)
        self.resume_button.setEnabled(True)
        self.resume_button.setVisible(True)

    def resume_puzzle_timer(self):
        """Resume the puzzle timer if it was paused."""
        if self.timer_running:
            return
        self.puzzle_timer.start()
        self.timer_running = True
        self.pause_button.setEnabled(True)
        self.pause_button.setVisible(True)
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(False)

    def check_answers(self):
        """Check current answers"""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "No puzzle loaded to check")
            return
        for row in self.current_puzzle.cells:
            for cell in row:
                if not cell or cell.is_black or not cell.user_input:
                    continue
                if cell.is_correct():
                    cell.correct = True
                else:
                    cell.incorrect = True

        self.crossword_widget.update()

    def check_current_letter(self):
        """Verify the currently selected letter."""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "Load a puzzle before checking letters")
            return
        cell = self.crossword_widget.get_current_cell()
        if not cell or cell.is_black or not cell.user_input:
            return
        if cell.is_correct():
            cell.correct = True
        else:
            cell.incorrect = True
        self.crossword_widget.update()

    def reveal_current_letter(self):
        """Reveal the currently selected letter."""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "Load a puzzle before revealing letters")
            return
        cell = self.crossword_widget.get_current_cell()
        if not cell or cell.is_black:
            return
        cell.reveal()
        self.crossword_widget.update()

    def reveal_current_word(self):
        """Reveal the word that contains the currently selected cell."""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "Load a puzzle before revealing words")
            return
        position = self.crossword_widget.get_current_position()
        if not position:
            return
        word_cells = self.crossword_widget.get_current_word_coordinates()
        for cell_row, cell_col in word_cells:
            cell = self.current_puzzle.cells[cell_row][cell_col]
            if cell.is_black:
                continue
            cell.reveal()
        self.crossword_widget.update()

    def check_current_word(self):
        """Verify the word that contains the currently selected cell."""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "Load a puzzle before checking words")
            return
        position = self.crossword_widget.get_current_position()
        if not position:
            return
        word_cells = self.crossword_widget.get_current_word_coordinates()
        for cell_row, cell_col in word_cells:
            cell = self.current_puzzle.cells[cell_row][cell_col]
            if cell.is_black:
                continue
            if not cell.user_input:
                continue
            if cell.is_correct():
                cell.correct = True
            else:
                cell.incorrect = True

        self.crossword_widget.update()

    def update_clues_display(self):
        """Update the clues display with separate across and down sections"""
        if not self.current_puzzle:
            self.clues_panel.clear()
            return

        # Update across clues
        across_text = ""
        for clue in sorted(self.current_puzzle.across_clues, key=lambda x: x.number):
            across_text += f"{clue.number}. {clue.text}\n\n"
        self.clues_panel.set_across_text(across_text.strip())

        # Update down clues
        down_text = ""
        for clue in sorted(self.current_puzzle.down_clues, key=lambda x: x.number):
            down_text += f"{clue.number}. {clue.text}\n\n"
        self.clues_panel.set_down_text(down_text.strip())

    def update_title_label(self):
        """Update the title label with puzzle info"""
        if not self.current_puzzle:
            self.title_label.setText("No puzzle loaded")
            self.author_label.setText("")
            return

        self.title_label.setText(self.current_puzzle.title)
        author_text = f"by {self.current_puzzle.author}" if self.current_puzzle.author else ""
        self.author_label.setText(author_text)

    def on_cell_selected(self, row, col):
        """Handle cell selection events"""
        print(f"Cell selected: ({row}, {col})")
        cell = self.current_puzzle.cells[row][col] if self.current_puzzle else None
        print(f"Cell has clue_number: {cell.clue_number if cell else 'None'}")

        # Always update current clue display, regardless of whether cell has a number
        self._update_current_clue_display(row, col)


    def _has_cell_in_direction(self, row, col, direction):
        """Check if a cell is part of a clue in the given direction"""
        clue_number = self.current_puzzle.cells[row][col].clue_number
        if not clue_number:
            return False

        clue = self.current_puzzle.get_clue(clue_number, direction)
        return clue is not None

    def raise_updated_signal(self):
        """Signal that the puzzle values were updated"""
        self.update_clues_display()  # Update any visual feedback

    def _update_current_clue_display(self, row, col):
        """Update the current clue display above the crossword"""
        if not self.current_puzzle:
            return

        print(f"Updating clue display for ({row}, {col})")
        print(f"Current highlight mode: {self.crossword_widget.highlight_mode}")

        cell = self.current_puzzle.cells[row][col]
        direction = ""

        # Get direction from current highlight mode
        if self.crossword_widget.highlight_mode == "across":
            direction = "across"
        elif self.crossword_widget.highlight_mode == "down":
            direction = "down"

        print(f"Direction: {direction}")
        print(f"Cell clue number: {cell.clue_number}")

        # Find the clue for this cell in the current direction
        clue = self._find_clue_for_cell(row, col, direction)

        if clue:
            clue_text = f"{direction.upper()}: {clue.text}"
            print(f"Found clue: {clue_text}")
        else:
            clue_text = ""
            print("No clue found for this cell")

        self.current_clue_label.setText(clue_text)

    def _find_clue_for_cell(self, row, col, direction):
        """Find the clue for a cell even if it doesn't have a number"""
        if not self.current_puzzle:
            return None

        # Always find the start of the word this cell belongs to
        # This ensures we get the correct clue for the current direction
        start_row, start_col = self._find_word_start(row, col, direction)

        if start_row is not None and start_col is not None:
            start_cell = self.current_puzzle.cells[start_row][start_col]
            if start_cell.clue_number:
                return self.current_puzzle.get_clue(start_cell.clue_number, direction)

        # Fallback: try to get clue directly from cell number
        if self.current_puzzle.cells[row][col].clue_number:
            return self.current_puzzle.get_clue(
                self.current_puzzle.cells[row][col].clue_number,
                direction
            )

        return None

    def _find_word_start(self, row, col, direction):
        """Find the starting cell of a word in the given direction"""
        if direction == "across":
            # Find leftmost cell in the same row
            start_col = col
            # Move left until we hit a black cell or the beginning of the puzzle
            while start_col > 0:
                if self.current_puzzle.cells[row][start_col - 1].is_black:
                    break
                start_col -= 1
            return row, start_col
        else:  # down
            # Find topmost cell in the same column
            start_row = row
            # Move up until we hit a black cell or the beginning of the puzzle
            while start_row > 0:
                if self.current_puzzle.cells[start_row - 1][col].is_black:
                    break
                start_row -= 1
            return start_row, col
