import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QTextEdit,
                             QPushButton, QFileDialog, QMessageBox, QSplitter,
                             QMenuBar, QMenu)
from PySide6.QtCore import Qt, Signal, QSize, QObject
from PySide6.QtGui import QFont, QPainter, QBrush, QColor, QPen, QKeyEvent, QAction
from models.krossword import KrossWordPuzzle, KrossWordCell
from parsers.ipuz_parser import IPUZParser
from services.file_loader import FileLoaderService

class TabEventFilter(QObject):
    """Global event filter to catch tab key presses"""

    def __init__(self, crossword_widget):
        super().__init__()
        self.crossword_widget = crossword_widget

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            if event.key() in [Qt.Key_Tab, Qt.Key_Backtab]:
                print(f"DEBUG: Global event filter caught tab key from: {obj}")
                # Forward to crossword widget
                self.crossword_widget._handle_navigation(event.key())
                return True  # Event handled
        return False  # Let other events pass

class CluesTextEdit(QTextEdit):
    """Custom text edit that ignores arrow keys to forward them to parent"""

    def keyPressEvent(self, event):
        # Ignore arrow keys, space bar, and Tab to let parent widget handle them
        if event.key() in [Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down, Qt.Key_Space, Qt.Key_Tab]:
            event.ignore()  # Forward to parent
        else:
            super().keyPressEvent(event)

