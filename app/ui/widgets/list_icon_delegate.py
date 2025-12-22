"""
ListIconDelegate - Professional delegate for list view rendering.

Controls all drawing to prevent Qt's default selection borders.
"""

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import QHeaderView, QStyle, QStyleOptionViewItem, QStyledItemDelegate, QTableWidget


class ListViewDelegate(QStyledItemDelegate):
    """
    Unified delegate for all list view columns.
    
    Completely controls item rendering to prevent default Qt selection borders.
    """
    
    MARGIN_LEFT = 12
    ICON_SIZE_SELECTED = QSize(30, 30)
    ICON_SIZE_NORMAL = QSize(28, 28)
    
    def __init__(self, parent=None, column_index: int = 1):
        """
        Initialize delegate.
        
        Args:
            parent: Parent widget (QTableWidget)
            column_index: Column index (0 = checkbox widget, 1 = name with icon, others = text only)
        """
        super().__init__(parent)
        self._column_index = column_index
        self._is_widget_column = (column_index in [0, 4])  # Checkbox y State son widgets
        self._is_name_column = (column_index == 1)
        self._table_widget = parent if isinstance(parent, QTableWidget) else None
    
    def paint(self, painter: QPainter, option, index) -> None:
        """
        Paint item with complete control over rendering.
        
        Does not call super().paint() to prevent Qt's default selection borders.
        Paints background ONCE for the entire row to avoid alpha seams.
        """
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        
        # Desactivar decoraciones de selección por defecto de Qt
        opt.state &= ~QStyle.StateFlag.State_HasFocus
        opt.state &= ~QStyle.StateFlag.State_KeyboardFocusChange
        opt.showDecorationSelected = False
        
        # Detectar estados de selección y hover ANTES de desactivarlos
        is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        is_hover = bool(opt.state & QStyle.StateFlag.State_MouseOver)
        
        # Columnas 0 y 4 tienen widgets (checkbox y state), no dibujar nada
        if self._is_widget_column:
            return
        
        # SOLUCIÓN PROFESIONAL: Pintar fondo UNA sola vez para toda la fila
        # Solo la columna de nombre (columna 1) pinta el fondo completo
        if (is_selected or is_hover) and self._is_name_column:
            self._draw_selection_background(painter, opt, index.row(), is_selected, is_hover)
        
        # Dibujar contenido según el tipo de columna
        if self._is_name_column:
            self._draw_name_column(painter, opt, index, is_selected)
        else:
            self._draw_text_column(painter, opt, index)
    
    def _draw_selection_background(self, painter: QPainter, option, row: int, is_selected: bool, is_hover: bool) -> None:
        """
        Draw selection/hover background for the current column only.
        
        Paints the background ONCE using option.rect to avoid alpha seams.
        Only the name column (column 1) should call this method.
        """
        # Solo dibujar fondo si es la columna de nombre (columna 1)
        # Las otras columnas no deben pintar fondo para evitar múltiples pasadas
        if not self._is_name_column:
            return
        
        # Usar SOLO option.rect - no calcular rectángulo completo de la fila
        # Esto evita problemas con el cálculo y asegura que solo se pinte una vez
        bg_rect = option.rect
        
        # Pintar el fondo UNA sola vez usando el rectángulo de la columna actual
        if is_selected:
            painter.fillRect(bg_rect, QColor(255, 255, 255, 18))
        elif is_hover:
            painter.fillRect(bg_rect, QColor(255, 255, 255, 10))
    
    def _draw_name_column(self, painter: QPainter, option, index, is_selected: bool) -> None:
        """Draw name column with icon and text."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        
        # Dibujar icono si existe
        if icon and isinstance(icon, QIcon) and not icon.isNull():
            icon_size = self.ICON_SIZE_SELECTED if is_selected else self.ICON_SIZE_NORMAL
            pixmap = icon.pixmap(icon_size)
            if not pixmap.isNull():
                icon_x = option.rect.left() + self.MARGIN_LEFT + 10
                icon_y = option.rect.top() + (option.rect.height() - icon_size.height()) // 2
                icon_rect = QRect(icon_x, icon_y, icon_size.width(), icon_size.height())
                painter.drawPixmap(icon_rect, pixmap)
        
        # Dibujar texto
        if text:
            icon_width = self.ICON_SIZE_SELECTED.width() if is_selected else self.ICON_SIZE_NORMAL.width()
            text_x = option.rect.left() + self.MARGIN_LEFT + icon_width + 32
            text_rect = QRect(
                text_x,
                option.rect.top(),
                option.rect.width() - text_x,
                option.rect.height()
            )
            painter.setPen(QColor(232, 232, 232))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(text))
    
    def _draw_text_column(self, painter: QPainter, option, index) -> None:
        """Draw text-only column."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text:
            painter.setPen(QColor(232, 232, 232))
            
            # Alineación según la columna
            alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            if self._column_index in [2, 3]:  # Extensión y Fecha: centrado
                alignment = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            
            painter.drawText(option.rect, alignment, str(text))
