"""
CategorySectionHeader - Header widget for file category sections in grid.

Displays category name as section title with a subtle separator line below.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.utils.font_manager import FontManager

SEPARATOR_COLOR_RGBA = (255, 255, 255, 20)
SEPARATOR_BOTTOM_OFFSET = 4


class CategorySectionHeader(QWidget):
    """Header widget displaying category name with separator line."""
    
    def __init__(self, category_label: str, parent=None):
        """Initialize section header with category label."""
        super().__init__(parent)
        self._category_label = category_label
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        label = QLabel(self._category_label, self)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        FontManager.safe_set_font(
            label,
            'Segoe UI',
            FontManager.SIZE_NORMAL,
            QFont.Weight.DemiBold
        )
        label.setStyleSheet("""
            QLabel {
                color: #B0B3B8;
                background-color: transparent;
                padding: 8px 0px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 8, 0, 8)
        main_layout.setSpacing(0)
        
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 12, 0)
        label_layout.setSpacing(0)
        label_layout.addStretch(1)
        label_layout.addWidget(label, 0)
        
        main_layout.addLayout(label_layout)
        # El separador se dibuja en paintEvent
    
    def paintEvent(self, event) -> None:
        """Paint separator line below title."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        separator_color = QColor(*SEPARATOR_COLOR_RGBA)
        painter.setPen(separator_color)
        
        rect = self.rect()
        y = rect.bottom() - SEPARATOR_BOTTOM_OFFSET
        painter.drawLine(0, y, rect.width(), y)
        
        painter.end()

