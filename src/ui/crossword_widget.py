from __future__ import annotations

from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QWidget

from models.krossword import KrossWordCell, KrossWordPuzzle


class KrossWordWidget(QWidget):
    """Widget for displaying and interacting with a crossword puzzle."""

    cell_selected = Signal(int, int)  # row, col
    value_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.puzzle: Optional[KrossWordPuzzle] = None
        self.selected_row = 0
        self.selected_col = 0
        self.highlight_mode = "across"  # "across" or "down"
        self.font_size = 16
        self.cell_size = 40
        self.setMouseTracking(True)
        self.setMinimumSize(400, 400)
        print("DEBUG: KrossWordWidget initialized")
        self.setFocusPolicy(Qt.StrongFocus)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_puzzle(self, puzzle: KrossWordPuzzle) -> None:
        self.puzzle = puzzle
        widget_width = max(400, self.puzzle.width * self.cell_size)
        widget_height = max(400, self.puzzle.height * self.cell_size + 50)
        self.setMinimumSize(widget_width, widget_height)
        self.update()

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

    def handle_global_navigation(self, key: int) -> None:
        self._handle_navigation(key)

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
        if not self.puzzle:
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

    def event(self, event):  # noqa: N802
        if event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
                print("DEBUG: Tab key caught in event() method")
                self._handle_navigation(event.key())
                return True
        return super().event(event)

    def keyPressEvent(self, event):  # noqa: N802
        if not self.puzzle:
            return

        key = event.key()
        print(f"DEBUG: KrossWordWidget keyPressEvent called with key: {key} ({Qt.Key_Tab})")

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
        elif Qt.Key_0 <= key <= Qt.Key_Z:
            self._handle_letter_input(key)
        elif key in (Qt.Key_Backspace, Qt.Key_Delete):
            print(
                "Backspace/Delete pressed. Current cell: "
                f"({self.selected_row}, {self.selected_col}), current content: "
                f"'{self.puzzle.cells[self.selected_row][self.selected_col].user_input}'"
            )
            self._handle_delete(key)
        elif key == Qt.Key_Return:
            print(f"DEBUG: Return key detected: {key}")
            self._handle_navigation(key)
        elif key == Qt.Key_Space:
            self._toggle_highlight_mode()
        else:
            super().keyPressEvent(event)

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

        painter.setPen(QPen(Qt.darkBlue))
        info_text = f"{self.puzzle.title} - {self.puzzle.width}x{self.puzzle.height}"
        painter.drawText(10, self.puzzle.height * self.cell_size + 30, info_text)

    def _draw_cells(self, painter: QPainter) -> None:
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
                painter.fillRect(x, y, self.cell_size, self.cell_size, QBrush(Qt.white))

        painter.setPen(QPen(Qt.black))
        font = QFont("Arial", self.font_size + 8, QFont.Normal)
        painter.setFont(font)

        has_input = bool(cell.user_input)
        has_solution = bool(cell.solution)

        if has_input:
            text = cell.user_input.upper()
            text_rect = painter.fontMetrics().boundingRect(text)
            text_x = x + (self.cell_size - text_rect.width()) // 2
            #text_y = y + (self.cell_size + text_rect.height()) // 2 - 2
            padding = 1
            baseline = self.cell_size - padding - painter.fontMetrics().descent()
            text_y = y + baseline


            painter.save()
            if cell.correct:
                painter.setPen(QPen(Qt.blue))
            else:
                painter.setPen(QPen(Qt.black))
            painter.drawText(text_x, text_y, text)
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
            triangle = QPolygon(
                [
                    QPoint(x + self.cell_size, y),              # top-right corner
                    QPoint(x + self.cell_size - 16, y),         # a bit to the left
                    QPoint(x + self.cell_size, y + 16),         # a bit down the right edge
                ]
            )
            painter.drawPolygon(triangle)
            # draw small white circle in the triangle
            circle_radius = 2
            circle_center_x = x + self.cell_size - 6   
            circle_center_y = y + 6

            painter.setBrush(QBrush(Qt.white))
            painter.drawEllipse(
                QPoint(circle_center_x, circle_center_y),
                circle_radius,
                circle_radius,
            )
            painter.restore()


        if cell.clue_number:
            painter.setPen(QPen(Qt.darkBlue))
            small_font = QFont("Arial", 8)
            painter.setFont(small_font)
            painter.drawText(x + 2, y + 12, str(cell.clue_number))

    # ------------------------------------------------------------------
    # Movement helpers and editing
    # ------------------------------------------------------------------

    def _handle_letter_input(self, key: int) -> None:
        cell = self.puzzle.cells[self.selected_row][self.selected_col]
        if cell.is_black:
            return

        char = ""
        if Qt.Key_0 <= key <= Qt.Key_Z:
            char = chr(key).upper()

        if char:
            was_empty = cell.user_input == ""
            print(
                f"DEBUG: Typed '{char}' in cell ({self.selected_row}, {self.selected_col}), "
                f"was_empty: {was_empty}"
            )
            cell.user_input = char

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
                print("DEBUG: Cell was empty and not last character, moving to adjacent character")
                self._loop_to_empty_in_entry(is_last_character)
            elif not is_last_character:
                print("DEBUG: Cell was filled and not last character, using regular movement")
                if self.highlight_mode == "down":
                    self._move_down()
                else:
                    self._move_right()

            self.value_changed.emit()
            self.update()

    def _loop_to_empty_in_entry(self, is_last_character: bool) -> None:
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
            search_start = self.selected_col + 1
            if search_start > end[0]:
                search_start = start[0]

            for col in range(search_start, end[0] + 1):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return

            for col in range(start[0], self.selected_col + 1):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return
        else:
            col = start[0]
            search_start = self.selected_row + 1
            if search_start > end[1]:
                search_start = start[1]

            for row in range(search_start, end[1] + 1):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return

            for row in range(start[1], self.selected_row + 1):
                if self.puzzle.cells[row][col].user_input == "":
                    self.selected_row, self.selected_col = (row, col)
                    print(f"DEBUG: Found first empty position: {(row, col)}")
                    self.cell_selected.emit(self.selected_row, self.selected_col)
                    self.update()
                    return

        print("DEBUG: No empty squares found in entry, moving to next character")
        if not is_last_character:
            self.highlight_mode = original_mode
            if self.highlight_mode == "down":
                self._move_down()
            else:
                self._move_right()

    def _handle_delete(self, key: int) -> None:
        cell = self.puzzle.cells[self.selected_row][self.selected_col]
        print(
            f"Delete handler: cell.is_black={cell.is_black}, user_input='{cell.user_input}'"
        )
        if not cell.is_black:
            if cell.user_input and not cell.correct:
                print(f"Deleting current cell content: {cell.user_input}")
                cell.user_input = ""
                self.value_changed.emit()
                self.update()
                if cell.incorrect:
                    cell.incorrect = False
            else:
                print("Cell is empty, moving to previous cell")
                original_row, original_col = self.selected_row, self.selected_col
                self._move_to_previous_cell()
                print(
                    "Moved to previous cell: "
                    f"({self.selected_row}, {self.selected_col}), original was "
                    f"({original_row}, {original_col})"
                )
                if (self.selected_row, self.selected_col) != (original_row, original_col):
                    prev_cell = self.puzzle.cells[self.selected_row][self.selected_col]
                    print(
                        f"Previous cell content: '{prev_cell.user_input}', is_black: {prev_cell.is_black}"
                    )
                    if prev_cell and not prev_cell.is_black and not prev_cell.correct:
                        prev_cell.user_input = ""
                        self.value_changed.emit()
                        if prev_cell.incorrect:
                            prev_cell.incorrect = False

                else:
                    print("Could not find a valid previous cell")
                self.update()

    def _toggle_highlight_mode(self) -> None:
        self.highlight_mode = "down" if self.highlight_mode == "across" else "across"
        self.cell_selected.emit(self.selected_row, self.selected_col)
        self.update()

    def _handle_navigation(self, key: int) -> None:
        print(f"DEBUG: _handle_navigation called with key: {key}")
        if key in (Qt.Key_Tab, Qt.Key_Backtab):
            print("DEBUG: Tab key pressed - calling _move_to_next_entry_start")
            self._move_to_next_entry_start()
        elif key == Qt.Key_Right:
            print("DEBUG: Right key pressed - calling move_right")
            self.move_right()
        elif key == Qt.Key_Return:
            print("DEBUG: Return key pressed - calling move_down")
            self.move_down()

    def _move_to_next_entry_start(self) -> None:
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

        if self.highlight_mode == "across":
            across_clues = self.puzzle.across_clues
            if across_clues:
                current_index = -1
                if current_clue:
                    for i, clue in enumerate(across_clues):
                        if clue.number == current_clue.number:
                            current_index = i
                            break

                if current_index == len(across_clues) - 1:
                    self.highlight_mode = "down"
                    if self.puzzle.down_clues:
                        next_clue = self.puzzle.down_clues[0]
                        print(
                            "Switching from across to down, moved to clue "
                            f"#{next_clue.number}: {next_clue.text[:50]}..."
                        )
                    else:
                        return
                else:
                    next_index = (current_index + 1) % len(across_clues)
                    next_clue = across_clues[next_index]
                    print(
                        f"Moved to next across clue #{next_clue.number}: "
                        f"{next_clue.text[:50]}..."
                    )
        else:
            down_clues = self.puzzle.down_clues
            if not down_clues:
                return

            current_index = -1
            if current_clue:
                for i, clue in enumerate(down_clues):
                    if clue.number == current_clue.number:
                        current_index = i
                        break

            if current_index == len(down_clues) - 1:
                self.highlight_mode = "across"
                if self.puzzle.across_clues:
                    next_clue = self.puzzle.across_clues[0]
                    print(
                        "Switching from down to across, moved to clue "
                        f"#{next_clue.number}: {next_clue.text[:50]}..."
                    )
                else:
                    return
            else:
                next_index = (current_index + 1) % len(down_clues)
                next_clue = down_clues[next_index]
                print(
                    f"Moved to next down clue #{next_clue.number}: "
                    f"{next_clue.text[:50]}..."
                )

        if next_clue:
            self.selected_row = next_clue.start_row
            self.selected_col = next_clue.start_col

        self.cell_selected.emit(self.selected_row, self.selected_col)
        self.update()

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
