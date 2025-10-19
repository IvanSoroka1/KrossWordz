from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union

@dataclass
class KrossWordCell:
    """Represents a single cell in the crossword grid"""
    solution: str = ""
    user_input: str = ""
    is_black: bool = True
    clue_number: Optional[int] = None

    def is_empty(self) -> bool:
        return self.user_input == "" or self.user_input == self.solution

    def is_correct(self) -> bool:
        return self.user_input == self.solution

@dataclass
class Clue:
    """Represents a clue across or down"""
    number: int
    text: str
    answer: str
    start_row: int
    start_col: int
    length: int
    direction: str  # "across" or "down"

@dataclass
class KrossWordPuzzle:
    """Main crossword puzzle data structure based on .ipuz format"""
    title: str = ""
    author: str = ""
    width: int = 0
    height: int = 0
    cells: List[List[KrossWordCell]] = field(default_factory=lambda: [[]])
    across_clues: List[Clue] = field(default_factory=list)
    down_clues: List[Clue] = field(default_factory=list)
    notes: str = ""
    difficulty: str = ""
    category: str = ""
    solution_state: bool = False  # Whether to show solutions

    def initialize_grid(self, width: int, height: int):
        """Initialize empty grid"""
        self.width = width
        self.height = height
        self.cells = []
        for i in range(height):
            row = []
            for j in range(width):
                row.append(KrossWordCell())
            self.cells.append(row)

    def set_cell(self, row: int, col: int, solution: str, is_empty: bool = False, clue_number: Optional[int] = None):
        """Set a cell with its properties"""
        if 0 <= row < self.height and 0 <= col < self.width:
            self.cells[row][col] = KrossWordCell(
                solution=solution,
                user_input="",
                is_black=not is_empty,
                clue_number=clue_number
            )

    def get_clue(self, number: int, direction: str) -> Optional[Clue]:
        """Get clue by number and direction"""
        clue_list = self.across_clues if direction == "across" else self.down_clues
        return next((clue for clue in clue_list if clue.number == number), None)

    def get_all_clues(self) -> List[Clue]:
        """Get all clues (across + down)"""
        return self.across_clues + self.down_clues

    def validate_solution(self, number: int, direction: str) -> bool:
        """Validate if a clue is correctly solved"""
        clue = self.get_clue(number, direction)
        if not clue:
            return False

        # Build the answer from the grid
        answer = []
        for i in range(clue.length):
            if direction == "across":
                if clue.start_col + i >= self.width:
                    return False
                answer.append(self.cells[clue.start_row][clue.start_col + i].user_input)
            else:  # down
                if clue.start_row + i >= self.height:
                    return False
                answer.append(self.cells[clue.start_row + i][clue.start_col].user_input)

        return "".join(answer) == clue.answer