from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QMessageBox

class Check_and_Reveal(QObject):
    grey_all_clues = Signal()
    def __init__(self, crossword_widget, current_puzzle):
        super().__init__()
        self.crossword_widget = crossword_widget    
        self.current_puzzle = current_puzzle

    def reveal_current_letter(self):
        """Reveal the currently selected letter."""
        if not self.current_puzzle:
            QMessageBox.warning(self, "Warning", "Load a puzzle before revealing letters")
            return
        cell = self.crossword_widget.get_current_cell()
        if not cell or cell.is_black:
            return
        if cell.user_input == '':
            cell.reveal()
            self.crossword_widget.fill_cell_signals(minus=False)
        else:
            cell.reveal()
        self.crossword_widget.check_filled_puzzle()
        self.crossword_widget.update()

    def reveal_current_word(self):
        """Reveal the word that contains the currently selected cell."""
        position = self.crossword_widget.get_current_position()
        if not position:
            return
        word_cells = self.crossword_widget.get_current_word_coordinates()
        for cell_row, cell_col in word_cells:
            cell = self.current_puzzle.cells[cell_row][cell_col]
            if cell.is_black:
                continue

            # if you call cell.reveal() here then cell.user_input will never be ''

            if cell.user_input == '':
                cell.reveal()
                self.crossword_widget.fill_cell_signals(minus=False)
            else:
                cell.reveal()

            self.crossword_widget.check_filled_puzzle()
        
        self.crossword_widget.update()

    def reveal_answers(self):
        """Reveal current answers"""
        for row in self.current_puzzle.cells:
            for cell in row:
                if not cell.is_black and cell.solution:
                    cell.reveal()
        self.grey_all_clues.emit()
        self.crossword_widget.filled_cells = self.crossword_widget.puzzle.fillable_cell_count
        self.crossword_widget.cell_count_changed.emit(self.crossword_widget.filled_cells)
        self.crossword_widget.display_message.emit(True)
        self.crossword_widget.update()
    
    def check_current_letter(self):
        """Verify the currently selected letter."""
        cell = self.crossword_widget.get_current_cell()
        if not cell or cell.is_black or not cell.user_input:
            return
        if cell.is_correct():
            cell.corrected = True
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
            return
        word_cells = self.crossword_widget.get_current_word_coordinates()
        for cell_row, cell_col in word_cells:
            cell = self.current_puzzle.cells[cell_row][cell_col]
            if cell.is_black:
                continue
            if not cell.user_input:
                continue
            if cell.is_correct():
                cell.corrected = True
            else:
                cell.incorrect = True

        self.crossword_widget.update()

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
                    cell.corrected = True
                else:
                    cell.incorrect = True
        self.crossword_widget.update()