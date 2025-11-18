import math
from ui.SelectableLabel import SelectableLabel
from PySide6.QtCore import Qt, QPoint, QTimer, QEasingCurve, Signal
from PySide6.QtGui import QFont, QTextCursor, QTextDocument 
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
    QTextEdit,
    QScrollArea,
    QApplication,
    QMenu
)


class CluesTextEdit(SelectableLabel):
    """Text edit styled for clues that forwards navigation keys to the parent."""

    selectClue = Signal(int, str)

    def __init__(self, number, direction, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setWordWrap(True)
        self.setTextFormat(Qt.RichText)

        self._default_stylesheet = self.styleSheet()
        self.number = number
        self.direction = direction
        self.styelsheet = dict()
        self.styelsheet["highlight"] = ""
        self.styelsheet["grey"] = ""




    def setText(self, text):
        """Set clue text and resize the label to tightly wrap the content."""
        super().setText(text)
        self._shrink_to_fit()

    def keyPressEvent(self, event):  # noqa: N802 (Qt interface)
        if event.key() in (
            Qt.Key_Left,
            Qt.Key_Right,
            Qt.Key_Up,
            Qt.Key_Down,
            Qt.Key_Space,
            Qt.Key_Tab,
        ):
            event.ignore()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selectClue.emit(self.number, self.direction)
        super().mousePressEvent(event)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._shrink_to_fit()

    def set_highlighted(self, highlighted: bool) -> None:
        """Toggle highlight coloring on the text edit background."""
        self.styelsheet["highlight"] = "background-color: #47c8ff;" if highlighted else ""
        self.applyStyleSheet()
        
    def set_grey_text(self, make_grey: bool) -> None:
        self.styelsheet["grey"] = "color: grey;" if make_grey else ""
        self.applyStyleSheet()

    def applyStyleSheet(self):
        self.setStyleSheet(self.styelsheet["highlight"] + self.styelsheet["grey"])

    def _shrink_to_fit(self) -> None:
        """Match label height to wrapped text height."""
        available_width = self.width()
        if available_width <= 0:
             return

        margins = self.contentsMargins()
        text_width = max(1, available_width - (margins.left() + margins.right()))

        doc = QTextDocument()
        doc.setDefaultFont(self.font())
        doc.setHtml(self.text())
        doc.setDocumentMargin(0)
        doc.setTextWidth(text_width)

        height = math.ceil(max(doc.size().height(), self.fontMetrics().height()))
        height += margins.top() + margins.bottom()

        self.setMinimumHeight(height)
        self.setMaximumHeight(height)


class CluesPanel(QWidget):
    clue_selected = Signal(int, str)

    """Container showing across and down clues side by side."""

    def __init__(self, across_clues: list[str], down_clues: list[str], parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)
        self.setLayout(self.layout)
        self.clues = dict()
        self.clueSides = dict()
        self._scroll_areas = dict()
        self._highlighted_key = None
        self._side_highlighted_key = None
        self.highlight_color = "#47c8ff"
        self.default_color = "#868686"
        self.scroll_layout = None
        self.across_text_edit = self._create_section(self.layout, "ACROSS", across_clues)
        self.down_text_edit = self._create_section(self.layout, "DOWN", down_clues)

    def _create_section(self, parent_layout: QHBoxLayout, title: str, clues: list[str] ) -> CluesTextEdit:
        container = QWidget(self)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(4)
        container.setLayout(section_layout)

        label = QLabel(title)
        label.setFont(QFont("Arial", 11, QFont.Bold))
        section_layout.addWidget(label)

        scroll_area = QScrollArea(container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        section_layout.addWidget(scroll_area)
        self._scroll_areas[title.lower()] = scroll_area

        scroll_content = QWidget(scroll_area)
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(4)
        scroll_content.setLayout(self.scroll_layout)
        scroll_area.setWidget(scroll_content)

        last_text_edit = None

        for clue in clues:
            clue_layout = QHBoxLayout()
            sideBox = QWidget()
            sideBox.setStyleSheet(f"background-color: {self.default_color};") 
            sideBox.setFixedWidth(12)
            text_edit = CluesTextEdit(clue.number, clue.direction, scroll_content)
            text_edit.selectClue.connect(self._handle_clue_click)
            self.clues[(clue.number, clue.direction)] = text_edit
            self.clueSides[(clue.number, clue.direction)] = sideBox
            text_edit.setText(f"<b>{clue.number}</b> {clue.text.strip()}")

            clue_layout.addWidget(sideBox)  
            clue_layout.addWidget(text_edit)
            self.scroll_layout.addLayout(clue_layout)
            last_text_edit = text_edit


        # text_edit = CluesTextEdit(container)
        # section_layout.addWidget(text_edit)
        parent_layout.addWidget(container)
        return last_text_edit

    def greyout_text(self, number: int, direction: str, make_grey: bool) -> None:
        key=(number, direction)
        text_edit = self.clues.get(key)
        if text_edit:
            text_edit.set_grey_text(make_grey)
    def grey_all_clues(self) -> None:
        for text_edit in self.clues.values():
            text_edit.set_grey_text(True)

    def highlight_clue(self, number: int, direction: str) -> None:
        """Highlight the requested clue and reset the previous one."""
        key = (number, direction)
        text_edit = self.clues.get(key)
        if key == self._highlighted_key:
            if text_edit:
                self._scroll_clue_into_view(direction, text_edit)
            return

        if self._highlighted_key and self._highlighted_key in self.clues:
            self.clues[self._highlighted_key].set_highlighted(False)

        if text_edit:
            text_edit.set_highlighted(True)
            self._highlighted_key = key
            self._scroll_clue_into_view(direction, text_edit)
        else:
            self._highlighted_key = None
    
    def highlight_clue_side(self, number: int, direction: str) -> None:
        key = (number, direction)
        sideBox = self.clueSides.get(key)
        if key == self._side_highlighted_key:
            if sideBox:
                self._scroll_clue_into_view(direction, sideBox)
            return

        if self._side_highlighted_key and self._side_highlighted_key in self.clueSides:
            self.clueSides[self._side_highlighted_key].setStyleSheet(f"background-color: {self.default_color};")

        if sideBox:
            sideBox.setStyleSheet(f"background-color: {self.highlight_color};")
            self._side_highlighted_key = key
            self._scroll_clue_into_view(direction, sideBox)
        else:
            self._side_highlighted_key = None

    def clear_highlight(self) -> None:
        """Remove highlight from the currently highlighted clue, if any."""
        if self._highlighted_key and self._highlighted_key in self.clues:
            self.clues[self._highlighted_key].set_highlighted(False)
        self._highlighted_key = None

    def _handle_clue_click(self, number: int, direction: str) -> None:
        """React to clue clicks by highlighting and bubbling the event."""
        self.highlight_clue(number, direction)
        self.clue_selected.emit(number, direction)

    def _scroll_clue_into_view(self, direction: str, text_edit: CluesTextEdit) -> None:
        """Scroll the appropriate area so the clue appears at the top."""
        scroll_area = self._scroll_areas.get(direction.lower())
        if not scroll_area:
            return

        scrollbar = scroll_area.verticalScrollBar()
        if not scrollbar:
            return

        container = scroll_area.widget()
        if not container:
            return

        top_left = text_edit.mapTo(container, QPoint(0, 0))
        target_y = max(0, top_left.y())
        target = min(target_y, scrollbar.maximum())

        current = scrollbar.value()
        if current == target:
            return

        timer = getattr(scroll_area, "_scroll_timer", None)
        if timer and timer.isActive():
            timer.stop()

        duration_ms = 300
        interval_ms = 16
        steps = max(1, duration_ms // interval_ms)
        easing = QEasingCurve(QEasingCurve.OutCubic)
        step = 0

        timer = QTimer(scroll_area)

        def update_scroll():
            nonlocal step
            step += 1
            progress = min(1.0, step / steps)
            eased = easing.valueForProgress(progress)
            value = current + (target - current) * eased
            scrollbar.setValue(int(round(value)))
            if progress >= 1.0:
                timer.stop()
                scrollbar.setValue(target)
                scroll_area._scroll_timer = None

        timer.timeout.connect(update_scroll)
        scroll_area._scroll_timer = timer
        timer.start(interval_ms)
        update_scroll()



    def set_across_text(self, text: str) -> None:
        self.across_text_edit.setText(text)

    def set_down_text(self, text: str) -> None:
        self.down_text_edit.setText(text)

    def clear(self) -> None:
        self.across_text_edit.clear()
        self.down_text_edit.clear()