class KrossWordWidget(QWidget):
    """Widget for displaying and interacting with a crossword puzzle"""

    cell_selected = Signal(int, int)  # row, col
    value_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.puzzle = None
        self.selected_row = 0
        self.selected_col = 0
        self.highlight_mode = "across"  # "across", "down"
        self.font_size = 16
        self.cell_size = 40
        self.setMouseTracking(True)
        self.setMinimumSize(400, 400)
        print("DEBUG: KrossWordWidget initialized")
        # Set focus policy to ensure it can receive key events
        self.setFocusPolicy(Qt.StrongFocus)

    def set_puzzle(self, puzzle: KrossWordPuzzle):
        """Set the crossword puzzle to display"""
        self.puzzle = puzzle
        # Resize widget to fit the puzzle
        widget_width = max(400, self.puzzle.width * self.cell_size)
        widget_height = max(400, self.puzzle.height * self.cell_size + 50)  # Extra space for title
        self.setMinimumSize(widget_width, widget_height)
        self.update()

    def _get_word_bounds(self, row, col, direction):
        """Get the start and end bounds of a word in the given direction"""
        if not self.puzzle:
            return None, None

        # Find start of word
        start_col, start_row = col, row
        if direction == "across":
            while start_col > 0 and not self.puzzle.cells[start_row][start_col - 1].is_black:
                start_col -= 1
        else:  # down
            while start_row > 0 and not self.puzzle.cells[start_row - 1][start_col].is_black:
                start_row -= 1

        # Find end of word
        end_col, end_row = col, row
        if direction == "across":
            while end_col < self.puzzle.width - 1 and not self.puzzle.cells[end_row][end_col + 1].is_black:
                end_col += 1
        else:  # down
            while end_row < self.puzzle.height - 1 and not self.puzzle.cells[end_row + 1][end_col].is_black:
                end_row += 1

        return (start_col, start_row), (end_col, end_row)

    def _find_word_start_in_widget(self, row, col, direction):
        """Find the starting cell of a word in the given direction - for widget use"""
        if direction == "across":
            # Find leftmost cell in the same row
            start_col = col
            # Move left until we hit a black cell or the beginning of the puzzle
            while start_col > 0:
                if self.puzzle.cells[row][start_col - 1].is_black:
                    break
                start_col -= 1
            return row, start_col
        else:  # down
            # Find topmost cell in the same column
            start_row = row
            # Move up until we hit a black cell or the beginning of the puzzle
            while start_row > 0:
                if self.puzzle.cells[start_row - 1][col].is_black:
                    break
                start_row -= 1
            return start_row, col

    def paintEvent(self, event):
        """Paint the crossword grid"""
        if not self.puzzle:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self._draw_cells(painter)
        self._draw_grid(painter)

    def _draw_grid(self, painter):
        """Draw the grid lines"""
        # First draw all inner grid lines with thin gray
        painter.setPen(QPen(Qt.gray, 2))

        # Draw all row lines - stop before bottom perimeter
        for row in range(1, self.puzzle.height):
            y = row * self.cell_size
            painter.drawLine(0, y, self.puzzle.width * self.cell_size - 1, y)

        # Draw all column lines - stop before right perimeter
        for col in range(1, self.puzzle.width):
            x = col * self.cell_size
            painter.drawLine(x, 0, x, self.puzzle.height * self.cell_size - 1)

        # Finally draw outer perimeter lines with thick gray - these will be on top
        # Top edge - slightly inset for better visibility
        painter.drawLine(1, 1, self.puzzle.width * self.cell_size - 1, 1)
        # Bottom edge
        painter.drawLine(1, self.puzzle.height * self.cell_size - 1,  self.puzzle.width * self.cell_size - 1, self.puzzle.height * self.cell_size - 1)
        # Left edge - slightly inset for better visibility
        painter.drawLine(1, 1, 1, self.puzzle.height * self.cell_size - 1)
        # Right edge
        painter.drawLine(self.puzzle.width * self.cell_size - 1, 1, self.puzzle.width * self.cell_size - 1, self.puzzle.height * self.cell_size - 1)

        # Draw the puzzle title and dimensions
        painter.setPen(QPen(Qt.darkBlue))
        info_text = f"{self.puzzle.title} - {self.puzzle.width}x{self.puzzle.height}"
        painter.drawText(10, self.puzzle.height * self.cell_size + 30, info_text)

    def _draw_cells(self, painter):
        """Draw the cells with content"""
        for row in range(self.puzzle.height):
            for col in range(self.puzzle.width):
                self._draw_cell(painter, row, col)

    def _draw_cell(self, painter, row, col):
        """Draw a single cell"""
        cell = self.puzzle.cells[row][col]
        x = col * self.cell_size
        y = row * self.cell_size

        # Fill cell background
        if cell.is_black:
            painter.fillRect(x, y, self.cell_size, self.cell_size, QBrush(Qt.black))
        else:
            # Check if this cell should be highlighted
            is_selected_cell = (row == self.selected_row and col == self.selected_col)
            should_highlight = False

            if self.highlight_mode in ["across", "down"] and self.puzzle:
                # Get word bounds from the selected cell
                start, end = self._get_word_bounds(self.selected_row, self.selected_col, self.highlight_mode)
                if start and end:
                    start_col, start_row = start
                    end_col, end_row = end
                    # Check if current cell is within word bounds
                    if self.highlight_mode == "across":
                        if row == start_row and start_col <= col <= end_col:
                            should_highlight = True
                    else:  # down
                        if col == start_col and start_row <= row <= end_row:
                            should_highlight = True

            # Apply highlighting
            if should_highlight:
                if is_selected_cell:
                    # Selected cell is yellow
                    painter.fillRect(x, y, self.cell_size, self.cell_size, QBrush(QColor(255, 255, 150)))  # Yellow
                else:
                    # Rest of word is light blue
                    painter.fillRect(x, y, self.cell_size, self.cell_size, QBrush(QColor(150, 200, 255)))  # Light blue
            else:
                painter.fillRect(x, y, self.cell_size, self.cell_size, QBrush(Qt.white))


        # Draw cell content
        painter.setPen(QPen(Qt.black))
        # Use a larger font that fills more of the cell - unbolded
        font = QFont("Arial", self.font_size + 8, QFont.Normal)  # Increased size by 8, not bold
        painter.setFont(font)

        if cell.user_input:
            text = cell.user_input.upper()  # Ensure uppercase
            # Calculate centered position for the letter
            text_rect = painter.fontMetrics().boundingRect(text)
            text_x = x + (self.cell_size - text_rect.width()) // 2
            text_y = y + (self.cell_size + text_rect.height()) // 2 - 2  # Center vertically, small adjustment
            painter.drawText(text_x, text_y, text)

        # Draw clue number
        if cell.clue_number:
            painter.setPen(QPen(Qt.darkBlue))
            small_font = QFont("Arial", 8)
            painter.setFont(small_font)
            painter.drawText(x + 2, y + 12, str(cell.clue_number))

    def mousePressEvent(self, event):
        """Handle mouse clicks to select cells"""
        if not self.puzzle:
            return

        col = int(round(event.position().x() // self.cell_size))
        row = int(round(event.position().y() // self.cell_size))

        if 0 <= row < self.puzzle.height and 0 <= col < self.puzzle.width:
            if not self.puzzle.cells[row][col].is_black:
                # Click on same cell to cycle highlight modes
                if row == self.selected_row and col == self.selected_col:
                    if self.highlight_mode == "across":
                        self.highlight_mode = "down"
                    else:  # down
                        self.highlight_mode = "across"
                else:
                    # Click on different cell to select it
                    self.selected_row = row
                    self.selected_col = col

                # Focus this widget to ensure arrow keys work
                self.setFocus()
                self.cell_selected.emit(row, col)
                self.update()

    def event(self, event):
        """Handle events, including forcing tab keys to be processed"""
        if event.type() == event.Type.KeyPress:
            if event.key() in [Qt.Key_Tab, Qt.Key_Backtab]:
                print(f"DEBUG: Tab key caught in event() method")
                self._handle_navigation(event.key())
                return True  # Event handled

        # Let base class handle other events
        return super().event(event)

    def keyPressEvent(self, event):
        """Handle keyboard input for cell values"""
        if not self.puzzle:
            return

        key = event.key()
        print(f"DEBUG: KrossWordWidget keyPressEvent called with key: {key} ({Qt.Key_Tab})")

        # Handle smart arrow keys that change highlight mode
        if key == Qt.Key_Left:
            if self.highlight_mode == "down":
                # In down mode, left/right keys change to across mode
                self.highlight_mode = "across"
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
            else:
                # In across mode, left keys move horizontally
                self._move_left()
        elif key == Qt.Key_Right:
            if self.highlight_mode == "down":
                # In down mode, left/right keys change to across mode
                self.highlight_mode = "across"
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
            else:
                # In across mode, right keys move horizontally
                self._move_right()
        elif key == Qt.Key_Up:
            if self.highlight_mode == "across":
                # In across mode, up/down keys change to down mode
                self.highlight_mode = "down"
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
            else:
                # In down mode, up keys move vertically
                self._move_up()
        elif key == Qt.Key_Down:
            if self.highlight_mode == "across":
                # In across mode, up/down keys change to down mode
                self.highlight_mode = "down"
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
            else:
                # In down mode, down keys move vertically
                self._move_down()
        elif Qt.Key_0 <= key <= Qt.Key_Z:
            self._handle_letter_input(key)
        elif key == Qt.Key_Backspace or key == Qt.Key_Delete:
            print(f"Backspace/Delete pressed. Current cell: ({self.selected_row}, {self.selected_col}), current content: '{self.puzzle.cells[self.selected_row][self.selected_col].user_input}'")
            self._handle_delete(key)
        elif key == Qt.Key_Return:
            print(f"DEBUG: Return key detected: {key}")
            self._handle_navigation(key)
        elif key == Qt.Key_Space:
            self._toggle_highlight_mode()
        else:
            super().keyPressEvent(event)

    def _handle_letter_input(self, key):
        """Handle letter input"""
        cell = self.puzzle.cells[self.selected_row][self.selected_col]
        if cell.is_black:
            return

        # Get the character
        char = ''
        if Qt.Key_0 <= key <= Qt.Key_Z:
            # Convert to uppercase
            char = chr(key).upper()

        if char:
            # Check if we're overwriting an existing character
            was_empty = cell.user_input == ""
            print(f"DEBUG: Typed '{char}' in cell ({self.selected_row}, {self.selected_col}), was_empty: {was_empty}")
            cell.user_input = char

            # Check if we're at the last character of the current entry (position-based)
            start, end = self._get_word_bounds(self.selected_row, self.selected_col, self.highlight_mode)
            is_last_character = False

            if start and end:
                if self.highlight_mode == "across":
                    is_last_character = (self.selected_col == end[0])
                else:  # down
                    is_last_character = (self.selected_row == end[1])

            # Use appropriate movement based on whether cell was empty and position in entry
            if was_empty:
                print("DEBUG: Cell was empty and not last character, moving to adjacent character")
                self._loop_to_empty_in_entry(is_last_character)
            elif not is_last_character:
                # If cell was already filled and not at last character, move to next cell normally
                print("DEBUG: Cell was filled and not last character, using regular movement")
                if self.highlight_mode == "down":
                    self._move_down()
                else:
                    self._move_right()
            # if it's not empty and it's the last character, do nothing
            

            self.value_changed.emit()
            self.update()

    def _loop_to_empty_in_entry(self, is_last_character):
        """Loop back to start of current entry and find empty squares to move to"""
        if not self.puzzle:
            return

        # Get current entry bounds
        start, end = self._get_word_bounds(self.selected_row, self.selected_col, self.highlight_mode)
        if not start or not end:
            return

        # Store original position and mode
        original_row, original_col = self.selected_row, self.selected_col
        original_mode = self.highlight_mode

        print(f"DEBUG: Original position: ({original_row}, {original_col}), entry start: {start}, end: {end}")

        # Find first empty square in entry, starting from next character and wrapping around
        if self.highlight_mode == "across":
            row = start[1]
            # Start from next character after current
            search_start = self.selected_col + 1
            if search_start > end[0]:
                search_start = start[0]

            # First pass: from start character to end
            for col in range(search_start, end[0] + 1):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return

            # Second pass: from start to current character (if not found in first pass)
            for col in range(start[0], self.selected_col + 1):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return
        else:  # down
            col = start[0]
            # Start from next character after current
            search_start = self.selected_row + 1
            if search_start > end[1]:
                search_start = start[1]

            # First pass: from start character to end
            for row in range(search_start, end[1] + 1):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return

            # Second pass: from start to current character (if not found in first pass)
            for row in range(start[1], self.selected_row + 1):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return

        # No empty squares found in entry - move to next character
        
        print("DEBUG: No empty squares found in entry, moving to next character")
        if not is_last_character:
            self.highlight_mode = original_mode  # Ensure mode is correct
            if self.highlight_mode == "down":
                self._move_down()
            else:
                self._move_right()
        # if it is the last character, then don't move at all 

    def _is_truly_last_empty_character(self):
        """Check if current cell is the last empty character in the entry"""
        if not self.puzzle:
            return False

        start, end = self._get_word_bounds(self.selected_row, self.selected_col, self.highlight_mode)
        if not start or not end:
            return False

        # Check if all other cells in the entry are filled
        if self.highlight_mode == "across":
            row = start[1]
            for col in range(start[0], end[0] + 1):
                if (row, col) != (self.selected_row, self.selected_col):
                    if self.puzzle.cells[row][col].user_input == "":
                        return False  # Found another empty cell
        else:  # down
            col = start[0]
            for row in range(start[1], end[1] + 1):
                if (row, col) != (self.selected_row, self.selected_col):
                    if self.puzzle.cells[row][col].user_input == "":
                        return False  # Found another empty cell

        return True  # Current cell is the last empty one

    def _handle_delete(self, key):
        """Handle backspace/delete key with smart behavior"""
        cell = self.puzzle.cells[self.selected_row][self.selected_col]
        print(f"Delete handler: cell.is_black={cell.is_black}, user_input='{cell.user_input}'")
        if not cell.is_black:
            if cell.user_input:
                # If there's a letter in the current cell, delete it and stay
                print(f"Deleting current cell content: {cell.user_input}")
                cell.user_input = ""
                self.value_changed.emit()
                self.update()
            else:
                # If cell is empty, move to previous cell and delete its content
                print("Cell is empty, moving to previous cell")
                original_row, original_col = self.selected_row, self.selected_col
                self._move_to_previous_cell()
                print(f"Moved to previous cell: ({self.selected_row}, {self.selected_col}), original was ({original_row}, {original_col})")
                if (self.selected_row != original_row or self.selected_col != original_col):
                    prev_cell = self.puzzle.cells[self.selected_row][self.selected_col]
                    print(f"Previous cell content: '{prev_cell.user_input}', is_black: {prev_cell.is_black}")
                    if prev_cell and not prev_cell.is_black:
                        prev_cell.user_input = ""
                        self.value_changed.emit()
                        self.update()
                else:
                    print("Could not find a valid previous cell")

    def _toggle_highlight_mode(self):
        """Toggle between across and down highlight modes"""
        if self.highlight_mode == "across":
            self.highlight_mode = "down"
        else:
            self.highlight_mode = "across"
        self.cell_selected.emit(self.selected_row, self.selected_col)
        self.update()

    def _handle_navigation(self, key):
        """Handle navigation keys"""
        print(f"DEBUG: _handle_navigation called with key: {key}")
        if key == Qt.Key_Tab or key == Qt.Key_Backtab:
            print("DEBUG: Tab key pressed - calling _move_to_next_entry_start")
            self._move_to_next_entry_start()
        elif key == Qt.Key_Right:
            print("DEBUG: Right key pressed - calling move_right")
            self.move_right()
        elif key == Qt.Key_Return:
            print("DEBUG: Return key pressed - calling move_down")
            self.move_down()

    def _move_to_next_entry_start(self):
        """Move to the start of the next across or down entry"""
        if not self.puzzle:
            return

        # Get current clue number by finding the word start from current position
        start_row, start_col = self._find_word_start_in_widget(self.selected_row, self.selected_col, self.highlight_mode)
        current_clue = None

        if start_row is not None and start_col is not None:
            start_cell = self.puzzle.cells[start_row][start_col]
            if start_cell.clue_number:
                current_clue = self.puzzle.get_clue(start_cell.clue_number, self.highlight_mode)

        # If current mode is across and we're at the last across clue, switch to down
        if self.highlight_mode == "across":
            across_clues = self.puzzle.across_clues
            if across_clues:
                current_index = -1
                if current_clue:
                    for i, clue in enumerate(across_clues):
                        if clue.number == current_clue.number:
                            current_index = i
                            break

                # If we're at the last across clue, switch to down mode
                if current_index == len(across_clues) - 1:
                    self.highlight_mode = "down"
                    if self.puzzle.down_clues:
                        next_clue = self.puzzle.down_clues[0]  # First down clue
                        print(f"Switching from across to down, moved to clue #{next_clue.number}: {next_clue.text[:50]}...")
                    else:
                        return  # No down clues available
                else:
                    # Continue with next across clue
                    next_index = (current_index + 1) % len(across_clues)
                    next_clue = across_clues[next_index]
                    print(f"Moved to next across clue #{next_clue.number}: {next_clue.text[:50]}...")
        else:
            # Current mode is down - cycle through down clues
            down_clues = self.puzzle.down_clues
            if not down_clues:
                return  # No down clues in this direction

            current_index = -1
            if current_clue:
                for i, clue in enumerate(down_clues):
                    if clue.number == current_clue.number:
                        current_index = i
                        break
            if current_index == len(down_clues) - 1:
                self.highlight_mode = "across"
                if self.puzzle.across_clues:
                    next_clue = self.puzzle.across_clues[0]  # First across clue
                    print(f"Switching from down to across, moved to clue #{next_clue.number}: {next_clue.text[:50]}...")
                else:
                    return  # No across clues available

            # Get next down clue (wrap around if at end)
            next_index = (current_index + 1) % len(down_clues)
            next_clue = down_clues[next_index]
            print(f"Moved to next down clue #{next_clue.number}: {next_clue.text[:50]}...")

        # Move to the selected clue's starting position
        self.selected_row = next_clue.start_row
        self.selected_col = next_clue.start_col
        self.cell_selected.emit(self.selected_row, self.selected_col)
        self.update()

    def _move_left(self):
        """Move selection to the left with arrow key"""
        new_col = self.selected_col - 1
        while new_col >= 0:
            if not self.puzzle.cells[self.selected_row][new_col].is_black:
                self.selected_col = new_col
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
                return
            new_col -= 1

    def _move_right(self):
        """Move selection to the right with arrow key"""
        new_col = self.selected_col + 1
        while new_col < self.puzzle.width:
            if not self.puzzle.cells[self.selected_row][new_col].is_black:
                self.selected_col = new_col
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
                return
            new_col += 1

    def _move_up(self):
        """Move selection up with arrow key"""
        new_row = self.selected_row - 1
        while new_row >= 0:
            if not self.puzzle.cells[new_row][self.selected_col].is_black:
                self.selected_row = new_row
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
                return
            new_row -= 1

    def _move_down(self):
        """Move selection down with arrow key"""
        new_row = self.selected_row + 1
        while new_row < self.puzzle.height:
            if not self.puzzle.cells[new_row][self.selected_col].is_black:
                self.selected_row = new_row
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
                return
            new_row += 1

    def move_right(self):
        """Move selection to the right (for Tab/Enter keys)"""
        if self.selected_col < self.puzzle.width - 1:
            self.selected_col += 1
            self._skip_black_cells()
        self.cell_selected.emit(self.selected_row, self.selected_col)
        self.update()

    def move_down(self):
        """Move selection down (for Enter key)"""
        if self.selected_row < self.puzzle.height - 1:
            self.selected_row += 1
            self._skip_black_cells()
        self.cell_selected.emit(self.selected_row, self.selected_col)
        self.update()

    def move_to_next_cell(self):
        """Move to the next available cell based on current highlight mode"""
        if self.highlight_mode == "down":
            self._move_to_next_empty_cell_down()
        else:
            self._move_to_next_empty_cell_across()

    def _is_cell_empty(self, row, col):
        """Check if a cell is empty (no user input)"""
        if not self.puzzle or row < 0 or row >= self.puzzle.height or col < 0 or col >= self.puzzle.width:
            return False
        cell = self.puzzle.cells[row][col]
        return not cell.is_black and cell.user_input == ""

    def _move_to_next_empty_cell_across(self):
        """Move to the next empty cell in across direction within current word"""
        original_row, original_col = self.selected_row, self.selected_col
        new_col = self.selected_col + 1

        # Look for empty cells in the current row (same word)
        while new_col < self.puzzle.width:
            if not self.puzzle.cells[self.selected_row][new_col].is_black and self._is_cell_empty(self.selected_row, new_col):
                self.selected_col = new_col
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
                return
            new_col += 1

        # Reached end of current word, no empty cells found - stay in current position
        print("Reached end of current across word with no empty cells, staying in position")

    def _move_to_next_empty_cell_down(self):
        """Move to the next empty cell in down direction within current word"""
        original_row, original_col = self.selected_row, self.selected_col
        new_row = self.selected_row + 1

        # Look for empty cells in the current column (same word)
        while new_row < self.puzzle.height:
            if not self.puzzle.cells[new_row][self.selected_col].is_black and self._is_cell_empty(new_row, self.selected_col):
                self.selected_row = new_row
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
                return
            new_row += 1

        # Reached end of current word, no empty cells found - stay in current position
        print("Reached end of current down word with no empty cells, staying in position")

    def _move_to_previous_cell(self):
        """Move to the previous available cell based on current highlight mode"""
        original_row, original_col = self.selected_row, self.selected_col
        print(f"Moving to previous cell from ({original_row}, {original_col}) in {self.highlight_mode} mode")

        if self.highlight_mode == "down":
            # In down mode, move up
            new_row = self.selected_row - 1
            if new_row >= 0:
                while new_row >= 0:
                    if not self.puzzle.cells[new_row][self.selected_col].is_black:
                        self.selected_row = new_row
                        print(f"Found previous cell above: ({self.selected_row}, {self.selected_col})")
                        return
                    new_row -= 1
                print("No valid cells above")

            # If we can't move up in the same column, move left to the previous column and go to the bottom
            if self.selected_col > 0:
                self.selected_col -= 1
                print(f"Moving left to column {self.selected_col}")
                new_row = self.puzzle.height - 1
                while new_row >= 0:
                    if not self.puzzle.cells[new_row][self.selected_col].is_black:
                        self.selected_row = new_row
                        print(f"Found previous cell in previous column: ({self.selected_row}, {self.selected_col})")
                        return
                    new_row -= 1
                print(f"No valid cells in previous column {self.selected_col}")
        else:
            # In across mode, move left (original logic)
            new_col = self.selected_col - 1
            if new_col >= 0:
                while new_col >= 0:
                    if not self.puzzle.cells[self.selected_row][new_col].is_black:
                        self.selected_col = new_col
                        print(f"Found previous cell to the left: ({self.selected_row}, {self.selected_col})")
                        return
                    new_col -= 1
                print("No valid cells to the left")

            # If we can't move left in the same row, move up to the previous row and go to the end
            if self.selected_row > 0:
                self.selected_row -= 1
                print(f"Moving up to row {self.selected_row}")
                new_col = self.puzzle.width - 1
                while new_col >= 0:
                    if not self.puzzle.cells[self.selected_row][new_col].is_black:
                        self.selected_col = new_col
                        print(f"Found previous cell in previous row: ({self.selected_row}, {self.selected_col})")
                        return
                    new_col -= 1
                print(f"No valid cells in previous row {self.selected_row}")

        # If we can't find a valid cell, return to original position
        self.selected_row = original_row
        self.selected_col = original_col
        print("Could not find valid previous cell, staying in original position")

    def _skip_black_cells(self):
        """Skip black cells when moving forward"""
        while (0 <= self.selected_row < self.puzzle.height and
               0 <= self.selected_col < self.puzzle.width and
               self.puzzle.cells[self.selected_row][self.selected_col].is_black):
            self.selected_col += 1
            if self.selected_col >= self.puzzle.width:
                self.selected_row += 1
                self.selected_col = 0
                # Wrap around to next row if at the end
                if self.selected_row >= self.puzzle.height:
                    # Go back to beginning if no valid cells found
                    self.selected_row = 0
                    self.selected_col = 0
                    break

    def _skip_black_cells_reverse(self):
        """Skip black cells when moving backward"""
        original_row, original_col = self.selected_row, self.selected_col
        while (0 <= self.selected_row < self.puzzle.height and
               0 <= self.selected_col < self.puzzle.width and
               self.puzzle.cells[self.selected_row][self.selected_col].is_black):
            self.selected_col -= 1
            if self.selected_col < 0:
                self.selected_row -= 1
                self.selected_col = self.puzzle.width - 1
                # Prevent infinite loop by going back to original position
                if (self.selected_row, self.selected_col) == (original_row, original_col):
                    break
                # Wrap around to previous row if at the beginning
                if self.selected_row < 0:
                    self.selected_row = self.puzzle.height - 1
                    self.selected_col = self.puzzle.width - 1
                    break

    def _skip_black_cells_up(self):
        """Skip black cells when moving up"""
        original_row, original_col = self.selected_row, self.selected_col
        while (0 <= self.selected_row < self.puzzle.height and
               0 <= self.selected_col < self.puzzle.width and
               self.puzzle.cells[self.selected_row][self.selected_col].is_black):
            self.selected_row -= 1
            if self.selected_row < 0:
                self.selected_col -= 1
                self.selected_row = self.puzzle.height - 1
                # Prevent infinite loop by going back to original position
                if (self.selected_row, self.selected_col) == (original_row, original_col):
                    break
                # Wrap around to previous column if at the top
                if self.selected_col < 0:
                    self.selected_col = self.puzzle.width - 1
                    self.selected_row = self.puzzle.height - 1
                    break

    def get_current_cell(self) -> KrossWordCell:
        """Get the currently selected cell"""
        if self.puzzle and 0 <= self.selected_row < self.puzzle.height:
            if 0 <= self.selected_col < self.puzzle.width:
                return self.puzzle.cells[self.selected_row][self.selected_col]
        return None

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
        self.setGeometry(100, 100, 1200, 800)

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

        # Right panel: Two separate clue sections
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Across clues section
        across_widget = QWidget()
        across_layout = QVBoxLayout(across_widget)
        across_label = QLabel("ACROSS")
        across_label.setFont(QFont("Arial", 11, QFont.Bold))
        across_layout.addWidget(across_label)

        self.across_clues_text = CluesTextEdit()
        self.across_clues_text.setReadOnly(True)
        self.across_clues_text.setMaximumHeight(200)
        across_layout.addWidget(self.across_clues_text)

        # Down clues section
        down_widget = QWidget()
        down_layout = QVBoxLayout(down_widget)
        down_label = QLabel("DOWN")
        down_label.setFont(QFont("Arial", 11, QFont.Bold))
        down_layout.addWidget(down_label)

        self.down_clues_text = CluesTextEdit()
        self.down_clues_text.setReadOnly(True)
        self.down_clues_text.setMaximumHeight(200)
        down_layout.addWidget(self.down_clues_text)

        # Title label
        self.title_label = QLabel("No puzzle loaded")
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        right_layout.addWidget(self.title_label)

        # Author label
        self.author_label = QLabel("")
        right_layout.addWidget(self.author_label)

        # Add sections to right panel
        right_layout.addWidget(across_widget)
        right_layout.addWidget(down_widget)

        # Add spacing
        right_layout.addSpacing(20)

        # Title label
        self.title_label = QLabel("No puzzle loaded")
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        right_layout.addWidget(self.title_label)

        # Author label
        self.author_label = QLabel("")
        right_layout.addWidget(self.author_label)

        # Keep only Check Answers button since Load/Save are now in menu
        check_button = QPushButton("Check Answers")
        check_button.clicked.connect(self.check_answers)
        right_layout.addWidget(check_button)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 500])

        layout.addWidget(splitter)
        self.statusBar().showMessage("Ready")

    def load_puzzle(self):
        """Load a puzzle from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load .ipuz Puzzle", "", "IPUZ Files (*.ipuz);;All Files (*)"
        )

        if file_path:
            try:
                self.current_puzzle = self.file_loader_service.load_ipuz_file(file_path)
                self.crossword_widget.set_puzzle(self.current_puzzle)
                self.update_clues_display()
                self.update_title_label()
                self.statusBar().showMessage(f"Loaded: {self.current_puzzle.title}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load puzzle: {e}")

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

        correct_count = 0
        total_cells = 0

        for row in self.current_puzzle.cells:
            for cell in row:
                if not cell.is_black and cell.solution:
                    total_cells += 1
                    if cell.user_input and cell.user_input == cell.solution:
                        correct_count += 1

        if total_cells > 0:
            percentage = (correct_count / total_cells) * 100
            status = f"Correct: {correct_count}/{total_cells} ({percentage:.1f}%)"
        else:
            status = "No solvable cells found"

        self.statusBar().showMessage(status)

    def update_clues_display(self):
        """Update the clues display with separate across and down sections"""
        if not self.current_puzzle:
            return

        # Update across clues
        across_text = ""
        for clue in sorted(self.current_puzzle.across_clues, key=lambda x: x.number):
            across_text += f"{clue.number}. {clue.text}\n\n"
        self.across_clues_text.setText(across_text.strip())

        # Update down clues
        down_text = ""
        for clue in sorted(self.current_puzzle.down_clues, key=lambda x: x.number):
            down_text += f"{clue.number}. {clue.text}\n\n"
        self.down_clues_text.setText(down_text.strip())

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