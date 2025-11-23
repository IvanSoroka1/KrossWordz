import os
import traceback
import json
from pathlib import Path
from datetime import datetime
from ui.message_dialog import show_message
from ui.ai_windows import ai_window
from ui.check_and_reveal import Check_and_Reveal
from ui.SelectableLabel import SelectableLabel
from ui.current_clue_widget import Current_Clue_Widget
from PySide6.QtCore import Qt, QTimer, QSize, QSettings
from PySide6.QtGui import QAction, QFont, QIcon, QColor, QPainter, QPixmap, QPalette
from PySide6.QtWidgets import (
    QDialog,
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
    QTabWidget,
)
from ui.preferences import preferences

from services.file_loader import FileLoaderService
from ui.clues_panel import CluesPanel
from ui.crossword_widget import KrossWordWidget
from ui.calendar import Calendar
from ui.crossword_window import timer_row, load_puzzle

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
        self.current_puzzle_path = None
        self.elapsed_seconds = 0
        self.timer_running = False
        self.layout = None
        self.puzzle_timer = QTimer(self)
        self.puzzle_timer.setInterval(1000)
        self.puzzle_timer.timeout.connect(self._update_timer_display)
        self.clues_panel = None
        self.current_clue_widget = None
        self.crossword_widget = None
        self.shown = False
        self.date_label = None
        self.right_panel = None
        self.left_panel = None
        self.init_ui()

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        some_menu = menubar.addMenu("Some Menu")
        self.preferences_action = QAction("Preferences", self)
        self.preferences_action.setMenuRole(QAction.PreferencesRole)
        some_menu.addAction(self.preferences_action)
        self.preferences_action.triggered.connect(self.show_preferences)

        self.preferences_window = preferences()
        self.settings = QSettings("KrossWordz", "KrossWordz")


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
        self.check_menu = menubar.addMenu("Check")

        self.check_letter_action = QAction("Check Letter", self)
        self.check_letter_action.setEnabled(False)
        self.check_menu.addAction(self.check_letter_action)

        self.check_word_action = QAction("Check Word", self)
        self.check_word_action.setEnabled(False)
        self.check_menu.addAction(self.check_word_action)

        self.check_puzzle_action = QAction("Check Grid", self)
        self.check_puzzle_action.setEnabled(False)
        self.check_menu.addAction(self.check_puzzle_action)

        self.reveal_menu = menubar.addMenu("Reveal")

        self.reveal_letter_action = QAction("Reveal Letter", self)
        self.reveal_letter_action.setEnabled(False)
        self.reveal_menu.addAction(self.reveal_letter_action)

        self.reveal_word_action = QAction("Reveal Word", self)
        self.reveal_word_action.setEnabled(False)
        self.reveal_menu.addAction(self.reveal_word_action)

        self.reveal_puzzle_action = QAction("Reveal Grid", self)
        self.reveal_puzzle_action.setEnabled(False)
        self.reveal_menu.addAction(self.reveal_puzzle_action)


    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KrossWordz - Crossword Puzzle App")
        self.showMaximized() # Make window fullscreen

        self.main_tabs = QTabWidget(self)
        # Create menu bar
        self.create_menu_bar()

        # Central widget with splitter
        central_widget = QWidget()

        self.setCentralWidget(self.main_tabs)
        puzzle_page = QWidget()
        self.layout = QHBoxLayout(puzzle_page)
        self.layout.setSpacing(-1)
        self.layout.setContentsMargins(-1, -1, -1, -1)


        self.calendar = Calendar()
        self.calendar.loadPuzzle.connect(self.load_puzzle_from_path)

        self.layout.addWidget(self.calendar)

        self.main_tabs.addTab(puzzle_page, "Puzzle")
        self.main_tabs.setTabToolTip(0, "Crossword")

        self.ai_page = ai_window()

        self.main_tabs.addTab(self.ai_page, "AI")
        self.main_tabs.setTabToolTip(1, "AI")

        self.check_and_reveal = None


    def on_cell_count_changed(self, count):
        self.cells_filled.setText(f"{count}/{self.current_puzzle.fillable_cell_count}")

    def show_preferences(self):
        self.preferences_window.show()        


    def display_message(self, correct: bool):
        if correct:
            self.pause_puzzle_timer()
            self.resume_button.setVisible(False)
            self.pause_button.setVisible(False)
        if correct or not self.shown:
            show_message(self, correct)

        if not self.shown:
            self.shown = True

        

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
        last_puzzle_dir = self.settings.value("last_puzzle_dir", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, caption="Load .ipuz Puzzle", filter="IPUZ Files (*.ipuz);;All Files (*)", dir=last_puzzle_dir
        )

        if file_path:
            self.settings.setValue("last_puzzle_dir", os.path.dirname(file_path))
            self.load_puzzle_from_path(file_path)


    def load_puzzle_from_path(self, file_path: str, show_error_dialog: bool = True) -> bool:
        """Load a puzzle from an explicit filesystem path"""
        if not file_path:
            return False

        normalized_path = os.path.abspath(os.path.expanduser(file_path))
        self.current_puzzle_path = None

        try:
            if self.calendar:
                self.layout.removeWidget(self.calendar)
                self.calendar.setParent(None)
                self.calendar.deleteLater()
                self.calendar = None
            timer_row(self)
            load_puzzle(self, normalized_path)
            return True

        except Exception as e:
            if show_error_dialog:
                QMessageBox.warning(self, "Error",
                    f"Failed to load puzzle:\n{e}\n\n{traceback.format_exc()}")
            else:
                print(f"Failed to load puzzle from {normalized_path}: {e}")
            self.current_puzzle_path = None
            return False

    def save_progress(self):
        """Save current progress"""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "No puzzle loaded to save")
            return
        if not self.current_puzzle_path:
            QMessageBox.warning(self, "Warning", "Original puzzle file path not available")
            return

        try:
            # Convert to serializable format
            saved = []
            for row in self.current_puzzle.cells:
                row_data = []
                for cell in row:
                    if cell.is_black:
                        row_data.append('#')
                    else:
                        row_data.append(cell.user_input)
                saved.append(row_data)

            with open(self.current_puzzle_path, "r", encoding="utf-8") as f:
                puzzle_data = json.load(f)

            puzzle_data["saved"] = saved

            with open(self.current_puzzle_path, "w", encoding="utf-8") as f:
                json.dump(puzzle_data, f, indent=2)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save progress: {e}")

    def on_clue_selected(self, number, direction):
        if not self.crossword_widget.puzzle:
            return

        clue = self.crossword_widget.puzzle.get_clue(number, direction)

        self.crossword_widget.highlight_mode = direction
        self.crossword_widget.selected_row = clue.start_row
        self.crossword_widget.selected_col = clue.start_col

        opposite_direction = "across" if direction == "down" else "down"
        start_row, start_col = self.crossword_widget.find_word_start(self.crossword_widget.selected_row, self.crossword_widget.selected_col, opposite_direction)
        opposite_direction_clue = self.crossword_widget.find_clue_for_cell(start_row, start_col, opposite_direction)

        if opposite_direction_clue:
            self.clues_panel.highlight_clue_side(opposite_direction_clue.number, opposite_direction_clue.direction) 

        self.crossword_widget.setFocus(Qt.MouseFocusReason)
        self._update_current_clue_display(self.crossword_widget.selected_row, self.crossword_widget.selected_col)
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



    def update_title_label(self):
        """Update the title label with puzzle info"""
        if not self.current_puzzle:
            self.title_label.setText("No puzzle loaded")
            self.author_label.setText("")
            return

        self.title_label.setText(self.current_puzzle.title)
        if self.current_puzzle.date:
            d = datetime.strptime(self.current_puzzle.date, "%m/%d/%Y")
            formatted = d.strftime("%A, %B %d, %Y")
            self.date_label.setText(formatted)


        author_text = f"By {self.current_puzzle.author}" if self.current_puzzle.author else ""
        self.author_label.setText(author_text)
        self.editor_label.setText(f"Edited by {self.current_puzzle.editor}" if self.current_puzzle.editor else "")


    def on_cell_selected(self, row, col):
        """Handle cell selection events"""
        print(f"Cell selected: ({row}, {col})")
        cell = self.current_puzzle.cells[row][col] if self.current_puzzle else None
        print(f"Cell has clue_number: {cell.clue_number if cell else 'None'}")

        # Always update current clue display, regardless of whether cell has a number
        self._update_current_clue_display(row, col)
        self._update_clues_highlight(row, col)
    
    def _update_clues_highlight(self, row, col):
        if not self.current_puzzle or not self.clues_panel:
            return

        direction = self.crossword_widget.highlight_mode
        
        # this should never happen. So can I just delete this?
        if direction not in ("across", "down"):
            self.clues_panel.clear_highlight()
            return

        clue = self.crossword_widget.find_clue_for_cell(row, col, direction)
        opposite_direction = "across" if direction == "down" else "down"
        start_row, start_col = self.crossword_widget.find_word_start(row, col, opposite_direction)
        opposite_direction_clue = self.crossword_widget.find_clue_for_cell(start_row, start_col, opposite_direction)

        if opposite_direction_clue:
            self.clues_panel.highlight_clue_side(opposite_direction_clue.number, opposite_direction_clue.direction)
        if clue:
            self.clues_panel.highlight_clue(clue.number, clue.direction)
        else:
            self.clues_panel.clear_highlight()


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

        # Get direction from current highlight mode
        if self.crossword_widget.highlight_mode == "across":
            direction = "across"
        elif self.crossword_widget.highlight_mode == "down":
            direction = "down"

        # Find the clue for this cell in the current direction
        clue = self.crossword_widget.find_clue_for_cell(row, col, direction)

        self.current_clue_widget.set_clue(clue)
