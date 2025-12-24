"""
ListIconDelegate - Professional delegate for list view rendering.

Controls all drawing to prevent Qt's default selection borders.
"""

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPalette, QPen
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem, QStyledItemDelegate, QTableWidget


class ListViewDelegate(QStyledItemDelegate):
    """
    Unified delegate for all list view columns.
    
    Completely controls item rendering to prevent default Qt selection borders.
    """
    
    MARGIN_LEFT = 5
    ICON_SIZE_SELECTED = QSize(30, 30)
    ICON_SIZE_NORMAL = QSize(28, 28)
    ICON_OFFSET_X = 5  # Offset horizontal del icono desde el margen izquierdo
    TEXT_OFFSET_X = 32  # Espacio entre icono y texto en columna de nombre
    CONTAINER_MARGIN = 2  # Margen del contenedor alrededor del icono
    CONTAINER_RADIUS = 8  # Radio de esquinas redondeadas del contenedor
    TEXT_COLOR = QColor(232, 232, 232)  # Color del texto en columnas
    BASE_BG_COLOR = QColor(17, 19, 24)  # Color base de fondo de celda
    HOVER_BG_COLOR = QColor(255, 255, 255, 20)  # Fondo hover tipo Finder (rgba(255,255,255,0.08) ≈ 20/255)
    CONTAINER_BG_COLOR = QColor(190, 190, 190)  # #BEBEBE - fondo contenedor
    CONTAINER_BORDER_COLOR = QColor(160, 160, 160)  # Borde contenedor normal
    SELECTION_BORDER_COLOR = QColor(100, 150, 255)  # Borde azul suave cuando está seleccionado
    SELECTION_BG_COLOR = QColor(100, 150, 255, 15)  # Fondo azul suave cuando está seleccionado
    
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
    
    def _get_hovered_row(self) -> int:
        """Obtener la fila bajo el mouse si existe."""
        if not self._table_widget:
            return -1
        try:
            hovered_row = getattr(self._table_widget, '_hovered_row', -1)
            return hovered_row if hovered_row >= 0 else -1
        except (AttributeError, RuntimeError):
            # Widget aún no está completamente inicializado o fue eliminado
            return -1
    
    def paint(self, painter: QPainter, option, index) -> None:
        """
        Paint item with complete control over rendering.
        
        Does not call super().paint() to prevent Qt's default selection borders.
        Paints a uniform background per cell to avoid vertical seams on Windows.
        """
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        
        # Desactivar decoraciones de selección por defecto de Qt
        opt.state &= ~QStyle.StateFlag.State_HasFocus
        opt.state &= ~QStyle.StateFlag.State_KeyboardFocusChange
        opt.showDecorationSelected = False
        
        # Detectar estado de selección ANTES de desactivarlo
        is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        
        # Detectar si la fila está en hover
        current_row = index.row()
        is_hovered = (current_row == self._get_hovered_row())
        
        # Fondo uniforme por celda: evita "costuras" verticales del estilo nativo
        # en estado normal en Windows. No usamos transparencia aquí.
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        base_color = self.BASE_BG_COLOR
        if self._table_widget:
            try:
                base_color = self._table_widget.palette().color(QPalette.ColorRole.Base)
            except Exception:
                pass
        
        # SOLO la columna 1 (Nombre) pinta el fondo de hover para las columnas de contenido
        # La columna 0 (checkbox) se excluye explícitamente del hover
        if self._is_widget_column:
            # Columna del checkbox: NO pintar hover, solo fondo base
            painter.fillRect(opt.rect, base_color)
        elif self._is_name_column and is_hovered and not is_selected:
            # Columna 1 con hover: pintar hover desde columna 1 hasta última visible
            full_row_rect = self._calculate_full_row_rect(current_row)
            if full_row_rect.isValid():
                # Combinar el clip actual con el rectángulo completo de las columnas de contenido
                painter.save()
                current_clip = painter.clipBoundingRect()
                if current_clip.isValid():
                    # Unir el clip actual con el rectángulo completo
                    combined_clip = current_clip.united(full_row_rect)
                    painter.setClipRect(combined_clip, Qt.ClipOperation.ReplaceClip)
                else:
                    # Si no hay clip actual, usar solo el rectángulo completo
                    painter.setClipRect(full_row_rect, Qt.ClipOperation.ReplaceClip)
                painter.fillRect(full_row_rect, self.HOVER_BG_COLOR)
                painter.restore()
            else:
                # Fallback: pintar solo la celda si no se puede calcular el rectángulo completo
                painter.fillRect(opt.rect, self.HOVER_BG_COLOR)
        elif not self._is_name_column:
            # Otras columnas de contenido: NO pintar fondo si hay hover (dejar que la columna 1 lo haga)
            if not is_hovered or is_selected:
                painter.fillRect(opt.rect, base_color)
            # Si hay hover, no pintar nada (transparente) para que se vea el hover de la columna 1
        else:
            # Columna 1 sin hover: fondo base
            painter.fillRect(opt.rect, base_color)

        # Columnas 0 y 4 tienen widgets (checkbox y state): tras pintar fondo, no dibujar contenido
        if self._is_widget_column:
            return

        # Dibujar contenido según el tipo de columna
        if self._is_name_column:
            self._draw_icon_container(painter, opt, is_selected)
            self._draw_name_column(painter, opt, index, is_selected)
        else:
            self._draw_text_column(painter, opt, index)
    
    def _calculate_icon_position(self, option, is_selected: bool) -> QRect:
        """Calculate icon position and size rectangle."""
        icon_size = self.ICON_SIZE_SELECTED if is_selected else self.ICON_SIZE_NORMAL
        icon_x = option.rect.left() + self.MARGIN_LEFT + self.ICON_OFFSET_X
        icon_y = option.rect.top() + (option.rect.height() - icon_size.height()) // 2
        return QRect(icon_x, icon_y, icon_size.width(), icon_size.height())
    
    def _draw_icon_container(self, painter: QPainter, option, is_selected: bool) -> None:
        """
        Draw container background over the icon area.
        
        Paints the background container similar to grid view, but only over the icon.
        Only called from the name column (column 1) to avoid multiple passes.
        """
        icon_rect = self._calculate_icon_position(option, is_selected)
        
        # Crear rectángulo del contenedor sobre el icono con margen
        container_rect = QRect(
            icon_rect.left() - self.CONTAINER_MARGIN,
            icon_rect.top() - self.CONTAINER_MARGIN,
            icon_rect.width() + (self.CONTAINER_MARGIN * 2),
            icon_rect.height() + (self.CONTAINER_MARGIN * 2)
        )
        
        # Pintar el contenedor siempre visible, igual que en grid
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Fondo gris claro siempre visible, igual que grid
        bg_color = self.CONTAINER_BG_COLOR
        border_color = self.CONTAINER_BORDER_COLOR
        border_width = 1
        
        if is_selected:
            # Cuando está seleccionado, cambiar borde a azul y añadir fondo azul semitransparente
            border_color = self.SELECTION_BORDER_COLOR
            border_width = 2
            bg_color = self.SELECTION_BG_COLOR
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, border_width))
        painter.drawRoundedRect(container_rect, self.CONTAINER_RADIUS, self.CONTAINER_RADIUS)
        
        # Restaurar render hint para el resto del dibujado
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    
    def _draw_name_column(self, painter: QPainter, option, index, is_selected: bool) -> None:
        """Draw name column with icon and text."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        
        # Calcular tamaño del icono una sola vez
        icon_size = self.ICON_SIZE_SELECTED if is_selected else self.ICON_SIZE_NORMAL
        
        # Dibujar icono si existe
        if icon and isinstance(icon, QIcon) and not icon.isNull():
            pixmap = icon.pixmap(icon_size)
            if not pixmap.isNull():
                icon_rect = self._calculate_icon_position(option, is_selected)
                painter.drawPixmap(icon_rect, pixmap)
        
        # Dibujar texto
        if text:
            text_x = option.rect.left() + self.MARGIN_LEFT + icon_size.width() + self.TEXT_OFFSET_X
            # Usar todo el ancho disponible hasta el borde derecho de la columna
            # Reducir solo 4px de margen derecho para que el texto llegue casi hasta el borde
            padding_right = 4
            text_width = option.rect.right() - text_x - padding_right
            text_rect = QRect(
                text_x,
                option.rect.top(),
                text_width,
                option.rect.height()
            )
            painter.setPen(self.TEXT_COLOR)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(text))
    
    def _draw_text_column(self, painter: QPainter, option, index) -> None:
        """Draw text-only column."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text:
            painter.setPen(self.TEXT_COLOR)
            
            # Alineación según la columna
            alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            if self._column_index in [2, 3]:  # Extensión y Fecha: centrado
                alignment = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            
            painter.drawText(option.rect, alignment, str(text))
    
    def _calculate_full_row_rect(self, row: int) -> QRect:
        """
        Calcular rectángulo completo de las columnas de contenido (desde columna 1 hasta última visible).
        
        Excluye explícitamente la columna 0 (checkbox) del hover.
        Usa visualRect(QModelIndex) del modelo, que es la API correcta y estable para delegates.
        """
        if not self._table_widget:
            return QRect()
        
        model = self._table_widget.model()
        if not model:
            return QRect()
        
        # Empezar desde la columna 1 (excluir columna 0 del checkbox)
        first_content_col = 1
        
        # Obtener índice de la primera columna de contenido (columna 1)
        first_index = model.index(row, first_content_col)
        if not first_index.isValid():
            return QRect()
        
        # Obtener rectángulo visual de la primera columna de contenido
        first_col_rect = self._table_widget.visualRect(first_index)
        if not first_col_rect.isValid():
            return QRect()
        
        # Encontrar la última columna visible (excluyendo columna 0 si está visible)
        last_visible_col = -1
        for col in range(self._table_widget.columnCount() - 1, first_content_col - 1, -1):
            if not self._table_widget.isColumnHidden(col):
                last_visible_col = col
                break
        
        if last_visible_col < first_content_col:
            # Si no hay columnas de contenido visibles, usar solo la primera
            return first_col_rect
        
        # Obtener índice de la última columna visible
        last_index = model.index(row, last_visible_col)
        if not last_index.isValid():
            return first_col_rect
        
        # Obtener rectángulo visual de la última columna visible
        last_col_rect = self._table_widget.visualRect(last_index)
        if not last_col_rect.isValid():
            return first_col_rect
        
        # Combinar ambos rectángulos para obtener el rectángulo completo de las columnas de contenido
        # Usar +1 en el ancho para evitar off-by-one (right() es inclusivo)
        full_rect = QRect(
            first_col_rect.left(),
            first_col_rect.top(),
            last_col_rect.right() - first_col_rect.left() + 1,
            first_col_rect.height()
        )
        
        return full_rect
