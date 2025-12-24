"""
ListCheckbox - Custom checkbox widget for list view.

Draws checkmark when checked.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QCheckBox, QStyle, QStyleOptionButton


class CustomCheckBox(QCheckBox):
    """Checkbox that draws checkmark when checked."""
    
    def __init__(self, parent=None):
        """Initialize checkbox with proper alignment."""
        super().__init__(parent)
        self.setStyleSheet("""
            QCheckBox {
                padding: 0px;
                margin: 0px;
            }
        """)
    
    def paintEvent(self, event) -> None:
        """Custom paint to ensure checkmark is visible."""
        super().paintEvent(event)
        if self.isChecked():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            # Trazo más fino para checkbox más pequeño (indicador 11x11)
            painter.setPen(QPen(QColor(255, 255, 255), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            
            opt = QStyleOptionButton()
            self.initStyleOption(opt)
            style = self.style()
            indicator_rect = style.subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, opt, self)
            
            cx = indicator_rect.center().x()
            cy = indicator_rect.center().y()
            # Checkmark más pequeño proporcional al indicador de 11x11 (mitad del original 22x22)
            painter.drawLine(cx - 2, cy, cx - 1, cy + 2)
            painter.drawLine(cx - 1, cy + 2, cx + 2, cy - 2)
            painter.end()

