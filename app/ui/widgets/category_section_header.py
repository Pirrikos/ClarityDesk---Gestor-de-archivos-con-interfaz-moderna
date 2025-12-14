"""
CategorySectionHeader - Header widget for file category sections in grid.

Displays category name as section title with a subtle separator line below.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QColor
from PySide6.QtWidgets import QLabel, QWidget


class CategorySectionHeader(QWidget):
    """Header widget displaying category name with separator line."""
    
    def __init__(self, category_label: str, parent=None):
        """Initialize section header with category label."""
        super().__init__(parent)
        self._category_label = category_label
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build the UI layout."""
        label = QLabel(self._category_label, self)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # Estilo moderno tipo Raycast
        font = QFont('Segoe UI', 11, QFont.Weight.DemiBold)
        label.setFont(font)
        label.setStyleSheet("""
            QLabel {
                color: #B0B3B8;
                background-color: transparent;
                padding: 8px 0px;
            }
        """)
        
        # Layout simple
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 16, 0, 8)
        main_layout.setSpacing(0)
        
        # Layout horizontal para el label
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(0)
        label_layout.addWidget(label)
        label_layout.addStretch()
        
        main_layout.addLayout(label_layout)
        # El separador se dibuja en paintEvent
    
    def paintEvent(self, event) -> None:
        """Paint separator line below title."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Línea horizontal fina: gris claro con 8% de opacidad
        separator_color = QColor(255, 255, 255, 20)  # rgba(255, 255, 255, 0.08) ≈ 8%
        painter.setPen(separator_color)
        
        # Dibujar línea en la parte inferior del widget
        rect = self.rect()
        y = rect.bottom() - 4  # 4px desde el borde inferior
        painter.drawLine(0, y, rect.width(), y)
        
        painter.end()

