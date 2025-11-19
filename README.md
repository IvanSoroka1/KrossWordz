# KrossWordz - Native Crossword Puzzle App

A native Qt/Python application for crossword puzzles that supports .ipuz file format.

## Features
- Load `.ipuz` files
- Interactive crossword grid with keyboard/mouse editing and pencil mode
- Clue display, navigation, highlighting, and clue lookup
- Timer tracking with pause/resume controls
- Check/reveal tools for letters, words, or the entire grid
- Enter Rebuses (hold down shift)
- Save and restore progress inside the `.ipuz` file
- Optional AI-powered clue explanations through Gemini
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

### Gemini AI Integration
CrossWordz can ask Google’s Gemini models to explain any clue. Set your Gemini API key in **Preferences → AI** (stored via `QSettings`) and the AI tab becomes active. Without a key, CrossWordz runs normally; the AI tab simply shows a reminder to configure the key.

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
KrossWordz/
├── src/
│   ├── main.py                   # Application entry point
│   ├── ui/
│   │   ├── main_window.py        # Main application window
│   │   ├── crossword_widget.py   # Grid rendering & input
│   │   ├── clues_panel.py        # Across/Down clue lists
│   │   ├── current_clue_widget.py# Current clue display
│   │   ├── check_and_reveal.py   # Check/reveal dialog logic
│   │   ├── preferences.py        # Settings UI
│   │   ├── ai_windows.py         # Gemini AI integration pane
│   │   ├── SelectableLabel.py    # Selectable QLabel helper
│   │   └── lookup.py             # External dictionary lookup
│   ├── models/
│   │   └── krossword.py          # Puzzle data structures
│   ├── parsers/
│   │   └── ipuz_parser.py        # `.ipuz` loader
│   └── services/
│       └── file_loader.py        # File loading utilities
├── assets/                       # Icons and other assets
├── packaging/                    # PyInstaller specs & helpers
├── requirements.txt
└── README.md
```
