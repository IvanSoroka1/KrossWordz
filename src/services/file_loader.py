import os
from typing import Optional
from parsers.ipuz_parser import IPUZParser
from models.crossword import KrossWordPuzzle

class FileLoaderService:
    """Service for loading crossword puzzle files"""

    def __init__(self):
        self.parser = IPUZParser()

    def load_ipuz_file(self, file_path: str) -> KrossWordPuzzle:
        """Load a crossword puzzle from a .ipuz file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.lower().endswith('.ipuz'):
            raise ValueError("File must have .ipuz extension")

        return self.parser.parse(file_path)

    def load_from_directory(self, directory: str) -> list:
        """Load all .ipuz files from a directory"""
        if not os.path.isdir(directory):
            raise ValueError(f"Directory not found: {directory}")

        crossword_files = []
        for filename in os.listdir(directory):
            if filename.lower().endswith('.ipuz'):
                try:
                    file_path = os.path.join(directory, filename)
                    puzzle = self.load_ipuz_file(file_path)
                    crossword_files.append((filename, puzzle))
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

        return crossword_files

    def get_file_info(self, file_path: str) -> dict:
        """Get basic information about a crossword file without fully parsing it"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read(1000)  # Read just enough for basic info
                return {
                    'file_size': len(data),
                    'has_content': len(data.strip()) > 0
                }
        except Exception as e:
            return {
                'error': str(e),
                'file_size': 0,
                'has_content': False
            }