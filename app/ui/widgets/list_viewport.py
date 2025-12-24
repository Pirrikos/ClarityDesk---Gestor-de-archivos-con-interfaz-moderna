"""
ListViewport - Custom viewport to intercept and eliminate gridlines.

Intercepts paintEvent at the viewport level to prevent Qt from drawing
brown vertical lines between columns when rows are selected.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QAbstractScrollArea, QWidget

from app.core.constants import CENTRAL_AREA_BG


class ListViewport(QWidget):
    """Viewport personalizado que elimina líneas verticales de Qt."""
    
    def __init__(self, parent_table: QAbstractScrollArea, parent=None):
        """Inicializar viewport con tabla padre."""
        super().__init__(parent)
        self._parent_table = parent_table
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Sobrepintar líneas verticales con color de fondo."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        bg_color = QColor(CENTRAL_AREA_BG)
        
        if hasattr(self._parent_table, 'horizontalHeader'):
            header = self._parent_table.horizontalHeader()
            viewport_rect = self.rect()
            
            horizontal_scrollbar = self._parent_table.horizontalScrollBar()
            scroll_offset_x = horizontal_scrollbar.value() if horizontal_scrollbar else 0
            
            selected_rows = set()
            if hasattr(self._parent_table, 'selectedItems'):
                for item in self._parent_table.selectedItems():
                    if item:
                        selected_rows.add(item.row())
            
            for col in range(self._parent_table.columnCount() - 1):
                column_right_edge = header.sectionViewportPosition(col) + header.sectionSize(col)
                x_pos_in_viewport = column_right_edge - scroll_offset_x
                
                if x_pos_in_viewport > 0 and x_pos_in_viewport < viewport_rect.width():
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(bg_color)
                    
                    if selected_rows:
                        for row in selected_rows:
                            if hasattr(self._parent_table, 'rowViewportPosition'):
                                row_top = self._parent_table.rowViewportPosition(row)
                                row_height = self._parent_table.rowHeight(row)
                                painter.drawRect(x_pos_in_viewport - 2, row_top, 4, row_height)
                    else:
                        painter.drawRect(x_pos_in_viewport - 2, 0, 4, viewport_rect.height())
        
        painter.end()

