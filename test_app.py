#!/usr/bin/env python3
"""
Test script for CrossWordz application
"""

import sys
import os
sys.path.append('src')

from models.crossword import CrosswordPuzzle, Clue, CrosswordCell
from parsers.ipuz_parser import IPUZParser
from services.file_loader import FileLoaderService

def test_parser():
    """Test the IPUZ parser"""
    print("Testing IPUZ parser...")

    parser = IPUZParser()
    file_loader = FileLoaderService()

    # Test sample file
    sample_path = "sample.ipuz"
    if os.path.exists(sample_path):
        try:
            puzzle = file_loader.load_ipuz_file(sample_path)
            print(f"✓ Successfully loaded puzzle: {puzzle.title}")
            print(f"  Size: {puzzle.width}x{puzzle.height}")
            print(f"  Across clues: {len(puzzle.across_clues)}")
            print(f"  Down clues: {len(puzzle.down_clues)}")
            return True
        except Exception as e:
            print(f"✗ Error loading sample: {e}")
            return False
    else:
        print("✗ Sample file not found")
        return False

def test_data_structures():
    """Test the data structures"""
    print("\nTesting data structures...")

    try:
        # Create a test puzzle
        puzzle = CrosswordPuzzle(title="Test Puzzle", width=3, height=3)
        puzzle.initialize_grid(3, 3)

        # Set some cells
        puzzle.set_cell(0, 0, "C", False, 1)
        puzzle.set_cell(0, 1, "A", False, 1)
        puzzle.set_cell(0, 2, "T", False, 1)
        puzzle.set_cell(1, 0, "#", True)  # Black cell

        # Test clue retrieval
        puzzle.across_clues.append(Clue(1, "Feline", "CAT", 0, 0, 3, "across"))

        clue = puzzle.get_clue(1, "across")
        if clue and clue.answer == "CAT":
            print("✓ Data structures working correctly")
            return True
        else:
            print("✗ Data structure test failed")
            return False

    except Exception as e:
        print(f"✗ Error in data structures: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting CrossWordz tests...")

    results = [
        test_data_structures(),
        test_parser()
    ]

    if all(results):
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())