"""
BadgeOverlayWidget - Floating badge widget for stack tiles.

Independent widget that floats above tiles to show count badges
without being clipped by parent widget boundaries.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QWidget


class BadgeOverlayWidget(QWidget):
    """Floating badge widget for displaying stack counts."""
    
    def __init__(self, parent: QWidget = None):
        """Initialize badge overlay widget."""
        super().__init__(parent)
        self._count = 0
        self._badge_size = 22
        
        # Configure widget attributes
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFixedSize(self._badge_size, self._badge_size)
        
        # Initially hidden
        self.setVisible(False)
    
    def set_count(self, count: int) -> None:
        """Set badge count and update visibility."""
        self._count = count
        
        # Calculate badge size based on count
        badge_size = self._badge_size
        if count >= 100:
            badge_size = 26
        elif count >= 10:
            badge_size = 24
        
        # Update widget size
        self.setFixedSize(badge_size, badge_size)
        
        self.setVisible(count > 1)
        if self.isVisible():
            self.update()
    
    def paintEvent(self, event) -> None:
        """Paint circular badge with count number."""
        if self._count <= 1:
            return
        
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Calculate badge size based on count
            badge_size = self._badge_size
            if self._count >= 100:
                badge_size = 26
            elif self._count >= 10:
                badge_size = 24
            
            # Calculate font size
            font_size = 11 if self._count < 10 else 10 if self._count < 100 else 9
            
            # Draw white circular background
            rect = self.rect()
            center_x = rect.width() // 2
            center_y = rect.height() // 2
            radius = badge_size // 2
            
            # White background circle
            bg_color = QColor(255, 255, 255, 255)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(QColor(0, 0, 0, 25), 1))
            painter.drawEllipse(
                center_x - radius,
                center_y - radius,
                badge_size,
                badge_size
            )
            
            # Draw count text
            painter.setPen(QPen(QColor(26, 26, 26, 255)))
            font = QFont('Segoe UI', font_size)
            font.setWeight(QFont.Weight.Black)  # Use enum instead of integer
            painter.setFont(font)
            
            text = str(self._count)
            metrics = QFontMetrics(font)
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()
            
            # Center text in badge
            text_x = center_x - (text_width // 2)
            text_y = center_y + (text_height // 2) - metrics.descent()
            
            painter.drawText(text_x, text_y, text)
        finally:
            painter.end()
