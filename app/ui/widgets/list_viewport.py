"""
ListViewport - Custom viewport to intercept and eliminate gridlines.

Intercepts paintEvent at the viewport level to prevent Qt from drawing
brown vertical lines between columns when rows are selected.
"""

from PySide6.QtCore import Qt, QElapsedTimer
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QAbstractScrollArea, QWidget, QHeaderView

from app.core.constants import CENTRAL_AREA_BG, DEBUG_LAYOUT
from app.core.logger import get_logger
logger = get_logger(__name__)


class ListViewport(QWidget):
    """Viewport personalizado que elimina líneas verticales de Qt y provee fondo estable."""
    
    def __init__(self, parent_table: QAbstractScrollArea, parent=None):
        """Inicializar viewport con tabla padre."""
        super().__init__(parent)
        self._parent_table = parent_table
        # Atributos profesionales para evitar flicker durante resize y zonas transparentes
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StaticContents, False)
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Pintar fondo sólido, eliminar líneas residuales e instrumentar."""
        t = QElapsedTimer()
        t.start()
        is_resize = getattr(self._parent_table, '_resize_in_progress', False)

        painter = QPainter(self)
        
        # 1. Pintar fondo sólido base INMEDIATAMENTE en TODO el área (solo en ventana principal)
        # En escritorio (is_desktop), dejamos que sea transparente para mostrar el DockBackgroundWidget
        if not getattr(self._parent_table, '_is_desktop', False):
            bg_color = QColor(CENTRAL_AREA_BG)
            painter.fillRect(self.rect(), bg_color)
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # 2. Limpiar líneas verticales residuales de selección
        if hasattr(self._parent_table, 'horizontalHeader'):
            header = self._parent_table.horizontalHeader()
            viewport_rect = self.rect()
            
            horizontal_scrollbar = self._parent_table.horizontalScrollBar()
            scroll_offset_x = horizontal_scrollbar.value() if horizontal_scrollbar else 0
            
            selected_rows = set()
            if hasattr(self._parent_table, 'selectedItems'):
                items = self._parent_table.selectedItems()
                for item in items:
                    if item:
                        selected_rows.add(item.row())
            
            if selected_rows:
                for col in range(self._parent_table.columnCount() - 1):
                    column_right_edge = header.sectionViewportPosition(col) + header.sectionSize(col)
                    x_pos_in_viewport = column_right_edge - scroll_offset_x
                    
                    if 0 < x_pos_in_viewport < viewport_rect.width():
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(bg_color)
                        
                        for row in selected_rows:
                            if hasattr(self._parent_table, 'rowViewportPosition'):
                                row_top = self._parent_table.rowViewportPosition(row)
                                row_height = self._parent_table.rowHeight(row)
                                if row_top >= 0:
                                    painter.drawRect(x_pos_in_viewport - 2, row_top, 4, row_height)
        
        painter.end()

        if not hasattr(self, '_paint_count_total'): self._paint_count_total = 0
        self._paint_count_total += 1
        if DEBUG_LAYOUT:
            elapsed = t.nsecsElapsed() / 1000000.0
            logger.info(f"🎨 [Viewport] Paint #{self._paint_count_total} | dur={elapsed:.2f}ms")

