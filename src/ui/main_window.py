import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from services.file_loader import FileLoaderService
from ui.clues_panel import CluesPanel
from ui.crossword_widget import KrossWordWidget
from ui.tab_event_filter import TabEventFilter

class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.file_loader_service = FileLoaderService()
        self.current_puzzle = None
        self.init_ui()
        # Create and install global event filter for tab key handling
        self.tab_event_filter = TabEventFilter(self.crossword_widget)
        QApplication.instance().installEventFilter(self.tab_event_filter)
        print("DEBUG: Global tab event filter installed")

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()

        # Create File menu
        file_menu = menubar.addMenu("File")

        # Create Load Puzzle action
        load_action = QAction("Load Puzzle", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_puzzle)
        file_menu.addAction(load_action)

        # Create Save Progress action
        save_action = QAction("Save Progress", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_progress)
        file_menu.addAction(save_action)

        # Add separator
        file_menu.addSeparator()

        # Create Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

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

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Crossword and current clue
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Current clue display above crossword
        self.current_clue_label = QLabel("Select a cell to see clue")
        self.current_clue_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.current_clue_label.setWordWrap(True)
        self.current_clue_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.current_clue_label.setMinimumHeight(30)
        left_layout.addWidget(self.current_clue_label)

        # Crossword grid
        self.crossword_widget = KrossWordWidget()
        self.crossword_widget.cell_selected.connect(self.on_cell_selected)
        self.crossword_widget.value_changed.connect(self.raise_updated_signal)
        self.crossword_widget.setFocusPolicy(Qt.StrongFocus)  # Make sure it can receive key events
        left_layout.addWidget(self.crossword_widget)

        # Right panel: puzzle info, clues, and actions
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

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

        right_layout.addSpacing(10)

        check_letter_button = QPushButton("Check Letter")
        check_letter_button.clicked.connect(self.check_current_letter)
        right_layout.addWidget(check_letter_button)

        check_word_button = QPushButton("Check Word")
        check_word_button.clicked.connect(self.check_current_word)
        right_layout.addWidget(check_word_button)

        check_puzzle_button = QPushButton("Check Answers")
        check_puzzle_button.clicked.connect(self.check_answers)
        right_layout.addWidget(check_puzzle_button)

        right_layout.addStretch()

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 800])

        layout.addWidget(splitter)
        self.statusBar().showMessage("Ready")

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
            self.statusBar().showMessage(f"Loaded: {self.current_puzzle.title}")
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

                self.statusBar().showMessage("Progress saved successfully")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save progress: {e}")

    def check_answers(self):
        """Check current answers"""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "No puzzle loaded to check")
            return


        for row in self.current_puzzle.cells:
            for cell in row:
                if not cell.is_black and cell.solution:
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

    def check_current_word(self):
        """Verify the word that contains the currently selected cell."""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "Load a puzzle before checking words")
            return
        position = self.crossword_widget.get_current_position()
        if not position:
            self.statusBar().showMessage("Select a cell within a word to check", 3000)
            return
        word_cells = self.crossword_widget.get_current_word_coordinates()
        # if not word_cells:
        #     self.statusBar().showMessage("Select a cell within a valid word", 3000)
        #     return
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

        if cell and cell.clue_number:
            # Show clue for selected cell number in status bar
            clue_text = f"Cell {row},{col} - Clue #{cell.clue_number}"

            across_clue = self.current_puzzle.get_clue(cell.clue_number, "across")
            down_clue = self.current_puzzle.get_clue(cell.clue_number, "down")

            if across_clue and self._has_cell_in_direction(row, col, "across"):
                clue_text += f" (Across: {across_clue.text})"
            if down_clue and self._has_cell_in_direction(row, col, "down"):
                clue_text += f" (Down: {down_clue.text})"

            self.statusBar().showMessage(clue_text, 3000)  # Show for 3 seconds)

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
