import json
from typing import Dict, Any, Optional
from models.krossword import KrossWordPuzzle, KrossWordCell, Clue

class IPUZParser:
    """Parser for .ipuz format files"""

    def __init__(self):
        self.supported_versions = ["1.0", "1.1", "2.0"]

    def parse(self, file_path: str) -> KrossWordPuzzle:
        """Parse a .ipuz file and return a KrossWordPuzzle object"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Error reading .ipuz file: {e}")

        # Validate it's a crossword file
        kind = data.get('kind', [])
        if 'http://ipuz.org/crossword#1' not in kind:
            raise ValueError("File is not a valid crossword file (missing kind)")

        version = data.get('version', '1.0')
        if version not in self.supported_versions:
            print(f"Warning: .ipuz version {version} not explicitly supported, attempting to parse")

        # Extract metadata
        title = data.get('title', 'Untitled Crossword')
        author = data.get('author', '')
        notes = data.get('notes', '')
        difficulty = data.get('difficulty', '')
        category = data.get('category', '')

        # Get grid dimensions
        width = data.get('dimensions', {}).get('width', 0)
        height = data.get('dimensions', {}).get('height', 0)

        if width <= 0 or height <= 0:
            raise ValueError("Invalid grid dimensions")

        # Create puzzle
        puzzle = KrossWordPuzzle(
            title=title,
            author=author,
            notes=notes,
            difficulty=difficulty,
            category=category,
            width=width,
            height=height
        )

        # Initialize empty grid
        puzzle.initialize_grid(width, height)

        # Parse grid - v2 uses "puzzle" instead of "grid"
        grid_data = data.get('puzzle', [])
        self._parse_grid(puzzle, grid_data, data)

        if data.get("saved", []):
            self._load_saved(puzzle, data.get("saved", []))

        # Parse clues
        clues_data = data.get('clues', {})
        self._parse_clues(puzzle, clues_data)

        self.get_fillable_cell_count(puzzle)

        return puzzle
    
    def get_fillable_cell_count(self, puzzle: KrossWordPuzzle):
        puzzle.fillable_cell_count = 0
        for row in puzzle.cells:
            for cell in row:
                if not cell.is_black:
                    puzzle.fillable_cell_count += 1
                    
    def _load_saved(self, puzzle:KrossWordPuzzle, saved: list):
        for row_idx in range(puzzle.height):
            if row_idx >= len(saved):
                break
            for col_idx in range(puzzle.width):
                if col_idx >= len(saved[row_idx]):
                    break
                puzzle.cells[row_idx][col_idx].user_input = saved[row_idx][col_idx]

    def _parse_grid(self, puzzle: KrossWordPuzzle, grid_data: list, data: dict):
        """Parse v2 format with separate puzzle and solution grids"""
        solution_grid = data.get('solution', [])
        for row_idx in range(puzzle.height):
            if row_idx >= len(grid_data) or row_idx >= len(solution_grid):
                break

            puzzle_row = grid_data[row_idx]
            solution_row = solution_grid[row_idx]

            for col_idx in range(puzzle.width):
                if col_idx >= len(puzzle_row) or col_idx >= len(solution_row):
                    break

                cell = puzzle.cells[row_idx][col_idx]
                puzzle_cell = puzzle_row[col_idx]
                solution_char = solution_row[col_idx]

                # Parse puzzle cell for clue numbers
                if isinstance(puzzle_cell, dict) and 'cell' in puzzle_cell:
                    # Handle shading/highlight styles
                    style = puzzle_cell.get('style')
                    if isinstance(style, dict):
                        if style.get('highlight'):
                            cell.is_shaded = True
                        if style.get("shapebg") == "circle":
                            cell.is_circled = True

                    clue_number = puzzle_cell['cell']
                    if clue_number > 0:
                        # White cell with a clue number
                        cell.is_black = False
                        cell.clue_number = clue_number
                    elif clue_number == 0:
                        # Empty white cell (no clue number, but still playable)
                        cell.is_black = False
                        cell.solution = ""

                # Override solution from solution grid if available
                if isinstance(solution_char, str) and len(solution_char) == 1:
                    cell.solution = solution_char.upper()
        

    def _parse_clues(self, puzzle: KrossWordPuzzle, clues_data: dict):
        """Parse the clues data"""
        # Parse across clues (handle both 'across' and 'Across')
        across_clues = clues_data.get('across', []) or clues_data.get('Across', [])
        self._parse_clue_list(puzzle, across_clues, "across")

        # Parse down clues (handle both 'down' and 'Down')
        down_clues = clues_data.get('down', []) or clues_data.get('Down', [])
        self._parse_clue_list(puzzle, down_clues, "down")

    def _parse_clue_list(self, puzzle: KrossWordPuzzle, clues_list: list, direction: str):
        """Parse a list of clues"""
        clue_list = []

        for clue_data in clues_list:
            if isinstance(clue_data, dict):
                # Modern format: {"clue": "text", "answer": "answer"}
                clue_text = clue_data.get('clue', '')
                answer = clue_data.get('answer', '').upper()
                clue_number = clue_data.get('number')
            elif isinstance(clue_data, list):
                # Most common v2 format: [number, "text"]
                clue_number = clue_data[0] if len(clue_data) > 0 else None
                clue_text = clue_data[1] if len(clue_data) > 1 else ""
                answer = ""  # Will be extracted from grid
            else:
                # Fallback format
                clue_number = None
                clue_text = str(clue_data)
                answer = ""

            # Extract answer from grid for v2 format
            if not answer:
                answer = self._extract_answer_from_grid(puzzle, clue_number, direction)

            clue = Clue(
                number=int(clue_number) if clue_number else 0,
                text=clue_text,
                answer=answer.upper() if answer else "",
                start_row=0,  # Will be set later
                start_col=0,  # Will be set later
                length=len(answer) if answer else 0,
                direction=direction
            )
            clue_list.append(clue)

        # Find starting positions for each clue
        for clue in clue_list:
            if clue.number > 0:
                clue.start_row, clue.start_col = self._find_clue_start(puzzle, clue, direction)

        # Add to appropriate list
        if direction == "across":
            puzzle.across_clues = clue_list
        else:
            puzzle.down_clues = clue_list

    def _extract_answer_from_grid(self, puzzle: KrossWordPuzzle, clue_number: int, direction: str) -> str:
        """Extract answer from grid for v2 format where answer isn't provided"""
        if direction == "across":
            # Scan across clue from starting position
            for row in range(puzzle.height):
                for col in range(puzzle.width):
                    cell = puzzle.cells[row][col]
                    if cell.clue_number == clue_number:
                        answer = ""
                        # Scan across to get full answer
                        for c in range(col, puzzle.width):
                            curr_cell = puzzle.cells[row][c]
                            if not curr_cell.is_black:
                                answer += curr_cell.solution
                            else:
                                break
                        return answer
        else:  # down
            # Scan down clue from starting position
            for row in range(puzzle.height):
                for col in range(puzzle.width):
                    cell = puzzle.cells[row][col]
                    if cell.clue_number == clue_number:
                        answer = ""
                        # Scan down to get full answer
                        for r in range(row, puzzle.height):
                            curr_cell = puzzle.cells[r][col]
                            if not curr_cell.is_black:
                                answer += curr_cell.solution
                            else:
                                break
                        return answer

        return ""

    def _find_clue_start(self, puzzle: KrossWordPuzzle, clue: Clue, direction: str) -> tuple:
        """Find the starting position of a clue in the grid"""
        target_length = clue.length
        target_answer = clue.answer

        for row_idx in range(puzzle.height):
            for col_idx in range(puzzle.width):
                if puzzle.cells[row_idx][col_idx].clue_number == clue.number:
                    # Found the starting cell for this clue number
                    return row_idx, col_idx

        # Fallback: search by answer pattern
        return 0, 0  # Default position