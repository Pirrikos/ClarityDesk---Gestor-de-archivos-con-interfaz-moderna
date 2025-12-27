"""
StateSectionWidget - Widget para mostrar sección ESTADOS en sidebar.

Muestra lista de estados con color a la izquierda, permite drag & drop para reordenar,
y conecta clicks para activar vista por estado.
"""

from typing import Callable, Optional
from pathlib import Path

from PySide6.QtCore import QMimeData, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QDrag, QFont, QFontMetrics, QIcon, QPainter, QPen, QTransform
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget

from app.core.constants import CHEVRON_COLOR
from app.ui.widgets.state_badge_widget import STATE_COLORS, STATE_LABELS, STATE_CORRECTED, STATE_DELIVERED, STATE_PENDING, STATE_REVIEW
from app.ui.widgets.folder_tree_styles import FONT_FAMILY, ITEM_HEIGHT as STYLES_ITEM_HEIGHT, ITEM_RIGHT_MARGIN, TEXT_PRIMARY
from app.ui.widgets.folder_tree_icon_utils import load_folder_icon_svg, get_assets_icons_path, FOLDER_ICON_SIZE


class StateSectionWidget(QWidget):
    """Widget para mostrar sección ESTADOS en sidebar."""
    
    state_selected = Signal(str)  # Emitido cuando se selecciona un estado
    
    COLOR_CIRCLE_RADIUS = 4  # Radio del círculo de color (diámetro 8px)
    ITEM_HEIGHT = STYLES_ITEM_HEIGHT  # 30px - igual que las carpetas
    TITLE_HEIGHT = STYLES_ITEM_HEIGHT  # Altura del título (igual que un item de carpeta)
    TITLE_ICON_SIZE = QSize(20, 20)  # Tamaño del icono del título (más pequeño que el de carpetas)
    CONTAINER_PADDING_LEFT = 10  # Padding izquierdo del contenedor del árbol (igual que las carpetas)
    ITEM_PADDING_RIGHT = ITEM_RIGHT_MARGIN  # 10px - igual que las carpetas
    ITEM_PADDING_VERTICAL = 4  # Padding vertical superior e inferior - igual que las carpetas (4px arriba y abajo)
    ITEM_SPACING = 0  # Sin espaciado entre items (el padding vertical ya lo maneja)
    # Para alinear con los títulos de las carpetas: contenedor (10px) + icono (32px) + espacio (4px) = 46px
    # Pero el círculo debe estar donde está el icono, así que: contenedor (10px) + mitad del icono (16px) = 26px para centrar el círculo
    # El texto empieza después del círculo con el mismo espaciado que entre icono y texto (4px)
    COLOR_CIRCLE_X = CONTAINER_PADDING_LEFT + 16  # Centro del círculo alineado con el centro del icono (10 + 16 = 26px)
    TEXT_X_OFFSET = CONTAINER_PADDING_LEFT + 32 + 4  # Donde empieza el texto de las carpetas (10 + 32 + 4 = 46px)
    
    # Constantes para chevron y línea separadora (igual que las carpetas)
    CONTROLS_AREA_PAD_X_RIGHT = 10
    CONTROLS_AREA_PADDING = 4
    CONTROLS_AREA_OFFSET = 8
    CONTROLS_AREA_BUTTON_SIZE = 24
    CONTROLS_AREA_SEPARATOR_MARGIN = 12
    CONTROLS_AREA_TOTAL_OFFSET = (
        CONTROLS_AREA_PAD_X_RIGHT + 
        CONTROLS_AREA_PADDING + 
        CONTROLS_AREA_OFFSET + 
        CONTROLS_AREA_BUTTON_SIZE + 
        CONTROLS_AREA_SEPARATOR_MARGIN
    )
    CHEVRON_CLICKABLE_WIDTH = 32
    CHEVRON_CLICKABLE_HEIGHT = 28
    CHEVRON_VERTICAL_SPACING = 14
    CHEVRON_VERTICAL_OFFSET = 0
    CHEVRON_SIZE = 4.0  # Tamaño del chevron
    SEPARATOR_VERTICAL_COLOR = QColor(255, 255, 255, 40)
    # Márgenes más pequeños para igualar la longitud de la línea con las carpetas
    # Las carpetas tienen ROOT_ITEM_TOP_SPACING (12px) que hace la línea más larga
    # Reducimos los márgenes para compensar: carpetas = 42px altura - 8px márgenes = 34px línea
    # Estados = 30px altura - 4px márgenes = 26px línea (más cercano a las carpetas)
    SEPARATOR_VERTICAL_MARGIN_TOP = 2
    SEPARATOR_VERTICAL_MARGIN_BOTTOM = 2
    SEPARATOR_VERTICAL_TEXT_MARGIN = 4
    
    def __init__(
        self,
        state_label_manager,
        tab_manager,
        parent=None
    ):
        """
        Inicializar widget de sección ESTADOS.
        
        Args:
            state_label_manager: StateLabelManager para obtener orden y labels.
            tab_manager: TabManager para activar contexto de estado.
            parent: Widget padre.
        """
        super().__init__(parent)
        self._state_label_manager = state_label_manager
        self._tab_manager = tab_manager
        self._states: list[str] = []
        self._active_state: Optional[str] = None
        self._drag_start_pos: Optional[QPoint] = None
        self._dragged_index: Optional[int] = None
        self._is_expanded: bool = True  # Por defecto expandido
        
        # SOLUCIÓN DEFINITIVA: Widget completamente neutro
        # El widget NO decide su posición, el layout lo hace
        # NO usar setContentsMargins aquí
        
        # Cargar icono estados.svg
        self._title_icon: Optional[QIcon] = None
        self._load_title_icon()
        
        self.setMouseTracking(True)
        
        # Conectar señal de cambio de labels para refrescar
        if state_label_manager:
            state_label_manager.labels_changed.connect(self._refresh_states)
        
        self._refresh_states()
        # Actualizar altura mínima después de refrescar estados
        self._update_minimum_height()
    
    def _load_title_icon(self) -> None:
        """Cargar icono estados.svg para el título."""
        try:
            icons_path = get_assets_icons_path()
            svg_path = icons_path / 'estados.svg'
            if svg_path.exists():
                self._title_icon = load_folder_icon_svg(svg_path, self.TITLE_ICON_SIZE)
            else:
                self._title_icon = QIcon()
        except Exception:
            self._title_icon = QIcon()
    
    def _refresh_states(self) -> None:
        """Refrescar lista de estados desde StateLabelManager."""
        if not self._state_label_manager:
            # Fallback a orden por defecto
            self._states = [STATE_PENDING, STATE_DELIVERED, STATE_CORRECTED, STATE_REVIEW]
        else:
            self._states = self._state_label_manager.get_states_in_order()
        
        # Verificar estado activo
        if self._tab_manager and self._tab_manager.has_state_context():
            self._active_state = self._tab_manager.get_state_context()
        else:
            self._active_state = None
        
        # Actualizar altura mínima después de refrescar estados
        self._update_minimum_height()
        self.update()
    
    def _update_minimum_height(self) -> None:
        """
        Actualizar altura mínima del widget según el número de estados.
        
        SOLUCIÓN DEFINITIVA: Widget completamente neutro.
        El margen superior lo maneja el layout contenedor, no el widget.
        Solo calculamos la altura de los items.
        
        Establece min = max para evitar comportamientos erráticos del layout.
        """
        if not self._states:
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            return
        
        # Altura total = título + (número de items * altura de item si está expandido, 0 si está colapsado)
        # El margen superior lo maneja el layout contenedor
        states_height = (len(self._states) * self.ITEM_HEIGHT) if self._is_expanded else 0
        height = self.TITLE_HEIGHT + states_height
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)  # Altura fija (min = max) para evitar problemas de layout
        # Forzar actualización del layout para que respete el nuevo tamaño
        self.updateGeometry()
    
    def set_active_state(self, state: Optional[str]) -> None:
        """
        Establecer estado activo para resaltar visualmente.
        
        REGLA OBLIGATORIA: Siempre actualizar la vista cuando se establece el estado,
        incluso si es el mismo, para garantizar que la selección visual se actualice
        correctamente al cambiar entre estados y carpetas.
        """
        # REGLA OBLIGATORIA: Siempre actualizar, incluso si el estado es el mismo,
        # porque el contexto puede haber cambiado (de carpeta a estado o viceversa)
        self._active_state = state
        self.update()
    
    def sizeHint(self) -> QSize:
        """Retornar tamaño preferido del widget."""
        if not self._states:
            return QSize(0, self.TITLE_HEIGHT)
        # SOLUCIÓN DEFINITIVA: Título + altura de items (si está expandido), sin margen superior
        # El margen superior lo maneja el layout contenedor
        states_height = (len(self._states) * self.ITEM_HEIGHT) if self._is_expanded else 0
        height = self.TITLE_HEIGHT + states_height
        return QSize(0, height)
    
    def minimumSizeHint(self) -> QSize:
        """Retornar tamaño mínimo."""
        return self.sizeHint()
    
    def paintEvent(self, event) -> None:
        """Pintar título y lista de estados con color a la izquierda."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        # SOLUCIÓN DEFINITIVA: Empezar en y=0 porque el margen ya lo aplica Qt
        # No duplicar el margen aquí, Qt ya lo maneja automáticamente
        y = 0
        
        # Fuente igual que las carpetas del sidebar
        font = QFont()
        # Usar la primera fuente disponible de la familia del sidebar
        font_family_list = FONT_FAMILY.replace('"', '').split(',')
        font.setFamily(font_family_list[0].strip() if font_family_list else "Segoe UI")
        font.setPixelSize(13)  # Tamaño 13px igual que las carpetas
        font.setWeight(QFont.Weight.Medium)  # Peso Medium para el título (igual que carpetas raíz)
        painter.setFont(font)
        
        font_metrics = QFontMetrics(font)
        
        # Dibujar título "ESTADOS" con icono (igual que las carpetas raíz)
        title_rect = QRect(0, y, rect.width(), self.TITLE_HEIGHT)
        
        # Dibujar icono
        if self._title_icon and not self._title_icon.isNull():
            icon_size = self.TITLE_ICON_SIZE
            icon_x = self.CONTAINER_PADDING_LEFT
            icon_y = y + (self.TITLE_HEIGHT - icon_size.height()) // 2
            icon_rect = QRect(icon_x, icon_y, icon_size.width(), icon_size.height())
            self._title_icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)
        
        # Calcular posición de la línea separadora y chevron
        viewport_width = rect.width()
        separator_x = self._calculate_separator_line_x(viewport_width)
        
        # Dibujar texto "ESTADOS" (recortar si hay línea separadora)
        text_color = QColor(TEXT_PRIMARY)
        painter.setPen(QPen(text_color))
        text_x = self.CONTAINER_PADDING_LEFT + self.TITLE_ICON_SIZE.width() + 4  # Icono + espacio
        text_clip_right = separator_x - self.SEPARATOR_VERTICAL_TEXT_MARGIN if separator_x > 0 else rect.width()
        text_y = y + (self.TITLE_HEIGHT + font_metrics.ascent()) // 2
        
        # Calcular rectángulo completo del texto (igual que Qt hace con SE_ItemViewItemText)
        # En Qt, SE_ItemViewItemText devuelve el rectángulo donde se dibuja el texto.
        # Para alinear correctamente el chevron, usamos donde termina el texto real más un pequeño margen.
        # Esto es más preciso que usar el ancho completo del widget.
        text_width = font_metrics.horizontalAdvance("ESTADOS")
        # El text_rect.right() debe ser donde termina el texto, que es text_x + text_width
        text_rect_right = text_x + text_width
        text_rect = QRect(text_x, y, text_width, self.TITLE_HEIGHT)
        
        # Guardar rectángulo original para el clipping del texto
        text_rect_clip = QRect(text_x, text_y - font_metrics.ascent(), text_clip_right - text_x, font_metrics.height())
        painter.setClipRect(text_rect_clip)
        painter.drawText(text_x, text_y, "ESTADOS")
        painter.setClipping(False)
        
        # Dibujar línea separadora vertical (igual que las carpetas)
        if separator_x > 0:
            # Desactivar antialiasing para líneas finas (igual que las carpetas)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            painter.setPen(QPen(self.SEPARATOR_VERTICAL_COLOR, 1))
            painter.drawLine(
                int(separator_x),
                int(title_rect.top() + self.SEPARATOR_VERTICAL_MARGIN_TOP),
                int(separator_x),
                int(title_rect.bottom() - self.SEPARATOR_VERTICAL_MARGIN_BOTTOM)
            )
            # Reactivar antialiasing para el resto del dibujado
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Dibujar chevron (igual que las carpetas)
        # Siempre mostrar chevron si hay estados (para expandir/colapsar)
        if self._states:
            chevron_center_x, chevron_center_y = self._calculate_chevron_center(title_rect, viewport_width, text_rect)
            # Validar que el chevron esté dentro del área visible del widget (permitir que esté ligeramente fuera del title_rect)
            if (0 <= chevron_center_x <= rect.width() and 
                title_rect.top() <= chevron_center_y <= title_rect.bottom()):
                rotation = 90.0 if self._is_expanded else 0.0  # 0° = derecha, 90° = abajo
                self._paint_chevron_right(painter, title_rect, chevron_center_x, chevron_center_y, rotation)
        
        # Cambiar fuente a Normal para los estados
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        font_metrics = QFontMetrics(font)
        
        y += self.TITLE_HEIGHT
        
        # Solo dibujar estados si está expandido
        if not self._is_expanded:
            painter.end()
            return
        
        for i, state in enumerate(self._states):
            item_rect = QRect(0, y, rect.width(), self.ITEM_HEIGHT)
            
            # Verificar si está activo
            is_active = (state == self._active_state)
            
            # Fondo activo (igual que las carpetas)
            if is_active:
                bg_color = QColor(35, 38, 45)  # SELECT_BG de folder_tree_styles
                painter.fillRect(item_rect, bg_color)
            
            # Círculo de color a la izquierda (donde está el icono de las carpetas)
            color = STATE_COLORS.get(state, QColor(200, 200, 200))
            # Padding normal para todos los items (el padding superior extra ya está en y para el primer estado)
            top_padding = self.ITEM_PADDING_VERTICAL
            bottom_padding = self.ITEM_PADDING_VERTICAL
            # Altura disponible para contenido = altura total - padding superior - padding inferior
            content_height = self.ITEM_HEIGHT - top_padding - bottom_padding
            circle_center_y = y + top_padding + content_height // 2
            
            # Dibujar círculo
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                self.COLOR_CIRCLE_X - self.COLOR_CIRCLE_RADIUS,
                circle_center_y - self.COLOR_CIRCLE_RADIUS,
                self.COLOR_CIRCLE_RADIUS * 2,
                self.COLOR_CIRCLE_RADIUS * 2
            )
            
            # Texto del label en minúsculas
            label = self._state_label_manager.get_label(state) if self._state_label_manager else STATE_LABELS.get(state, state.lower())
            # Asegurar que esté en minúsculas
            label = label.lower() if label else state.lower()
            
            # Color del texto (igual que las carpetas)
            text_color = QColor(230, 230, 230)  # TEXT_PRIMARY
            painter.setPen(QPen(text_color))
            
            # Posición del texto (alineado con los títulos de las carpetas)
            text_x = self.TEXT_X_OFFSET
            # Centrar verticalmente con padding normal (igual que el círculo)
            text_y = y + top_padding + (content_height + font_metrics.ascent()) // 2
            
            painter.drawText(text_x, text_y, label)
            
            y += self.ITEM_HEIGHT
        
        painter.end()
    
    def _calculate_separator_line_x(self, viewport_width: int) -> int:
        """Calcular posición X de la línea separadora (igual que las carpetas)."""
        return viewport_width - self.CONTROLS_AREA_TOTAL_OFFSET
    
    def _calculate_chevron_center(self, title_rect: QRect, viewport_width: int, text_rect: QRect) -> tuple[int, int]:
        """
        Calcular posición del centro del chevron (igual que las carpetas cuando no hay menú).
        
        En las carpetas sin menú: center_x = text_rect.right() - CONTROLS_AREA_OFFSET
        """
        # Calcular posición de la línea separadora primero
        separator_x = self._calculate_separator_line_x(viewport_width)
        
        # Ajuste: En Qt, text_rect.right() incluye más espacio que nuestro cálculo manual.
        # Para alinear correctamente con las carpetas, necesitamos usar un offset mayor.
        # El chevron debe estar cerca de donde termina el texto pero con espacio suficiente.
        if separator_x > 0:
            # Si hay separador, el chevron va justo después del separador con un pequeño margen
            center_x = separator_x + self.CONTROLS_AREA_SEPARATOR_MARGIN + 12  # +2px más a la derecha
        else:
            # Si no hay separador, usar text_rect.right() con un offset ajustado
            center_x = text_rect.right() + 20  # +2px más a la derecha
        
        # Asegurar que el chevron esté dentro del área visible
        pad_x_right = self.CONTROLS_AREA_PAD_X_RIGHT
        max_x = viewport_width - pad_x_right - self.CHEVRON_CLICKABLE_WIDTH // 2
        center_x = min(center_x, max_x)
        
        center_y = title_rect.top() + (title_rect.height() // 2) + self.CHEVRON_VERTICAL_OFFSET
        return center_x, center_y
    
    def _paint_chevron_right(self, painter: QPainter, title_rect: QRect, center_x: int, center_y: int, rotation: float) -> None:
        """Pintar chevron minimalista estilo macOS que rota según el estado expandido/colapsado (igual que las carpetas)."""
        painter.save()
        try:
            chevron_color = QColor(CHEVRON_COLOR)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            
            # Aplicar rotación desde el centro
            chevron_transform = QTransform()
            chevron_transform.translate(center_x, center_y)
            chevron_transform.rotate(rotation)
            chevron_transform.translate(-center_x, -center_y)
            painter.setTransform(chevron_transform, combine=True)
            
            size = self.CHEVRON_SIZE
            chevron_pen = QPen(chevron_color, 1.8)
            chevron_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            chevron_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(chevron_pen)
            
            painter.drawLine(
                int(center_x - size * 0.5), int(center_y - size),
                int(center_x + size * 0.5), int(center_y)
            )
            painter.drawLine(
                int(center_x + size * 0.5), int(center_y),
                int(center_x - size * 0.5), int(center_y + size)
            )
        finally:
            painter.restore()
    
    def _get_chevron_clickable_rect(self, title_rect: QRect, text_rect: QRect) -> QRect:
        """Obtener rectángulo clickeable del chevron."""
        viewport_width = self.width()
        center_x, center_y = self._calculate_chevron_center(title_rect, viewport_width, text_rect)
        
        chevron_x = center_x - self.CHEVRON_CLICKABLE_WIDTH // 2
        chevron_y = center_y - self.CHEVRON_CLICKABLE_HEIGHT // 2
        
        # Asegurar que esté dentro del rectángulo del título
        chevron_x = max(title_rect.left(), min(chevron_x, title_rect.right() - self.CHEVRON_CLICKABLE_WIDTH))
        chevron_y = max(title_rect.top(), min(chevron_y, title_rect.bottom() - self.CHEVRON_CLICKABLE_HEIGHT))
        
        return QRect(chevron_x, chevron_y, self.CHEVRON_CLICKABLE_WIDTH, self.CHEVRON_CLICKABLE_HEIGHT)
    
    def mousePressEvent(self, event) -> None:
        """Manejar click en un estado o en el chevron para plegar/desplegar."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            title_rect = QRect(0, 0, self.width(), self.TITLE_HEIGHT)
            
            # Calcular text_rect para el chevron (igual que en paintEvent)
            font = QFont()
            font_family_list = FONT_FAMILY.replace('"', '').split(',')
            font.setFamily(font_family_list[0].strip() if font_family_list else "Segoe UI")
            font.setPixelSize(13)
            font_metrics = QFontMetrics(font)
            text_x = self.CONTAINER_PADDING_LEFT + self.TITLE_ICON_SIZE.width() + 4
            text_width = font_metrics.horizontalAdvance("ESTADOS")
            text_rect = QRect(text_x, 0, text_width, self.TITLE_HEIGHT)
            
            # Verificar si el click es en el chevron
            chevron_rect = self._get_chevron_clickable_rect(title_rect, text_rect)
            if chevron_rect.contains(pos):
                # Toggle expand/collapse
                self._is_expanded = not self._is_expanded
                self._update_minimum_height()
                self.update()
                return
            
            # Verificar si el click es en el título (fuera del chevron)
            if title_rect.contains(pos):
                # Click en el título pero no en el chevron - no hacer nada
                return
            
            # Click en un estado
            clicked_index = self._get_index_at_position(pos)
            if clicked_index is not None and clicked_index < len(self._states):
                state = self._states[clicked_index]
                # Emitir señal antes de navegar para que MainWindow pueda cancelar búsqueda
                self.state_selected.emit(state)
                # NAVEGACIÓN: set_state_context dispara navegación en TabManager
                self._tab_manager.set_state_context(state)
                self._active_state = state
                self.update()
            
            # Iniciar drag para reordenar
            self._drag_start_pos = event.pos()
            self._dragged_index = clicked_index
    
    def mouseMoveEvent(self, event) -> None:
        """Manejar movimiento del mouse para iniciar drag."""
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_start_pos is not None:
            if (event.pos() - self._drag_start_pos).manhattanLength() > 10:  # Threshold para iniciar drag
                self._start_drag(self._dragged_index)
            else:
                self.update()  # Refrescar para mostrar hover
    
    def mouseReleaseEvent(self, event) -> None:
        """Limpiar estado de drag."""
        self._drag_start_pos = None
        self._dragged_index = None
        self.update()
    
    def _get_index_at_position(self, pos: QPoint) -> Optional[int]:
        """Obtener índice del estado en la posición especificada."""
        y = pos.y()
        # Restar altura del título
        y_relative = y - self.TITLE_HEIGHT
        if y_relative < 0:
            return None  # Click en el título, no en un estado
        index = y_relative // self.ITEM_HEIGHT
        if 0 <= index < len(self._states):
            return index
        return None
    
    def _start_drag(self, index: Optional[int]) -> None:
        """Iniciar drag para reordenar estados."""
        if index is None or index < 0 or index >= len(self._states):
            return
        
        # Crear mime data con el índice
        mime_data = QMimeData()
        mime_data.setText(f"state_reorder:{index}")
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)
    
    def dragEnterEvent(self, event) -> None:
        """Aceptar drag interno para reordenar."""
        if event.mimeData().hasText() and event.mimeData().text().startswith("state_reorder:"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event) -> None:
        """Manejar movimiento durante drag."""
        if event.mimeData().hasText() and event.mimeData().text().startswith("state_reorder:"):
            event.acceptProposedAction()
            # Mostrar indicador visual de posición de drop
            self.update()
        else:
            event.ignore()
    
    def dropEvent(self, event) -> None:
        """Manejar drop para reordenar estados."""
        if not event.mimeData().hasText():
            event.ignore()
            return
        
        text = event.mimeData().text()
        if not text.startswith("state_reorder:"):
            event.ignore()
            return
        
        try:
            source_index = int(text.split(":")[1])
        except (ValueError, IndexError):
            event.ignore()
            return
        
        # Obtener índice de destino
        target_index = self._get_index_at_position(event.pos())
        if target_index is None or source_index == target_index:
            event.ignore()
            return
        
        # Reordenar estados
        new_order = self._states.copy()
        state = new_order.pop(source_index)
        new_order.insert(target_index, state)
        
        # Guardar nuevo orden
        if self._state_label_manager:
            self._state_label_manager.reorder_states(new_order)
        
        # Refrescar
        self._refresh_states()
        
        event.acceptProposedAction()

