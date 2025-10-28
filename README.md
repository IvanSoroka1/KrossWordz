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
# Optionally launch with a puzzle already selected
python src/main.py path/to/puzzle.ipuz
```

## Build a macOS App Bundle
The project ships with a PyInstaller spec that produces a signed-ready `.app` bundle with a native `.ipuz` file association.

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller --clean --noconfirm packaging/crosswordz-mac.spec
```

After the build finishes, move `dist/CrossWordz.app` into `/Applications`. macOS will read the embedded `CFBundleDocumentTypes` metadata so that `.ipuz` files show CrossWordz as the default app. Double-clicking a puzzle (or dragging it onto the Dock icon) now launches CrossWordz and loads the file immediately. If Finder was already associating `.ipuz` files with another program, open any `.ipuz` file's **Get Info** pane, change **Open with** to CrossWordz, and click **Change All...** once.

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
