"""
DockSeparator - Separator widget for dock layout.

Visual separator between system icons and application stacks, similar to macOS Dock.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget


class DockSeparator(QWidget):
    """Separator widget for dock - vertical line divider."""
    
    def __init__(self, parent=None):
        """Initialize dock separator."""
        super().__init__(parent)
        self.setFixedWidth(1)  # Thin vertical line
        self.setMinimumHeight(50)  # Minimum height
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    
    def paintEvent(self, event) -> None:
        """Paint vertical separator line."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Subtle gray line similar to macOS Dock separator
        # macOS uses a very subtle gray line with some transparency
        separator_color = QColor(255, 255, 255, 40)  # White with low opacity
        
        painter.setPen(separator_color)
        # Draw vertical line in the center
        center_x = self.width() // 2
        painter.drawLine(center_x, 8, center_x, self.height() - 8)
        
        painter.end()

