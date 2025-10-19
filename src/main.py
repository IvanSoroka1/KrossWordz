#!/usr/bin/env python3
"""
CrossWordz - Crossword Puzzle Application
A native Qt-based application for solving crossword puzzles that supports .ipuz format files.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow

def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("CrossWordz")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CrossWordz")

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()