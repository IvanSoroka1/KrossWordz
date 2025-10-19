# CrossWordz - Native Crossword Puzzle App

A native Qt/Python application for crossword puzzles that supports .ipuz file format.

## Features
- Load .ipuz files
- Interactive crossword grid
- Clue display and navigation
- Save progress
- Cross-platform (Windows, macOS, Linux)

## Dependencies
- PySide6 (Qt6 for Python)
- Python 3.8+

## Quick Start
```bash
pip install -r requirements.txt
python src/main.py
```

## Project Structure
```
crosswordz/
├── src/
│   ├── main.py           # Application entry point
│   ├── __init__.py
│   ├── ui/
│   │   ├── __init__.py
│   │   └── main_window.py  # Main application window
│   ├── models/
│   │   ├── __init__.py
│   │   └── crossword.py   # Crossword data models
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── ipuz_parser.py # .ipuz file parser
│   └── services/
│       ├── __init__.py
│       └── file_loader.py # File loading utilities
├── requirements.txt
└── README.md
```