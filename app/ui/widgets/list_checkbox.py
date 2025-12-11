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
            painter.setPen(QPen(QColor(255, 255, 255), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            
            opt = QStyleOptionButton()
            self.initStyleOption(opt)
            style = self.style()
            indicator_rect = style.subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, opt, self)
            
            center_x = indicator_rect.center().x()
            center_y = indicator_rect.center().y()
            painter.drawLine(center_x - 5, center_y, center_x - 1, center_y + 4)
            painter.drawLine(center_x - 1, center_y + 4, center_x + 5, center_y - 4)
            painter.end()

