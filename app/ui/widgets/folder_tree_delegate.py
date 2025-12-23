from PySide6.QtCore import QEvent, QModelIndex, QPoint, QRect, QSize, Qt, QEasingCurve, QTimer, QVariantAnimation
from PySide6.QtGui import QBrush, QColor, QIcon, QMouseEvent, QPainter, QPen, QPolygon, QTransform
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QTreeView, QStyle

from app.ui.widgets.folder_tree_menu_utils import calculate_menu_rect_viewport
from app.ui.widgets.folder_tree_widget_utils import find_sidebar


class FolderTreeSectionDelegate(QStyledItemDelegate):
    """Delegate de pintura para agrupar visualmente la sección activa como bloque tipo tarjeta."""

    # Constantes para área de controles (tres puntitos + chevron)
    CONTROLS_AREA_PAD_X_RIGHT = 10  # Separador vertical del sidebar
    CONTROLS_AREA_PADDING = 4  # Padding interno
    CONTROLS_AREA_OFFSET = 8  # Offset desde el texto
    CONTROLS_AREA_BUTTON_SIZE = 24  # Tamaño del área de tres puntitos
    CONTROLS_AREA_SEPARATOR_MARGIN = 12  # Margen antes del área de controles
    
    # Cálculo: separador_x = viewport_width - PAD_X_RIGHT - PADDING - OFFSET - BUTTON_SIZE - SEPARATOR_MARGIN
    CONTROLS_AREA_TOTAL_OFFSET = (
        CONTROLS_AREA_PAD_X_RIGHT + 
        CONTROLS_AREA_PADDING + 
        CONTROLS_AREA_OFFSET + 
        CONTROLS_AREA_BUTTON_SIZE + 
        CONTROLS_AREA_SEPARATOR_MARGIN
    )  # = 58
    
    # Constantes para tres puntitos (menú)
    MENU_BUTTON_SIZE = 24  # Área de clic del botón de menú
    MENU_BUTTON_PADDING = 4  # Padding interno del botón
    MENU_BUTTON_VERTICAL_OFFSET = 6  # Offset vertical desde el centro (hacia arriba)
    MENU_BUTTON_MIN_TOP_MARGIN = 2  # Margen mínimo desde arriba
    
    # Constantes para chevron
    CHEVRON_SIZE = 14  # Tamaño del chevron tipo Mac (aumentado para más elegancia)
    CHEVRON_CLICKABLE_WIDTH = 32  # Ancho del área clickeable (izquierda y derecha)
    CHEVRON_CLICKABLE_HEIGHT = 28  # Alto del área clickeable (especialmente hacia abajo)
    CHEVRON_VERTICAL_SPACING = 18  # Espacio vertical debajo de los tres puntitos (aumentado para bajar posición)
    CHEVRON_VERTICAL_OFFSET = 4  # Offset vertical adicional
    
    # Constantes para línea separadora vertical
    SEPARATOR_VERTICAL_COLOR = QColor(255, 255, 255, 40)  # Blanco tenue
    SEPARATOR_VERTICAL_MARGIN_TOP = 4
    SEPARATOR_VERTICAL_MARGIN_BOTTOM = 4
    SEPARATOR_VERTICAL_TEXT_MARGIN = 4  # Margen entre texto y línea para evitar solapamiento
    
    # Constantes para línea separadora horizontal (ya existente)
    SEPARATOR_HORIZONTAL_COLOR = QColor(255, 255, 255, 23)  # rgba(255, 255, 255, 0.09)

    def __init__(self, tree_view: QTreeView):
        super().__init__(tree_view)
        self._view = tree_view
        self._hover_bg = QColor("#23262D")
        self._selected_bg = QColor("#23262D")
        
        self._animations: dict[object, dict] = {}
        self._setup_animation_tracking()
    
    def _setup_animation_tracking(self) -> None:
        if not self._view:
            return
        
        self._view.expanded.connect(self._on_expanded)
        self._view.collapsed.connect(self._on_collapsed)
    
    def _create_animation_updater(self, index, key: str, anim_data: dict):
        def update_value(value):
            anim_data[key] = float(value)
            if self._view:
                visual_rect = self._view.visualRect(index)
                if visual_rect.isValid():
                    self._view.viewport().update(visual_rect)
        return update_value
    
    def _cancel_existing_animations(self, index) -> None:
        if index in self._animations:
            anim_data = self._animations[index]
            for anim in anim_data.get('animations', []):
                try:
                    if anim:  # Verificar que el objeto aún existe
                        anim.stop()
                        anim.deleteLater()
                except RuntimeError:
                    # El objeto C++ ya fue eliminado, ignorar
                    pass
            # Limpiar entrada del diccionario
            del self._animations[index]
    
    def clear_all_animations(self) -> None:
        for index in list(self._animations.keys()):
            self._cancel_existing_animations(index)
        self._animations.clear()
    
    def _create_animation(
        self,
        index,
        anim_data: dict,
        duration: int,
        easing: QEasingCurve.Type,
        start_value: float,
        end_value: float,
        key: str,
        on_finished=None
    ) -> QVariantAnimation:
        anim = QVariantAnimation(self._view)
        anim.setDuration(duration)
        anim.setEasingCurve(easing)
        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        anim.valueChanged.connect(self._create_animation_updater(index, key, anim_data))
        if on_finished:
            anim.finished.connect(on_finished)
        anim_data['animations'].append(anim)
        return anim
    
    def _animate_chevron_expand(self, index) -> None:
        # 140ms, OutCubic
        if not index.isValid():
            return
        
        self._cancel_existing_animations(index)
        
        anim_data = {
            'chevron_rotation': 90.0,
            'chevron_opacity': 0.7,
            'bg_highlight_opacity': 0.0,
            'animations': []
        }
        self._animations[index] = anim_data
        
        rotation_anim = self._create_animation(
            index, anim_data, 140, QEasingCurve.Type.OutCubic,
            90.0, 0.0, 'chevron_rotation'
        )
        
        fade_anim = self._create_animation(
            index, anim_data, 140, QEasingCurve.Type.OutCubic,
            0.7, 1.0, 'chevron_opacity'
        )
        
        highlight_anim = self._create_animation(
            index, anim_data, 120, QEasingCurve.Type.OutCubic,
            0.0, 0.04, 'bg_highlight_opacity',
            lambda: self._start_highlight_fadeout(index, anim_data)
        )
        
        rotation_anim.start()
        fade_anim.start()
        highlight_anim.start()
    
    def _animate_chevron_collapse(self, index) -> None:
        # 140ms, OutCubic
        if not index.isValid():
            return
        
        self._cancel_existing_animations(index)
        
        anim_data = {
            'chevron_rotation': 0.0,
            'chevron_opacity': 1.0,
            'bg_highlight_opacity': 0.0,
            'animations': []
        }
        self._animations[index] = anim_data
        
        rotation_anim = self._create_animation(
            index, anim_data, 140, QEasingCurve.Type.OutCubic,
            0.0, 90.0, 'chevron_rotation',
            lambda: self._cleanup_animation(index, is_chevron=True)
        )
        
        rotation_anim.start()
    
    def _start_highlight_fadeout(self, index, anim_data: dict) -> None:
        fadeout_anim = self._create_animation(
            index, anim_data, 120, QEasingCurve.Type.InCubic,
            anim_data.get('bg_highlight_opacity', 0.04), 0.0, 'bg_highlight_opacity',
            lambda: self._cleanup_animation(index, is_chevron=True)
        )
        fadeout_anim.start()
    
    def _cleanup_animation(self, index, is_chevron: bool = False) -> None:
        if index in self._animations:
            anim_data = self._animations[index]
            if is_chevron and 'chevron_rotation' not in anim_data:
                return
            for anim in anim_data.get('animations', []):
                anim.deleteLater()
            QTimer.singleShot(200, lambda idx=index: self._animations.pop(idx, None))
    
    def _iterate_children(self, index, callback) -> None:
        model = self._view.model()
        if not model:
            return
        child_count = model.rowCount(index)
        for i in range(child_count):
            child_index = model.index(i, 0, index)
            if child_index.isValid():
                callback(child_index)
    
    def _on_expanded(self, index) -> None:
        if not index.isValid():
            return
        self._animate_chevron_expand(index)
        self._iterate_children(index, self._animate_child_expand)
    
    def _on_collapsed(self, index) -> None:
        if not index.isValid():
            return
        self._animate_chevron_collapse(index)
        self._iterate_children(index, self._animate_child_collapse)
    
    def _animate_child_expand(self, index) -> None:
        # 180ms
        self._cancel_existing_animations(index)
        
        anim_data = {
            'opacity': 0.0,
            'icon_rotation': -12.0,
            'animations': []
        }
        self._animations[index] = anim_data
        
        opacity_anim = self._create_animation(
            index, anim_data, 180, QEasingCurve.Type.OutCubic,
            0.0, 1.0, 'opacity',
            lambda: self._cleanup_animation(index, is_chevron=False)
        )
        
        icon_anim = self._create_animation(
            index, anim_data, 180, QEasingCurve.Type.OutCubic,
            -12.0, 0.0, 'icon_rotation'
        )
        
        opacity_anim.start()
        icon_anim.start()
    
    def _animate_child_collapse(self, index) -> None:
        if index not in self._animations:
            self._animations[index] = {'opacity': 1.0, 'icon_rotation': 0.0, 'animations': []}
        
        anim_data = self._animations[index]
        
        for anim in anim_data.get('animations', []):
            anim.stop()
            anim.deleteLater()
        anim_data['animations'] = []
        anim_data['icon_rotation'] = 0.0
        
        opacity_anim = self._create_animation(
            index, anim_data, 150, QEasingCurve.Type.InCubic,
            anim_data.get('opacity', 1.0), 0.0, 'opacity',
            lambda: self._cleanup_animation(index, is_chevron=False)
        )
        
        opacity_anim.start()
    

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        # Siempre obtener el ancho ACTUAL del viewport para evitar desplazamiento de líneas
        viewport_width = self._view.viewport().width()
        
        # Verificar has_chevron una sola vez al inicio
        item = index.model().itemFromIndex(index) if hasattr(index.model(), 'itemFromIndex') else None
        has_chevron = item and item.rowCount() > 0
        is_root = not index.parent().isValid()
        should_draw_separator = has_chevron or is_root
        
        # Aplicar animaciones
        anim_data = self._animations.get(index)
        opacity = 1.0
        icon_rotation = 0.0
        chevron_rotation = None
        chevron_opacity = 1.0
        bg_highlight_opacity = 0.0
        is_child_anim = False
        is_chevron_anim = False
        
        if anim_data:
            is_chevron_anim = 'chevron_rotation' in anim_data
            is_child_anim = 'opacity' in anim_data and 'chevron_rotation' not in anim_data
        
        if is_chevron_anim:
            chevron_rotation = anim_data.get('chevron_rotation', None)
            chevron_opacity = anim_data.get('chevron_opacity', 1.0)
            bg_highlight_opacity = anim_data.get('bg_highlight_opacity', 0.0)
        elif is_child_anim:
            opacity = anim_data.get('opacity', 1.0)
            icon_rotation = anim_data.get('icon_rotation', 0.0)
        
        painter.save()
        try:
            # Pintar highlight del fondo (solo para nodo padre en expansión)
            if bg_highlight_opacity > 0.0:
                highlight_color = QColor(255, 255, 255, int(bg_highlight_opacity * 255))
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(highlight_color))
                painter.drawRoundedRect(option.rect, 6, 6)
            
            # Calcular rectángulo para feedback (hover/selected) - estilo Finder exacto
            # El hover cubre toda la línea incluyendo controles (chevron y tres puntitos)
            pad_x_right = self.CONTROLS_AREA_PAD_X_RIGHT  # Padding del sidebar derecho
            separator_x = self._calculate_separator_line_x(viewport_width)
            left = 0  # Desde el borde izquierdo del viewport
            # El hover siempre llega hasta el margen derecho, cubriendo controles
            right = viewport_width - pad_x_right
            top = option.rect.top()
            bottom = option.rect.bottom()
            
            feedback_rect = None
            if right > left and bottom > top:
                feedback_rect = QRect(left, top, right - left, bottom - top)
            
            # Pintar fondo de selección primero (debajo del hover) - estilo Finder rectangular
            if option.state & QStyle.State.State_Selected and feedback_rect:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # Sin antialiasing para bordes rectos
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(self._selected_bg))
                painter.drawRect(feedback_rect)  # Rectángulo sin bordes redondeados - estilo Finder
            
            # Pintar hover background si es necesario (encima de selected) - estilo Finder rectangular
            if option.state & QStyle.State.State_MouseOver and feedback_rect:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # Sin antialiasing para bordes rectos
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(self._hover_bg))
                painter.drawRect(feedback_rect)  # Rectángulo sin bordes redondeados - estilo Finder
            
            # Dibujar líneas separadoras ANTES de aplicar opacidad de animación
            # para que siempre aparezcan con opacidad 1 (sin retraso visual)
            separator_y = option.rect.bottom()
            # Todas las líneas horizontales llegan hasta el final del viewport
            horizontal_right = viewport_width - pad_x_right
            
            # Línea horizontal (siempre hasta el final)
            painter.setPen(QPen(self.SEPARATOR_HORIZONTAL_COLOR, 1))
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            painter.drawLine(0, separator_y, horizontal_right, separator_y)
            
            # Línea vertical (solo si hay controles)
            if should_draw_separator:
                painter.setPen(QPen(self.SEPARATOR_VERTICAL_COLOR, 1))
                painter.drawLine(
                    int(separator_x), 
                    int(option.rect.top() + self.SEPARATOR_VERTICAL_MARGIN_TOP), 
                    int(separator_x), 
                    int(option.rect.bottom() - self.SEPARATOR_VERTICAL_MARGIN_BOTTOM)
                )
            
            # Aplicar opacidad DESPUÉS de dibujar las líneas (solo para hijos en animación)
            if is_child_anim and opacity < 1.0:
                painter.setOpacity(opacity)
            
            # Aplicar rotación del icono (solo al icono, después de pintar el fondo)
            if abs(icon_rotation) > 0.01:
                # Guardar estado antes de rotar el icono
                painter.save()
                style = self._view.style()
                deco_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemDecoration, option, self._view)
                if deco_rect.isValid():
                    icon_center_x = deco_rect.center().x()
                    icon_center_y = deco_rect.center().y()
                    # Aplicar rotación solo al icono
                    icon_transform = QTransform()
                    icon_transform.translate(icon_center_x, icon_center_y)
                    icon_transform.rotate(icon_rotation * 0.5)
                    icon_transform.translate(-icon_center_x, -icon_center_y)
                    painter.setTransform(icon_transform, combine=True)
            
            original_state = option.state
            option.state = option.state & ~QStyle.State.State_Selected
            
            # Alinear texto de subcarpetas con texto de raíces (no con icono)
            icon = index.data(Qt.ItemDataRole.DecorationRole)
            has_icon = icon and isinstance(icon, QIcon) and not icon.isNull()
            is_subfolder = index.parent().isValid()
            
            # Establecer color diferente para raíces (más fuerte) e hijas (más claro)
            palette = option.palette
            if is_subfolder:
                # Carpetas hijas: gris más claro (más tenue)
                palette.setColor(palette.ColorRole.Text, QColor("#B0B5BA"))  # Gris claro
            else:
                # Carpetas raíz: gris más fuerte (más visible)
                palette.setColor(palette.ColorRole.Text, QColor("#E6E6E6"))  # Gris más fuerte
            option.palette = palette
            
            original_rect = option.rect
            if not has_icon and is_subfolder:
                icon_size = self._view.iconSize()
                if icon_size.isValid():
                    icon_space = icon_size.width() + 4
                    option.rect = option.rect.adjusted(icon_space, 0, 0, 0)
            
            # Recortar el texto para que no sobrepase la línea separadora
            if should_draw_separator:
                text_clip_right = separator_x - self.SEPARATOR_VERTICAL_TEXT_MARGIN
                if option.rect.right() > text_clip_right:
                    option.rect.setRight(text_clip_right)
            
            super().paint(painter, option, index)
            option.state = original_state
            option.rect = original_rect
            
            # Pintar chevron blanco al lado derecho si el item tiene hijos
            if has_chevron:
                is_expanded = self._view.isExpanded(index)
                rotation = 90.0 if is_expanded else 0.0
                self._paint_chevron_right(painter, option, index, rotation, chevron_opacity)
            
            # Pintar tres puntitos solo en carpetas raíz (sin padre)
            if is_root:
                self._paint_menu_button(painter, option, index)
            
            # Restaurar estado del icono si se aplicó rotación
            if abs(icon_rotation) > 0.01:
                painter.restore()
        finally:
            painter.restore()
    
    def _paint_menu_button(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        """Pintar botón de tres puntitos solo en carpetas raíz."""
        menu_rect = self._get_menu_button_rect(option, index)
        if not menu_rect.isValid():
            return
        
        menu_rect_abs = calculate_menu_rect_viewport(menu_rect, option.rect)
        
        painter.save()
        try:
            sidebar = find_sidebar(self._view)
            is_hovered = sidebar and sidebar._hovered_menu_index == index if sidebar else False
            
            dot_color = QColor(255, 255, 255)  # Color blanco
            dot_color.setAlpha(255 if is_hovered else 200)  # Ligeramente más transparente cuando no está hover
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(dot_color))
            
            dot_radius = 2.0
            dot_spacing = 4
            center_y = menu_rect_abs.center().y() - 4  # Subido 4px más para alineación visual (mantener offset visual)
            start_x = menu_rect_abs.center().x() - dot_spacing
            
            for i in range(3):
                x = start_x + (i * dot_spacing)
                painter.drawEllipse(QPoint(int(x), int(center_y)), int(dot_radius), int(dot_radius))
        finally:
            painter.restore()
    
    def _get_menu_button_rect(self, option: QStyleOptionViewItem, index) -> QRect:
        # Retorna coordenadas RELATIVAS a option.rect (no absolutas del viewport)
        # Usar constantes centralizadas
        button_size = self.MENU_BUTTON_SIZE
        
        # Calcular posición desde el borde derecho del viewport para alineación consistente
        # Los tres puntitos deben estar a la derecha de la línea separadora
        # Línea está en: viewport_width - TOTAL_OFFSET (58)
        # Tres puntitos deben estar en: viewport_width - PAD_X_RIGHT - PADDING - OFFSET (22)
        viewport_width = self._view.viewport().width()
        right_abs = viewport_width - self.CONTROLS_AREA_PAD_X_RIGHT - self.CONTROLS_AREA_PADDING - self.CONTROLS_AREA_OFFSET
        
        # Convertir a coordenadas RELATIVAS a option.rect
        # right_abs es coordenada absoluta del viewport, convertir a relativa del item
        left_rel = right_abs - button_size - option.rect.left()
        # Asegurar que no se salga del rect del item por la izquierda (pero permitir que se extienda más allá del right si es necesario para alineación)
        left_rel = max(0, left_rel)
        
        # Posición vertical: más arriba en la esquina (RELATIVA)
        item_height = option.rect.height()
        center_y_rel = (item_height // 2) - self.MENU_BUTTON_VERTICAL_OFFSET
        top_rel = center_y_rel - button_size // 2
        top_rel = max(self.MENU_BUTTON_MIN_TOP_MARGIN, top_rel)  # Mínimo desde arriba para mantener margen
        bottom_rel = min(item_height, top_rel + button_size)  # No salirse por abajo
        
        # Ajustar height si se recortó
        height = bottom_rel - top_rel
        
        # Retornar coordenadas RELATIVAS a option.rect
        return QRect(left_rel, top_rel, button_size, height)
    
    def _calculate_chevron_center(self, option: QStyleOptionViewItem, index: QModelIndex) -> tuple[int, int]:
        """
        Calcular posición central del chevron (center_x, center_y).
        Usado tanto para dibujo como para área clickeable para asegurar alineación perfecta.
        """
        menu_rect = self._get_menu_button_rect(option, index)
        if not menu_rect.isValid():
            # Fallback si no hay menú (para items que no son raíz)
            style = self._view.style()
            text_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, option, self._view)
            if text_rect.isValid():
                center_x = text_rect.right() - self.CONTROLS_AREA_OFFSET
            else:
                center_x = option.rect.right() - self.CONTROLS_AREA_BUTTON_SIZE
            item_height = option.rect.height()
            center_y = (item_height // 2) + self.CHEVRON_VERTICAL_OFFSET
        else:
            menu_rect_abs = calculate_menu_rect_viewport(menu_rect, option.rect)
            # Misma posición X que los tres puntitos (centrado)
            center_x = menu_rect_abs.center().x()
            # Posición Y: más separado debajo de los tres puntitos
            # Los tres puntitos están en: menu_rect_abs.center().y() - 4
            dot_radius = 2.0
            center_y = menu_rect_abs.center().y() - 4 + dot_radius + self.CHEVRON_VERTICAL_SPACING
        
        return center_x, center_y
    
    def _get_chevron_clickable_rect(self, option: QStyleOptionViewItem, index: QModelIndex) -> QRect:
        """
        Calcular el área clickeable del chevron en coordenadas RELATIVAS a option.rect.
        Usa _calculate_chevron_center() para asegurar alineación perfecta con el dibujo.
        """
        clickable_width = self.CHEVRON_CLICKABLE_WIDTH
        clickable_height = self.CHEVRON_CLICKABLE_HEIGHT
        
        # Usar método centralizado para calcular posición
        center_x, center_y = self._calculate_chevron_center(option, index)
        
        # Calcular área clickeable centrada en center_x, center_y
        # Área aumentada hacia abajo, izquierda y derecha para facilitar el click
        chevron_x_rel = center_x - option.rect.left() - clickable_width // 2
        chevron_y_rel = center_y - option.rect.top() - 8  # Desplazado hacia arriba para que el área se extienda más hacia abajo
        
        # Asegurar que el área clickeable esté dentro del área de controles (a la derecha de la línea)
        viewport_width = self._view.viewport().width()
        line_x = self._calculate_separator_line_x(viewport_width)
        line_x_rel = line_x - option.rect.left()
        
        # Asegurar que el área clickeable esté a la derecha de la línea
        if chevron_x_rel < line_x_rel + 2:
            chevron_x_rel = line_x_rel + 2
        
        # Asegurar que el área no se salga del rect del item
        chevron_x_rel = max(chevron_x_rel, 0)
        chevron_y_rel = max(chevron_y_rel, 0)
        
        # Ajustar tamaño si se sale del rect
        available_width = option.rect.width() - chevron_x_rel
        available_height = option.rect.height() - chevron_y_rel
        clickable_width = min(clickable_width, available_width)
        clickable_height = min(clickable_height, available_height)
        
        # Retornar coordenadas RELATIVAS a option.rect
        return QRect(chevron_x_rel, chevron_y_rel, clickable_width, clickable_height)
    
    def _paint_chevron_right(self, painter: QPainter, option: QStyleOptionViewItem, index, rotation: float, opacity: float) -> None:
        """Pintar chevron blanco elegante tipo Mac debajo de los tres puntitos."""
        chevron_size = self.CHEVRON_SIZE
        
        # Usar método centralizado para calcular posición (mismo que área clickeable)
        center_x, center_y = self._calculate_chevron_center(option, index)
        
        painter.save()
        try:
            # Aplicar opacidad del chevron
            if opacity < 1.0:
                painter.setOpacity(opacity)
            
            # Aplicar rotación centrada en el chevron
            chevron_transform = QTransform()
            chevron_transform.translate(center_x, center_y)
            chevron_transform.rotate(rotation)
            chevron_transform.translate(-center_x, -center_y)
            painter.setTransform(chevron_transform, combine=True)
            
            # Color gris claro elegante tipo Mac
            chevron_color = QColor("#D0D5DA")
            chevron_color.setAlpha(int(255 * opacity))
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            
            # Chevron hueco: solo contorno, sin relleno - estilo Mac elegante
            pen_width = 2.0  # Grosor del contorno aumentado para más presencia y elegancia
            chevron_pen = QPen(chevron_color, pen_width)
            chevron_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            chevron_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(chevron_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)  # Sin relleno
            
            # Diseño elegante tipo Mac: chevron más ancho y equilibrado
            # Estilo SF Symbols de macOS: proporciones más generosas y elegantes
            half_size = chevron_size * 0.5
            # Proporciones tipo Mac mejoradas: más ancho y elegante
            width_factor = 0.65  # Ancho aumentado para más presencia (antes 0.5)
            height_factor = 0.9  # Altura ligeramente aumentada para mejor proporción
            
            # Puntos para el chevron (sin base): solo dos líneas en V más anchas
            # Lado izquierdo más separado para crear un chevron más ancho
            left_offset = half_size * width_factor
            top_left = QPoint(int(center_x - left_offset), int(center_y - half_size * height_factor))  # Izquierda arriba
            bottom_left = QPoint(int(center_x - left_offset), int(center_y + half_size * height_factor))  # Izquierda abajo
            # Punta derecha más pronunciada y equilibrada
            tip_right = QPoint(int(center_x + half_size * 0.7), int(center_y))  # Punta derecha más ancha y elegante
            
            # Dibujar solo las dos líneas del chevron (sin la base)
            painter.drawLine(top_left, tip_right)  # Línea superior
            painter.drawLine(tip_right, bottom_left)  # Línea inferior
        finally:
            painter.restore()

    def _calculate_separator_line_x(self, viewport_width: int) -> int:
        """Calcular posición X de la línea separadora desde el borde derecho del viewport."""
        return viewport_width - self.CONTROLS_AREA_TOTAL_OFFSET
    
    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        """Mantener tamaño estándar; delegar en comportamiento por defecto."""
        return super().sizeHint(option, index)
    
    def editorEvent(self, event: QEvent, model, option: QStyleOptionViewItem, index) -> bool:
        """Interceptar eventos de mouse para detectar clic en botón de menú (tres puntitos)."""
        if event.type() == QEvent.Type.MouseButtonPress:
            mouse_event = event
            if isinstance(mouse_event, QMouseEvent) and mouse_event.button() == Qt.MouseButton.LeftButton:
                if not index.parent().isValid():
                    menu_rect = self._get_menu_button_rect(option, index)
                    if menu_rect.isValid():
                        menu_rect_viewport = calculate_menu_rect_viewport(menu_rect, option.rect)
                        
                        if menu_rect_viewport.contains(mouse_event.pos()):
                            sidebar = find_sidebar(self._view)
                            if sidebar:
                                folder_path = index.data(Qt.ItemDataRole.UserRole)
                                if folder_path:
                                    sidebar._show_root_menu(folder_path, mouse_event.globalPos())
                            return True
        
        return super().editorEvent(event, model, option, index)
