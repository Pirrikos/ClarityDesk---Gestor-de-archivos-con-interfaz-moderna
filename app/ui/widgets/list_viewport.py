"""
ListViewport - Custom viewport to intercept and eliminate gridlines.

Intercepts paintEvent at the viewport level to prevent Qt from drawing
brown vertical lines between columns when rows are selected.
"""

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QAbstractScrollArea, QWidget


class ListViewport(QWidget):
    """
    Custom viewport that intercepts Qt's gridline drawing.
    
    Overrides paintEvent to prevent Qt from drawing vertical separator
    lines between columns when rows are selected.
    """
    
    def __init__(self, parent_table: QAbstractScrollArea, parent=None):
        """
        Initialize custom viewport.
        
        Args:
            parent_table: The QTableWidget that owns this viewport
            parent: Parent widget
        """
        super().__init__(parent)
        self._parent_table = parent_table
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Override paintEvent to intercept Qt's gridline drawing.
        
        Calls the base class paintEvent first, then overpaints any
        vertical gridlines with the background color to eliminate them.
        """
        # Primero, dejar que Qt dibuje todo normalmente
        super().paintEvent(event)
        
        # Luego, interceptar y eliminar las líneas verticales entre columnas
        # Estas líneas son dibujadas por Qt cuando hay selección en modo lista
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # Color de fondo para sobrepintar las líneas marrones
        bg_color = QColor(17, 19, 24)  # #111318
        
        # Obtener el header para calcular posiciones de columnas
        if hasattr(self._parent_table, 'horizontalHeader'):
            header = self._parent_table.horizontalHeader()
            viewport_rect = self.rect()
            
            # Obtener el desplazamiento horizontal del scrollbar
            horizontal_scrollbar = self._parent_table.horizontalScrollBar()
            scroll_offset_x = horizontal_scrollbar.value() if horizontal_scrollbar else 0
            
            # Obtener las filas seleccionadas para sobrepintar solo en esas áreas
            selected_rows = set()
            if hasattr(self._parent_table, 'selectedItems'):
                for item in self._parent_table.selectedItems():
                    if item:
                        selected_rows.add(item.row())
            
            # Sobre pintar las líneas verticales entre columnas
            # Solo pintar entre columnas visibles
            for col in range(self._parent_table.columnCount() - 1):
                # Calcular la posición del borde derecho de la columna
                column_right_edge = header.sectionViewportPosition(col) + header.sectionSize(col)
                
                # Ajustar para el desplazamiento horizontal
                x_pos_in_viewport = column_right_edge - scroll_offset_x
                
                # Solo sobrepintar si la línea está dentro del área visible
                if x_pos_in_viewport > 0 and x_pos_in_viewport < viewport_rect.width():
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(bg_color)
                    
                    # Si hay filas seleccionadas, solo sobrepintar en esas filas
                    if selected_rows:
                        for row in selected_rows:
                            if hasattr(self._parent_table, 'rowViewportPosition'):
                                row_top = self._parent_table.rowViewportPosition(row)
                                row_height = self._parent_table.rowHeight(row)
                                # Dibujar un rectángulo más ancho para cubrir completamente la línea
                                painter.drawRect(x_pos_in_viewport - 2, row_top, 4, row_height)
                    else:
                        # Si no hay selección, sobrepintar toda la altura (por si acaso)
                        painter.drawRect(x_pos_in_viewport - 2, 0, 4, viewport_rect.height())
        
        painter.end()

