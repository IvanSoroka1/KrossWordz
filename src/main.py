#!/usr/bin/env python3
"""CrossWordz application entry point with file association support."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Tuple

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


class CrossWordzApplication(QApplication):
    """Custom QApplication that forwards macOS FileOpen events."""
    file_requested = Signal(str)
    def event(self, event):  # noqa: D401 - Qt override
        if event.type() == QEvent.FileOpen:
            file_path = event.file()
            if file_path:
                self.file_requested.emit(file_path)
            return True
        return super().event(event)


def _parse_command_line(argv: List[str]) -> Tuple[Optional[str], List[str]]:
    """Return (ipuz_file, argv_for_qt)."""

    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("ipuz_file", nargs="?", help="Path to a .ipuz puzzle to open")
    args, qt_args = parser.parse_known_args(argv[1:])
    qt_argv = [argv[0], *qt_args]
    return args.ipuz_file, qt_argv


def main():
    """Main entry point for the application."""
    requested_file, qt_argv = _parse_command_line(sys.argv)
    app = CrossWordzApplication(qt_argv)

    # Set application info
    app.setApplicationName("CrossWordz")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CrossWordz")

    # Create and show main window
    window = MainWindow()
    app.file_requested.connect(window.load_puzzle_from_path)

    if requested_file:
        window.load_puzzle_from_path(requested_file)

    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
