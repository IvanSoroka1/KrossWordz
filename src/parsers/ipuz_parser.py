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
        grid_data = data.get('puzzle', []) or data.get('grid', [])
        self._parse_grid(puzzle, grid_data, data)

        # Parse clues
        clues_data = data.get('clues', {})
        self._parse_clues(puzzle, clues_data)

        return puzzle

    def _parse_grid(self, puzzle: KrossWordPuzzle, grid_data: list, data: dict = None):
        """Parse the main grid data"""

        # Check if this is v2 format with separate puzzle and solution grids
        if data and 'solution' in data:
            self._parse_v2_grid(puzzle, grid_data, data)
        else:
            # Check if this is a "staggered" format (separate clue number rows)
            # In staggered format: odd rows (1, 3, 5...) contain the actual puzzle,
            # even rows (0, 2, 4...) contain clue numbers or separators

            use_staggered = len(grid_data) >= 3 and isinstance(grid_data[1][0], str) and grid_data[1][0].isalpha()

            if use_staggered:
                self._parse_staggered_grid(puzzle, grid_data, data)
            else:
                # Fallback to v1 format
                self._parse_v1_grid(puzzle, grid_data)

    def _parse_v2_grid(self, puzzle: KrossWordPuzzle, grid_data: list, data: dict):
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

    def _parse_staggered_grid(self, puzzle: KrossWordPuzzle, grid_data: list, raw_data: dict):
        """Parse staggered format where odd rows have puzzle letters"""

        clue_numbers_from_first_row = grid_data[0] if len(grid_data) > 0 else []

        for row_idx, original_row in enumerate(grid_data):
            if row_idx % 2 == 0:  # Even rows (0, 2, 4...) - clue numbers or separators
                # Skip clue number rows, they'll be processed with corresponding puzzle cells
                continue

            actual_row_idx = row_idx // 2  # Map puzzle row to actual grid row
            if actual_row_idx >= puzzle.height:
                break

            for col_idx, cell_data in enumerate(original_row):
                if col_idx >= puzzle.width:
                    break

                cell = puzzle.cells[actual_row_idx][col_idx]

                if isinstance(cell_data, dict):
                    # Cell has structured data
                    solution = cell_data.get('solution', '')
                    is_empty = not cell_data.get('is_block', False)
                    cell.solution = solution.upper() if solution else ""
                    cell.is_black = not is_empty

                    # Handle clue numbers from this dict or from first row
                    number = cell_data.get('number')
                    if number:
                        cell.clue_number = int(number)
                    elif col_idx < len(clue_numbers_from_first_row) and clue_numbers_from_first_row[col_idx].isdigit():
                        cell.clue_number = int(clue_numbers_from_first_row[col_idx])

                elif isinstance(cell_data, str):
                    if cell_data == '.' or cell_data == '#':
                        # Black cell
                        cell.is_black = True
                        cell.solution = ""
                    else:
                        # Letter cell
                        cell.is_black = False
                        cell.solution = cell_data.upper()

                        # Also check if there's a clue number from the first row
                        if col_idx < len(clue_numbers_from_first_row) and clue_numbers_from_first_row[col_idx].isdigit():
                            cell.clue_number = int(clue_numbers_from_first_row[col_idx])

        # Also check rows 4, 6, etc. for additional clue numbers
        if len(grid_data) > 3:
            row4_clues = grid_data[4] if len(grid_data) > 4 else []
            if row4_clues and row4_clues[0].isdigit():
                for col_idx, clue_num in enumerate(row4_clues):
                    if col_idx < puzzle.width and col_idx < len(row4_clues) and clue_num.isdigit():
                        # Map to corresponding puzzle row
                        puzzle_row = 4 // 2  # Row 2 in puzzle
                        if puzzle_row < puzzle.height:
                            puzzle.cells[puzzle_row][col_idx].clue_number = int(clue_num)

        if len(grid_data) > 5:
            row6_clues = grid_data[6] if len(grid_data) > 6 else []
            if row6_clues and row6_clues[0].isdigit():
                for col_idx, clue_num in enumerate(row6_clues):
                    if col_idx < puzzle.width and col_idx < len(row6_clues) and clue_num.isdigit():
                        puzzle_row = 6 // 2  # Row 3 in puzzle
                        if puzzle_row < puzzle.height:
                            puzzle.cells[puzzle_row][col_idx].clue_number = int(clue_num)

    def _parse_flat_grid(self, puzzle: KrossWordPuzzle, grid_data: list):
        """Parse regular flat grid format"""
        for row_idx, row in enumerate(grid_data):
            if row_idx >= puzzle.height:
                break

            for col_idx, cell_data in enumerate(row):
                if col_idx >= puzzle.width:
                    break

                cell = puzzle.cells[row_idx][col_idx]

                if isinstance(cell_data, dict):
                    # Cell has structured data
                    solution = cell_data.get('solution', '')
                    is_empty = not cell_data.get('is_block', False)
                    cell.solution = solution.upper() if solution else ""
                    cell.is_black = not is_empty

                    # Handle clue numbers
                    number = cell_data.get('number')
                    if number:
                        cell.clue_number = int(number)

                elif isinstance(cell_data, str):
                    if cell_data == '.' or cell_data == '#':
                        # Black cell
                        cell.is_black = True
                        cell.solution = ""
                    elif len(cell_data) == 1:
                        # Single character letter
                        cell.is_black = False
                        cell.solution = cell_data.upper()
                    else:
                        # Multi-character sequence
                        cell.is_black = False
                        cell.solution = cell_data.upper()

        # For flat grids, automatically assign clue numbers
        current_num = 1
        for row_idx in range(puzzle.height):
            for col_idx in range(puzzle.width):
                cell = puzzle.cells[row_idx][col_idx]
                if not cell.is_black and cell.clue_number is None:
                    # Check if this is a starting cell
                    has_across = (col_idx + 1 < puzzle.width and
                                not puzzle.cells[row_idx][col_idx + 1].is_black)
                    has_down = (row_idx + 1 < puzzle.height and
                               not puzzle.cells[row_idx + 1][col_idx].is_black)

                    # Check if this cell could start a word
                    is_start_of_word = False
                    if has_across:
                        if col_idx == 0 or puzzle.cells[row_idx][col_idx - 1].is_black:
                            is_start_of_word = True
                    if has_down:
                        if row_idx == 0 or puzzle.cells[row_idx - 1][col_idx].is_black:
                            is_start_of_word = True
                    if is_start_of_word:
                        cell.clue_number = current_num
                        current_num += 1

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

    def create_sample_ipuz(self) -> str:
        """Create a sample .ipuz file for testing"""
        return {
            "version": "1.0",
            "kind": ["http://ipuz.org/crossword#1"],
            "title": "Sample Crossword",
            "author": "Test Author",
            "dimensions": {"width": 7, "height": 7},
            "grid": [
                ["#", "1", "1", "2", "2", "2", "#"],
                ["3", "C", "A", "T", "1", "B", "4"],
                ["3", "A", "#", "O", "U", "C", "E"],
                ["3", "R", "#", "M", "P", "T", "#"],
                ["5", "D", "O", "G", "6", "R", "#"],
                ["#", "7", "F", "I", "S", "H", "."],
                ["#", "#", "#", "#", ".", ".", "."]
            ],
            "clues": {
                "across": [
                    {"number": 1, "clue": "Feline pet", "answer": "CAT"},
                    {"number": 3, "clue": "Big boat", "answer": "CAR"},
                    {"number": 5, "clue": "Canine companion", "answer": "DOG"},
                    {"number": 7, "clue": "Aquatic animal", "answer": "FISH"}
                ],
                "down": [
                    {"number": 1, "clue": "Fowl", "answer": "BIRD"},
                    {"number": 2, "clue": "Computer output", "answer": "OUTPUT"},
                    {"number": 4, "clue": "Small body of water", "answer": "POND"},
                    {"number": 6, "clue": "Sea animal", "answer": "SHARK"}
                ]
            }
        }