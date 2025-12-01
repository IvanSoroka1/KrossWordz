from __future__ import annotations

from math import sqrt
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, QPoint, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygon, QPolygonF
from PySide6.QtWidgets import QWidget, QApplication, QMenu, QSizePolicy

from models.krossword import KrossWordCell, KrossWordPuzzle
from ui.ai_windows import ai_window
from ui.lookup import open_onelook

class KrossWordWidget(QWidget):
    """Widget for displaying and interacting with a crossword puzzle."""

    cell_selected = Signal(int, int)  # row, col
    pencil_mode_toggle_requested = Signal()
    value_changed = Signal()
    display_message = Signal(bool)
    request_clue_explanation = Signal(str, str)
    cell_count_changed = Signal(int)
    greyout_clue = Signal(int, str, bool)
    resize_current_clue = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.puzzle: Optional[KrossWordPuzzle] = None
        self.selected_row = 0
        self.selected_col = 0
        self.highlight_mode = "across"  # "across" or "down"
        self.pencil_mode = False
        self.font_size = 16
        self.cells_filled = 0
        self.puzzle_solved = False
        self.cell_size = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setMouseTracking(True)
        self.setMinimumSize(200, 200)
        print("DEBUG: KrossWordWidget initialized")
        self.setFocusPolicy(Qt.StrongFocus)
        self.dirty = False
        self.referenced_cells = []
    

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def select_first_square(self):
        for j in range(self.puzzle.height): # it would be unusual for a puzzle to have the first row be all black
            for i in range(self.puzzle.width):        
                if not self.puzzle.cells[j][i].is_black:
                    self.selected_row = j
                    self.selected_col = i
                    return 

        raise Exception("Puzzle has no non-black cells")

    def get_grid_width(self):
        if not self.puzzle:
            return None
        return self.cell_size * self.puzzle.width

    def show_context_menu(self, pos: QPoint) -> None:
        row = pos.y()//self.cell_size
        col = pos.x()//self.cell_size

        if row != self.selected_row or col != self.selected_col:
            return
            
        clue = self.find_clue_for_cell(row, col, self.highlight_mode)

        menu = QMenu(self)
        explain_action = menu.addAction("Explain this clue and answer pair")
        explain_action.triggered.connect(lambda : self.request_clue_explanation.emit(clue.text, clue.answer))
        lookup_action = menu.addAction("Lookup this answer in the dictionary")
        lookup_action.triggered.connect(lambda : open_onelook(clue.answer))
        menu.exec(self.mapToGlobal(pos))
    

    def focusNextPrevChild(self, next: bool) -> bool:
        return False  # stop Qt from moving focus on Tab/Shift+Tab

    def find_clue_for_cell(self, row, col, direction):
        """Find the clue for a cell even if it doesn't have a number"""
        # Always find the start of the word this cell belongs to
        # This ensures we get the correct clue for the current direction
        start_row, start_col = self.find_word_start(row, col, direction)

        if start_row is not None and start_col is not None:
            start_cell = self.puzzle.cells[start_row][start_col]
            if start_cell.clue_number:
                return self.puzzle.get_clue(start_cell.clue_number, direction)
        return None

    def find_word_start(self, row, col, direction):
        """Find the starting cell of a word in the given direction"""
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

    def set_puzzle(self, puzzle: KrossWordPuzzle) -> None:
        self.highlight_mode = "across"
        self.selected_row = 0
        self.selected_col = 0
        self.puzzle = puzzle
        self._recompute_cell_metrics()
        self.select_first_square()
        self.update()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        if self.puzzle:
            self._recompute_cell_metrics()
            self.update()

    def _recompute_cell_metrics(self) -> None:
        """Update cell size based on the current widget dimensions."""
        if not self.puzzle or self.puzzle.width <= 0 or self.puzzle.height <= 0:
            return

        rect = self.contentsRect()
        available_width = rect.width() or self.width()
        available_height = rect.height() or self.height()

        if available_width <= 0 or available_height <= 0:
            return

        cell_width = max(1, available_width // self.puzzle.width)
        cell_height = max(1, available_height // self.puzzle.height)
        self.cell_size = max(1, min(cell_width, cell_height))
        self.font_size = int(self.cell_size * 0.65)
        self.resize_current_clue.emit(self.cell_size*self.puzzle.width)


    def get_current_cell(self) -> Optional[KrossWordCell]:
        if self.puzzle and 0 <= self.selected_row < self.puzzle.height:
            if 0 <= self.selected_col < self.puzzle.width:
                return self.puzzle.cells[self.selected_row][self.selected_col]
        return None

    def get_current_position(self) -> Optional[Tuple[int, int]]:
        if not self.puzzle:
            return None
        return self.selected_row, self.selected_col

    def get_current_word_coordinates(self) -> List[Tuple[int, int]]:
        if not self.puzzle:
            return []

        start, end = self._get_word_bounds(
            self.selected_row, self.selected_col, self.highlight_mode
        )
        if not start or not end:
            return []

        cells: List[Tuple[int, int]] = []
        if self.highlight_mode == "across":
            row = start[1]
            for col in range(start[0], end[0] + 1):
                cells.append((row, col))
        else:
            col = start[0]
            for row in range(start[1], end[1] + 1):
                cells.append((row, col))
        return cells


    # ------------------------------------------------------------------
    # Qt event handlers
    # ------------------------------------------------------------------

    def paintEvent(self, event):  # noqa: N802 (Qt override)
        if not self.puzzle:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._draw_cells(painter)
        self._draw_grid(painter)

    def mousePressEvent(self, event):  # noqa: N802
        if not self.puzzle or event.button() == Qt.MouseButton.RightButton:
            return
        col = int(round(event.position().x() // self.cell_size))
        row = int(round(event.position().y() // self.cell_size))
        if 0 <= row < self.puzzle.height and 0 <= col < self.puzzle.width:
            if not self.puzzle.cells[row][col].is_black:
                if row == self.selected_row and col == self.selected_col:
                    self.highlight_mode = "down" if self.highlight_mode == "across" else "across"
                else:
                    self.selected_row = row
                    self.selected_col = col
                self.setFocus()
                self.cell_selected.emit(row, col)
                self.update()
                self.dirty = True

    def event(self, event):  # noqa: N802
        if event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
                mods = QApplication.keyboardModifiers()
                self._handle_navigation(event.key(), mods & Qt.ShiftModifier)
                self.dirty = True
                return True
        return super().event(event)

    def keyPressEvent(self, event):  # noqa: N802
        if not self.puzzle:
            return
        key = event.key()
        mods = event.modifiers()
        puzzle_modified = True
        if key == Qt.Key_Left:
            if self.highlight_mode == "down":
                self.highlight_mode = "across"
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
            else:
                self._move_left()
        elif key == Qt.Key_Right:
            if self.highlight_mode == "down":
                self.highlight_mode = "across"
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
            else:
                self._move_right()
        elif key == Qt.Key_Up:
            if self.highlight_mode == "across":
                self.highlight_mode = "down"
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
            else:
                self._move_up()
        elif key == Qt.Key_Down:
            if self.highlight_mode == "across":
                self.highlight_mode = "down"
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
            else:
                self._move_down()
        elif key == Qt.Key_Period:
            self.pencil_mode_toggle_requested.emit()
            return
        elif Qt.Key_0 <= key <= Qt.Key_Z:
            self._handle_letter_input(key, mods)
        elif key in (Qt.Key_Backspace, Qt.Key_Delete):
            self._handle_delete(key)
        elif key == Qt.Key_Return:
            print(f"DEBUG: Return key detected: {key}")
            self._handle_navigation(key)
        elif key == Qt.Key_Space:
            self._toggle_highlight_mode()
        else:
            puzzle_modified = False
            super().keyPressEvent(event)

        if puzzle_modified:
            self.dirty = True

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------
    def _draw_grid(self, painter: QPainter) -> None:
        painter.setPen(QPen(Qt.gray, 2))

        for row in range(1, self.puzzle.height):
            y = row * self.cell_size
            painter.drawLine(0, y, self.puzzle.width * self.cell_size - 1, y)

        for col in range(1, self.puzzle.width):
            x = col * self.cell_size
            painter.drawLine(x, 0, x, self.puzzle.height * self.cell_size - 1)

        painter.drawLine(1, 1, self.puzzle.width * self.cell_size - 1, 1)
        painter.drawLine(
            1,
            self.puzzle.height * self.cell_size - 1,
            self.puzzle.width * self.cell_size - 1,
            self.puzzle.height * self.cell_size - 1,
        )
        painter.drawLine(1, 1, 1, self.puzzle.height * self.cell_size - 1)
        painter.drawLine(
            self.puzzle.width * self.cell_size - 1,
            1,
            self.puzzle.width * self.cell_size - 1,
            self.puzzle.height * self.cell_size - 1,
        )


    def _draw_cells(self, painter: QPainter) -> None:
        self._get_referenced_cells()
        for row in range(self.puzzle.height):
            for col in range(self.puzzle.width):
                self._draw_cell(painter, row, col)

    def _draw_cell(self, painter: QPainter, row: int, col: int) -> None:
        cell = self.puzzle.cells[row][col]
        x = col * self.cell_size
        y = row * self.cell_size

        if cell.is_black:
            painter.fillRect(x, y, self.cell_size, self.cell_size, QBrush(Qt.black))
        else:
            is_selected_cell = row == self.selected_row and col == self.selected_col
            should_highlight = False

            if self.highlight_mode in ("across", "down") and self.puzzle:
                start, end = self._get_word_bounds(
                    self.selected_row, self.selected_col, self.highlight_mode
                )
                if start and end:
                    start_col, start_row = start
                    end_col, end_row = end
                    if self.highlight_mode == "across":
                        if row == start_row and start_col <= col <= end_col:
                            should_highlight = True
                    else:
                        if col == start_col and start_row <= row <= end_row:
                            should_highlight = True

            if should_highlight:
                if is_selected_cell:
                    painter.fillRect(
                        x,
                        y,
                        self.cell_size,
                        self.cell_size,
                        QBrush(QColor(255, 255, 150)),
                    )
                else:
                    painter.fillRect(
                        x,
                        y,
                        self.cell_size,
                        self.cell_size,
                        QBrush(QColor(150, 200, 255)),
                    )
            else:
                if cell.is_shaded:
                    painter.fillRect(x, y, self.cell_size, self.cell_size, QColor(194, 194, 194))
                else:
                    painter.fillRect(x, y, self.cell_size, self.cell_size, QBrush(Qt.white))

        if [row, col] in self.referenced_cells:
           painter.fillRect(
                        x,
                        y,
                        self.cell_size,
                        self.cell_size,
                        QBrush(QColor(255, 252, 50)),
                    ) 

        painter.setPen(QPen(Qt.black))
        #font = QFont("Arial Light", self.font_size, QFont.Light)
        font = QFont("Arial", self.font_size, QFont.Normal)
        painter.setFont(font)

        if cell.is_circled:
            painter.save()
            painter.setPen(QPen(Qt.black, 1))
            painter.drawEllipse(QPoint(x + self.cell_size / 2, y + self.cell_size / 2), self.cell_size/2-2 , self.cell_size/2-2 )
            painter.restore()

        has_input = bool(cell.user_input)
        has_solution = bool(cell.solution)

        if has_input:
            text = cell.user_input.upper()
            metrics = painter.fontMetrics()
            text_rect = metrics.boundingRect(text)
            max_text_width = self.cell_size - 4

            if text_rect.width() > max_text_width:
                # Shrink the font so multi-character rebus entries still fit inside the square.
                font = painter.font()
                current_size = font.pointSizeF() if font.pointSizeF() > 0 else float(font.pointSize())
                # Scale to fit, but don't go below a legible minimum.
                scaled_size = max(8.0, current_size * (max_text_width / text_rect.width()))
                font.setPointSizeF(scaled_size)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_rect = metrics.boundingRect(text)

            text_x = x + (self.cell_size - text_rect.width()) / 2.0
            #padding = 1
            #baseline = self.cell_size - padding - metrics.descent()
            baseline = self.cell_size - metrics.descent()
            text_y = y + baseline


            painter.save()
            if cell.corrected:
                painter.setPen(QPen(Qt.blue))
            elif cell.pencilled:
                painter.setPen(QPen(Qt.gray))
            else:
                painter.setPen(QPen(Qt.black))
            painter.drawText(QPointF(text_x, text_y), text)
            painter.restore()

        if cell.incorrect and has_input and has_solution:
            painter.save()
            painter.setPen(QPen(Qt.red, 3))
            painter.drawLine(x + 2, y + 2, x + self.cell_size - 2, y + self.cell_size - 2)
            painter.restore()
        
        if cell.revealed:
            painter.save()
            painter.setBrush(QBrush(Qt.red))
            painter.setPen(Qt.NoPen)

            triangle = QPolygonF(
                [
                    QPointF(x + self.cell_size, y),              # top-right corner
                    QPointF(x + (2/3)*self.cell_size, y),         # a bit to the left
                    QPointF(x + self.cell_size, y + self.cell_size/3),         # a bit down the right edge
                ]
            )

            painter.drawPolygon(triangle)
            # the center of an equilateral triangle with lengths of a, is (1/3)a, (1/3)a. This is found by adding the three coordinates of the triangle and diving by the number of coordinates.

            circle_center_x = x + (8/9)*self.cell_size
            circle_center_y = y + (1/9)*self.cell_size
            circle_radius =  0.5*(sqrt(2)/6)*(1/3)*self.cell_size

            painter.setBrush(QBrush(Qt.white))
            painter.drawEllipse(
                QPointF(circle_center_x, circle_center_y),
                circle_radius,
                circle_radius,
            )
            painter.restore()


        if cell.clue_number:
            painter.setPen(QPen(Qt.black))
            small_font = QFont("Arial")
            small_font.setPointSizeF(self.cell_size * 0.25)
            painter.setFont(small_font)
            padding = self.cell_size * 0.1
            painter.drawText(
                QRectF(x + padding, y + padding, self.cell_size / 2, self.cell_size / 2),
                Qt.AlignLeft | Qt.AlignTop,
                str(cell.clue_number),
            )

    # ------------------------------------------------------------------
    # Movement helpers and editing
    # ------------------------------------------------------------------

    def _get_referenced_cells(self):
        self.referenced_cells = []
        clue = self.find_clue_for_cell(self.selected_row, self.selected_col, self.highlight_mode)
        for reference in clue.references:
            direction = reference['direction'].lower()
            reference_clue = self.puzzle.get_clue(reference['number'], direction)
            if not reference_clue:
                continue
            cell_coords = list(self._get_word_start(reference_clue.start_row, reference_clue.start_col, direction))

            list_index = 1 if direction == "across" else 0
            bound = self.puzzle.width if direction == "across" else self.puzzle.height

            while cell_coords[list_index] < bound and not self.puzzle.cells[cell_coords[0]][cell_coords[1]].is_black:
                cell_coords_copy = cell_coords.copy()
                self.referenced_cells.append(cell_coords_copy)
                cell_coords[list_index] += 1



    def _handle_letter_input(self, key: int, rebus: bool) -> None:
        cell = self.puzzle.cells[self.selected_row][self.selected_col]
        if cell.is_black or self.puzzle_solved:
            return
        
        if cell.corrected:
            if self.highlight_mode == "down":
                self._move_down()
            else:
                self._move_right()
            return


        char = ""
        if Qt.Key_0 <= key <= Qt.Key_Z:
            char = chr(key).upper()

        if char:
            was_empty = cell.user_input == ""
            if rebus:
                cell.user_input += char
            else:
                cell.user_input = char

            if was_empty:
                self.fill_cell_signals(minus=False)

            if self.pencil_mode:
                cell.pencilled = True
            else:
                cell.pencilled = False

            if cell.incorrect:
                cell.incorrect = False

            # if it's a rebus cell, then don't move
            if not rebus:
                start, end = self._get_word_bounds(
                    self.selected_row, self.selected_col, self.highlight_mode
                )
                is_last_character = False

                if start and end:
                    if self.highlight_mode == "across":
                        is_last_character = self.selected_col == end[0]
                    else:
                        is_last_character = self.selected_row == end[1]

                if was_empty:
                    # if the current cell you're editing is empty, loop to the next empty cell
                    self._loop_to_empty_in_entry(is_last_character)
                elif not is_last_character:
                    # if the current cell you're editing is not the last character in the entry and is not empty
                    # move to the next cell
                    if self.highlight_mode == "down":
                        self._move_down()
                    else:
                        self._move_right()
                # if the cell is not empty and it is the last cell then don't move
        self.check_filled_puzzle()

        self.value_changed.emit()

        self.update()

    def check_filled_word(self):
        for direction in ("across", "down"):
            (start, end) = self._get_word_bounds(self.selected_row, self.selected_col, direction)
            if self.word_filled(start[0], start[1], direction):
                start_cell = self.puzzle.cells[start[1]][start[0]]
                self.greyout_clue.emit(start_cell.clue_number, direction, True)
    
    def ungrey_text(self):
        for direction in ("across", "down"):
            (start, end) = self._get_word_bounds(self.selected_row, self.selected_col, direction)
            start_cell = self.puzzle.cells[start[1]][start[0]]
            self.greyout_clue.emit(start_cell.clue_number, direction, False)

            
    
    def check_filled_puzzle(self):
        if self.cells_filled == self.puzzle.fillable_cell_count:
            for row in self.puzzle.cells:
                for cell in row:
                    if cell.is_black:
                        continue
                    if not cell.is_correct():
                        self.display_message.emit(False)
                        return
            self.puzzle_solved = True
            self.display_message.emit(True)


    def _loop_to_empty_in_entry(self, is_last_character: bool, next_cell: bool = True) -> None:
        if not self.puzzle:
            return

        start, end = self._get_word_bounds(
            self.selected_row, self.selected_col, self.highlight_mode
        )
        if not start or not end:
            return

        original_row, original_col = self.selected_row, self.selected_col
        original_mode = self.highlight_mode

        print(
            f"DEBUG: Original position: ({original_row}, {original_col}), "
            f"entry start: {start}, end: {end}"
        )

        if self.highlight_mode == "across":
            row = start[1]
            search_start = self.selected_col + 1 if next_cell == True else self.selected_col
            if search_start > end[0]:
                search_start = start[0]

            for col in range(search_start, end[0] + 1):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return

            for col in range(start[0], self.selected_col + 1 if next_cell == True else self.selected_col):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return
        else:
            col = start[0]
            search_start = self.selected_row + 1 if next_cell == True else self.selected_row
            if search_start > end[1]:
                search_start = start[1]

            for row in range(search_start, end[1] + 1):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return

            for row in range(start[1], self.selected_row + 1 if next_cell == True else self.selected_row):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return

        print("DEBUG: No empty squares found in entry, moving to next character")
        if next_cell:
            if not is_last_character:
                self.highlight_mode = original_mode
                if self.highlight_mode == "down":
                    self._move_down()
                else:
                    self._move_right()

    def _handle_delete(self, key: int) -> None:
        cell = self.puzzle.cells[self.selected_row][self.selected_col]
        if not cell.is_black:
            # if the current cell is filled and is not corrected, then delete it and don't move back
            if cell.user_input and not cell.corrected:
                cell.user_input = ""
                self.fill_cell_signals(minus=True)

                self.update()
                if cell.incorrect:
                    cell.incorrect = False
            else:
                original_row, original_col = self.selected_row, self.selected_col
                self._move_to_previous_cell()
                if (self.selected_row, self.selected_col) != (original_row, original_col):
                    prev_cell = self.puzzle.cells[self.selected_row][self.selected_col]
                    if prev_cell and not prev_cell.is_black and not prev_cell.corrected:
                        if prev_cell.user_input:
                            prev_cell.user_input = ""
                            self.fill_cell_signals(minus=True)
                        if prev_cell.incorrect:
                            prev_cell.incorrect = False
                    self.cell_selected.emit(self.selected_row, self.selected_col)

                self.update()

    def _toggle_highlight_mode(self) -> None:
        self.highlight_mode = "down" if self.highlight_mode == "across" else "across"
        self.cell_selected.emit(self.selected_row, self.selected_col)
        self.update()

    def _handle_navigation(self, key: int, shift: bool) -> None:
        print(f"DEBUG: _handle_navigation called with key: {key}")
        if key in (Qt.Key_Tab, Qt.Key_Backtab):
            print("DEBUG: Tab key pressed - calling _move_to_next_entry_start")
            self._move_to_next_entry_start(shift)
        elif key == Qt.Key_Right:
            print("DEBUG: Right key pressed - calling move_right")
            self.move_right()
        elif key == Qt.Key_Return:
            print("DEBUG: Return key pressed - calling move_down")
            self.move_down()

    def _move_to_next_entry_start(self, shift: bool) -> None:
        if not self.puzzle:
            return

        start_row, start_col = self._find_word_start_in_widget(
            self.selected_row, self.selected_col, self.highlight_mode
        )
        current_clue = None
        next_clue = None

        if start_row is not None and start_col is not None:
            start_cell = self.puzzle.cells[start_row][start_col]
            if start_cell.clue_number:
                current_clue = self.puzzle.get_clue(start_cell.clue_number, self.highlight_mode)

        clues = self.puzzle.across_clues if self.highlight_mode == "across" else self.puzzle.down_clues

        end = len(clues)
        step = 1
        if shift:
            end = -1
            step = -1

        foundNonFilledWord = False
        current_index = -1
        if current_clue:
            for i, clue in enumerate(clues):
                if clue.number == current_clue.number:
                    current_index = i
                    break

        original_index = current_index
        for i in range(2):
            if clues:
                for j in range((current_index + 1) if not shift else (current_index -1), end, step):
                    next_clue = clues[j]
                    if not self.word_filled(next_clue.start_col, next_clue.start_row):
                        foundNonFilledWord = True
                        break
                if foundNonFilledWord:  
                    break
                else:         
                    clues = self.puzzle.across_clues if self.highlight_mode == "down" else self.puzzle.down_clues
                    self.highlight_mode = "across" if self.highlight_mode == "down" else "down"
                    if not shift:
                        current_index = -1
                        end = len(clues)
                    else:
                        current_index = len(clues)
        
        # if the grid is completely full, then just go to the next numerical clue 
        clue_found = False
        if not foundNonFilledWord:
            if not shift:
                if original_index + 1 < len(clues):
                    next_clue = clues[original_index + 1]
                    clue_found = True
            else:
                if original_index - 1 >= 0:
                    next_clue = clues[original_index - 1]
                    clue_found = True
            if not clue_found:
                clues = self.puzzle.across_clues if self.highlight_mode == "down" else self.puzzle.down_clues
                self.highlight_mode = "across" if self.highlight_mode == "down" else "down"
                next_clue = clues[0] if not shift else clues[-1]

        if next_clue:
            self.selected_row = next_clue.start_row
            self.selected_col = next_clue.start_col
            self._loop_to_empty_in_entry(False, False)

        self.cell_selected.emit(self.selected_row, self.selected_col)
        self.update()
    
    def word_filled(self, word_start_col, word_start_row, direction = None):
        if not direction:
            direction = self.highlight_mode
        if direction == "across":
            i = word_start_col
            while i < self.puzzle.width and not self.puzzle.cells[word_start_row][i].is_black:
                if self.puzzle.cells[word_start_row][i].user_input == "":
                        return False
                i += 1
        else:
            i = word_start_row
            while i < self.puzzle.height and not self.puzzle.cells[i][word_start_col].is_black:
                if self.puzzle.cells[i][word_start_col].user_input == "":
                        return False
                i += 1
        return True

    def fill_cell_signals(self, minus:bool) -> None:
        if minus:
            self.cells_filled -= 1
            self.ungrey_text()
        else:
            self.cells_filled += 1
            self.check_filled_word()
        self.cell_count_changed.emit(self.cells_filled)

    def _handle_directional_move(self, delta_row: int, delta_col: int) -> None:
        new_row = self.selected_row + delta_row
        new_col = self.selected_col + delta_col

        while 0 <= new_row < self.puzzle.height and 0 <= new_col < self.puzzle.width:
            if not self.puzzle.cells[new_row][new_col].is_black:
                self.selected_row = new_row
                self.selected_col = new_col
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
                return
            new_row += delta_row
            new_col += delta_col

    def _move_left(self) -> None:
        self._handle_directional_move(0, -1)

    def _move_right(self) -> None:
        self._handle_directional_move(0, 1)

    def _move_up(self) -> None:
        self._handle_directional_move(-1, 0)

    def _move_down(self) -> None:
        self._handle_directional_move(1, 0)

    def move_right(self) -> None:
        if self.selected_col < self.puzzle.width - 1:
            self.selected_col += 1
            self._skip_black_cells()
        self.cell_selected.emit(self.selected_row, self.selected_col)
        self.update()

    def move_down(self) -> None:
        if self.selected_row < self.puzzle.height - 1:
            self.selected_row += 1
            self._skip_black_cells()
        self.cell_selected.emit(self.selected_row, self.selected_col)
        self.update()

    def move_to_next_cell(self) -> None:
        if self.highlight_mode == "down":
            self._move_to_next_empty_cell_down()
        else:
            self._move_to_next_empty_cell_across()

    def _is_cell_empty(self, row: int, col: int) -> bool:
        if not self.puzzle or row < 0 or row >= self.puzzle.height or col < 0 or col >= self.puzzle.width:
            return False
        cell = self.puzzle.cells[row][col]
        return not cell.is_black and cell.user_input == ""

    def _move_to_next_empty_cell_across(self) -> None:
        original_row, original_col = self.selected_row, self.selected_col
        new_col = self.selected_col + 1

        while new_col < self.puzzle.width:
            if (
                not self.puzzle.cells[self.selected_row][new_col].is_black
                and self._is_cell_empty(self.selected_row, new_col)
            ):
                self.selected_col = new_col
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
                return
            new_col += 1

        print("Reached end of current across word with no empty cells, staying in position")

    def _move_to_next_empty_cell_down(self) -> None:
        original_row, original_col = self.selected_row, self.selected_col
        new_row = self.selected_row + 1

        while new_row < self.puzzle.height:
            if (
                not self.puzzle.cells[new_row][self.selected_col].is_black
                and self._is_cell_empty(new_row, self.selected_col)
            ):
                self.selected_row = new_row
                self.cell_selected.emit(self.selected_row, self.selected_col)
                self.update()
                return
            new_row += 1

        print("Reached end of current down word with no empty cells, staying in position")

    def _move_to_previous_cell(self) -> None:
        original_row, original_col = self.selected_row, self.selected_col
        print(
            f"Moving to previous cell from ({original_row}, {original_col}) in {self.highlight_mode} mode"
        )

        if self.highlight_mode == "down":
            new_row = self.selected_row - 1
            if new_row >= 0:
                while new_row >= 0:
                    if not self.puzzle.cells[new_row][self.selected_col].is_black:
                        self.selected_row = new_row
                        print(
                            f"Found previous cell above: ({self.selected_row}, {self.selected_col})"
                        )
                        return
                    new_row -= 1
                print("No valid cells above")

            if self.selected_col > 0:
                self.selected_col -= 1
                print(f"Moving left to column {self.selected_col}")
                new_row = self.puzzle.height - 1
                while new_row >= 0:
                    if not self.puzzle.cells[new_row][self.selected_col].is_black:
                        self.selected_row = new_row
                        print(
                            f"Found previous cell in previous column: ({self.selected_row}, {self.selected_col})"
                        )
                        return
                    new_row -= 1
                print(f"No valid cells in previous column {self.selected_col}")
        else:
            new_col = self.selected_col - 1
            if new_col >= 0:
                while new_col >= 0:
                    if not self.puzzle.cells[self.selected_row][new_col].is_black:
                        self.selected_col = new_col
                        print(
                            f"Found previous cell to the left: ({self.selected_row}, {self.selected_col})"
                        )
                        return
                    new_col -= 1
                print("No valid cells to the left")

            if self.selected_row > 0:
                self.selected_row -= 1
                print(f"Moving up to row {self.selected_row}")
                new_col = self.puzzle.width - 1
                while new_col >= 0:
                    if not self.puzzle.cells[self.selected_row][new_col].is_black:
                        self.selected_col = new_col
                        print(
                            f"Found previous cell in previous row: ({self.selected_row}, {self.selected_col})"
                        )
                        return
                    new_col -= 1
                print(f"No valid cells in previous row {self.selected_row}")

        self.selected_row = original_row
        self.selected_col = original_col
        print("Could not find valid previous cell, staying in original position")

    def _skip_black_cells(self) -> None:
        while (
            0 <= self.selected_row < self.puzzle.height
            and 0 <= self.selected_col < self.puzzle.width
            and self.puzzle.cells[self.selected_row][self.selected_col].is_black
        ):
            self.selected_col += 1
            if self.selected_col >= self.puzzle.width:
                self.selected_row += 1
                self.selected_col = 0
                if self.selected_row >= self.puzzle.height:
                    self.selected_row = 0
                    self.selected_col = 0
                    break

    def _skip_black_cells_reverse(self) -> None:
        original_row, original_col = self.selected_row, self.selected_col
        while (
            0 <= self.selected_row < self.puzzle.height
            and 0 <= self.selected_col < self.puzzle.width
            and self.puzzle.cells[self.selected_row][self.selected_col].is_black
        ):
            self.selected_col -= 1
            if self.selected_col < 0:
                self.selected_row -= 1
                self.selected_col = self.puzzle.width - 1
                if (self.selected_row, self.selected_col) == (original_row, original_col):
                    break
                if self.selected_row < 0:
                    self.selected_row = self.puzzle.height - 1
                    self.selected_col = self.puzzle.width - 1
                    break

    def _skip_black_cells_up(self) -> None:
        original_row, original_col = self.selected_row, self.selected_col
        while (
            0 <= self.selected_row < self.puzzle.height
            and 0 <= self.selected_col < self.puzzle.width
            and self.puzzle.cells[self.selected_row][self.selected_col].is_black
        ):
            self.selected_row -= 1
            if self.selected_row < 0:
                self.selected_col -= 1
                self.selected_row = self.puzzle.height - 1
                if (self.selected_row, self.selected_col) == (original_row, original_col):
                    break
                if self.selected_col < 0:
                    self.selected_col = self.puzzle.width - 1
                    self.selected_row = self.puzzle.height - 1
                    break

    # ------------------------------------------------------------------
    # Word range helpers
    # ------------------------------------------------------------------

    def _get_word_bounds(self, row: int, col: int, direction: str):
        if not self.puzzle:
            return None, None

        start_col, start_row = col, row
        if direction == "across":
            while start_col > 0 and not self.puzzle.cells[start_row][start_col - 1].is_black:
                start_col -= 1
        else:
            while start_row > 0 and not self.puzzle.cells[start_row - 1][start_col].is_black:
                start_row -= 1

        end_col, end_row = col, row
        if direction == "across":
            while end_col < self.puzzle.width - 1 and not self.puzzle.cells[end_row][end_col + 1].is_black:
                end_col += 1
        else:
            while end_row < self.puzzle.height - 1 and not self.puzzle.cells[end_row + 1][end_col].is_black:
                end_row += 1

        return (start_col, start_row), (end_col, end_row)
    
    def _get_word_start(self, row: int, col: int, direction: str):
        if direction == "across":
            start_col = col
            while start_col > 0 and not self.puzzle.cells[row][start_col - 1].is_black:
                start_col -= 1
            return row, start_col
        else:
            start_row = row
            while start_row > 0 and not self.puzzle.cells[start_row - 1][col].is_black:
                start_row -= 1
            return start_row, col

    def set_pencil_mode(self):
        self.pencil_mode = not self.pencil_mode
        self.dirty = True
        return self.pencil_mode

    def _find_word_start_in_widget(self, row: int, col: int, direction: str):
        if direction == "across":
            start_col = col
            while start_col > 0:
                if self.puzzle.cells[row][start_col - 1].is_black:
                    break
                start_col -= 1
            return row, start_col
        else:
            start_row = row
            while start_row > 0:
                if self.puzzle.cells[start_row - 1][col].is_black:
                    break
                start_row -= 1
            return start_row, col
