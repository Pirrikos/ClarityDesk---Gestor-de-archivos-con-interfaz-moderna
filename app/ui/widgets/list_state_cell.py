"""
ListStateCell - Widget for displaying state in list view table cells.

Shows a colored horizontal bar with state text, similar to grid badge.
"""

from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QWidget

from app.ui.utils.font_manager import FontManager

# Import state constants and labels
try:
    from app.ui.widgets.state_badge_widget import (
        STATE_COLORS,
        STATE_LABELS,
    )
except ImportError:
    STATE_COLORS = {}
    STATE_LABELS = {}


class ListStateCell(QWidget):
    """Widget for displaying file state in list view table cells."""

    def __init__(self, state: Optional[str], parent=None):
        """Initialize state cell widget."""
        super().__init__(parent)
        self._state = state
        self.setFixedHeight(24)  # Height of state bar
        self.setMinimumWidth(80)
        self.setMaximumHeight(24)
        self.setStyleSheet("QWidget { background-color: transparent; border: none; }")
        
    def set_state(self, state: Optional[str]) -> None:
        """Update state and repaint."""
        self._state = state
        self.update()

    def paintEvent(self, event) -> None:
        """Draw colored bar with state text."""
        if self._state is None or self._state not in STATE_COLORS:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get state color and label
        bar_color = STATE_COLORS[self._state]
        label_text = STATE_LABELS.get(self._state, "")
        
        rect = self.rect()
        
        # Draw colored bar background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bar_color)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Draw white text
        font = FontManager.create_font("Segoe UI", FontManager.SIZE_SMALL, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        
        # Center text horizontally and vertically
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(label_text)
        text_height = metrics.height()
        text_x = (rect.width() - text_width) // 2
        text_y = (rect.height() + text_height) // 2 - metrics.descent()
        
        painter.drawText(text_x, text_y, label_text)
        
        painter.end()

    def sizeHint(self) -> QSize:
        """Return preferred widget size."""
        return QSize(120, 24)

