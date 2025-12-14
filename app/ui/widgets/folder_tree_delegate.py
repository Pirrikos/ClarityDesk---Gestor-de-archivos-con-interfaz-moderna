from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QEasingCurve, QTimer, QVariantAnimation
from PySide6.QtGui import QBrush, QColor, QFont, QMouseEvent, QPainter, QPen, QPolygon, QTransform
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QTreeView, QStyle

from app.ui.widgets.folder_tree_menu_utils import calculate_menu_rect_viewport
from app.ui.widgets.folder_tree_widget_utils import find_sidebar



class FolderTreeSectionDelegate(QStyledItemDelegate):
    """Delegate de pintura para agrupar visualmente la sección activa como bloque tipo tarjeta."""

    def __init__(self, tree_view: QTreeView):
        """Guardar referencia al QTreeView para calcular rectángulos visibles."""
        super().__init__(tree_view)
        self._view = tree_view
        # Skin oscuro tipo Raycast
        self._block_bg = QColor(31, 34, 40, 168)  # Tinte oscuro con ligera transparencia
        self._hover_bg = QColor(31, 34, 40, 220)  # Hover suave
        self._text_color = QColor("#E6E7EA")
        self._radius = 12  # Bordes redondeados amplios
        self._padding = 6  # Aire alrededor del contenido
        
        # Animation state tracking
        # Para hijos: {opacity, icon_rotation, animations}
        # Para nodos padre (chevron): {chevron_rotation, chevron_opacity, bg_highlight_opacity, animations}
        self._animations: dict[object, dict] = {}
        self._setup_animation_tracking()
    
    def _setup_animation_tracking(self) -> None:
        """Setup animation tracking for expansion/collapse."""
        if not self._view:
            return
        
        # Track expansion state changes
        self._view.expanded.connect(self._on_expanded)
        self._view.collapsed.connect(self._on_collapsed)
    
    def _create_animation_updater(self, index, key: str, anim_data: dict):
        """Crear función de actualización para animaciones que repinta el viewport."""
        def update_value(value):
            anim_data[key] = float(value)
            if self._view:
                visual_rect = self._view.visualRect(index)
                if visual_rect.isValid():
                    self._view.viewport().update(visual_rect)
        return update_value
    
    def _cancel_existing_animations(self, index) -> None:
        """Cancelar animaciones existentes para un índice."""
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
        """Limpiar todas las animaciones activas."""
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
        """Helper para crear animaciones con configuración común."""
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
        """Animate chevron rotation + fade on expansion (140ms, OutCubic)."""
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
        """Animate chevron rotation on collapse (140ms, OutCubic)."""
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
        """Iniciar fadeout del highlight después de la expansión."""
        fadeout_anim = self._create_animation(
            index, anim_data, 120, QEasingCurve.Type.InCubic,
            anim_data.get('bg_highlight_opacity', 0.04), 0.0, 'bg_highlight_opacity',
            lambda: self._cleanup_animation(index, is_chevron=True)
        )
        fadeout_anim.start()
    
    def _cleanup_animation(self, index, is_chevron: bool = False) -> None:
        """Clean up animation data after completion."""
        if index in self._animations:
            anim_data = self._animations[index]
            if is_chevron and 'chevron_rotation' not in anim_data:
                return
            for anim in anim_data.get('animations', []):
                anim.deleteLater()
            QTimer.singleShot(200, lambda idx=index: self._animations.pop(idx, None))
    
    def _iterate_children(self, index, callback) -> None:
        """Iterar sobre hijos de un índice y aplicar callback."""
        model = self._view.model()
        if not model:
            return
        child_count = model.rowCount(index)
        for i in range(child_count):
            child_index = model.index(i, 0, index)
            if child_index.isValid():
                callback(child_index)
    
    def _on_expanded(self, index) -> None:
        """Handle node expansion - animate chevron + highlight, then fade-in for children."""
        if not index.isValid():
            return
        self._animate_chevron_expand(index)
        self._iterate_children(index, self._animate_child_expand)
    
    def _on_collapsed(self, index) -> None:
        """Handle node collapse - animate chevron, then fade-out for children."""
        if not index.isValid():
            return
        self._animate_chevron_collapse(index)
        self._iterate_children(index, self._animate_child_collapse)
    
    def _animate_child_expand(self, index) -> None:
        """Animate child item expansion with fade-in and icon pivot (180ms)."""
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
        """Animate child item collapse - limpio y seco, sin efectos adicionales."""
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
        # Apply animation effects
        anim_data = self._animations.get(index)
        opacity = 1.0
        icon_rotation = 0.0
        chevron_rotation = None
        chevron_opacity = 1.0
        bg_highlight_opacity = 0.0
        
        # Detectar si es animación de chevron (nodo padre) o de hijo
        is_chevron_anim = anim_data and 'chevron_rotation' in anim_data
        is_child_anim = anim_data and 'opacity' in anim_data and 'chevron_rotation' not in anim_data
        
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
            
            # Aplicar opacidad (solo para hijos)
            if is_child_anim and opacity < 1.0:
                painter.setOpacity(opacity)
            
            # Pintar hover background si es necesario
            if option.state & QStyle.State.State_MouseOver:
                style = self._view.style()
                # Compute exact rects for icon (decoration) and text
                text_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, option, self._view)
                deco_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemDecoration, option, self._view)
                union = text_rect.united(deco_rect)
                # Fallback to option.rect if union invalid
                if not union.isValid():
                    union = option.rect
                # Padding and clamping inside item rect
                pad_x = 6
                pad_y = 3
                left = max(option.rect.left(), union.left() - pad_x)
                right = min(option.rect.right(), union.right() + pad_x)
                top = max(option.rect.top(), union.top() - pad_y)
                bottom = min(option.rect.bottom(), union.bottom() + pad_y)
                if right > left and bottom > top:
                    hover_rect = QRect(left, top, right - left, bottom - top)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(self._hover_bg))
                    painter.drawRoundedRect(hover_rect, 6, 6)
            
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
            
            # Pintar el contenido (icono y texto) primero para tener las dimensiones correctas
            super().paint(painter, option, index)
            
            # Pintar chevron DESPUÉS del contenido para usar las dimensiones correctas
            # (animado o estático, solo si el nodo tiene hijos)
            model = index.model()
            if model and model.rowCount(index) > 0:
                if chevron_rotation is not None:
                    # Chevron animado
                    self._paint_chevron(painter, option, index, chevron_rotation, chevron_opacity)
                else:
                    # Chevron estático según estado expandido/colapsado
                    is_expanded = self._view.isExpanded(index)
                    static_rotation = 0.0 if is_expanded else 90.0
                    self._paint_chevron(painter, option, index, static_rotation, 1.0)
            
            # Pintar tres puntitos solo en carpetas raíz (sin padre)
            if not index.parent().isValid():
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
            
            dot_color = QColor(self._text_color)
            dot_color.setAlpha(255 if is_hovered else 180)
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(dot_color))
            
            dot_radius = 2.0
            dot_spacing = 4
            center_y = menu_rect_abs.center().y() - 2
            start_x = menu_rect_abs.center().x() - dot_spacing
            
            for i in range(3):
                x = start_x + (i * dot_spacing)
                painter.drawEllipse(QPoint(int(x), int(center_y)), int(dot_radius), int(dot_radius))
        finally:
            painter.restore()
    
    def _get_menu_button_rect(self, option: QStyleOptionViewItem, index) -> QRect:
        """Obtener rectángulo del botón de menú (tres puntitos) dentro del contenedor del item.
        
        IMPORTANTE: Retorna coordenadas RELATIVAS a option.rect (no absolutas del viewport).
        """
        # Obtener rectángulo del texto para posicionar el botón al lado del texto
        style = self._view.style()
        text_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, option, self._view)
        
        # Calcular posición del botón de forma más robusta
        button_size = 24  # Área de clic más grande
        padding = 4
        
        # Calcular right en coordenadas absolutas primero
        if text_rect.isValid():
            right_abs = text_rect.right() - padding
        else:
            # Fallback: calcular basado en el rect del item
            right_abs = option.rect.right() - padding - 8
        
        # Asegurar que no se salga del rect del item
        right_abs = min(right_abs, option.rect.right() - padding)
        
        # Convertir a coordenadas RELATIVAS a option.rect
        left_rel = right_abs - button_size - option.rect.left()
        left_rel = max(0, left_rel)  # No salirse por la izquierda
        
        # Posición vertical: centrado pero un poco más arriba (RELATIVA)
        item_height = option.rect.height()
        center_y_rel = (item_height // 2) - 2  # Subido 2px desde el centro
        top_rel = center_y_rel - button_size // 2
        top_rel = max(0, top_rel)  # No salirse por arriba
        bottom_rel = min(item_height, top_rel + button_size)  # No salirse por abajo
        
        # Ajustar height si se recortó
        height = bottom_rel - top_rel
        
        # Retornar coordenadas RELATIVAS a option.rect
        return QRect(left_rel, top_rel, button_size, height)
    
    def _paint_chevron(self, painter: QPainter, option: QStyleOptionViewItem, index, rotation: float, opacity: float) -> None:
        """Pintar chevron con rotación y fade (sin modificar geometría)."""
        style = self._view.style()
        deco_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemDecoration, option, self._view)
        
        if not deco_rect.isValid():
            icon_left = option.rect.left() + 16
        else:
            icon_left = deco_rect.left()
        
        chevron_size = 10  # Tamaño del chevron (10px, más grande)
        spacing = 4  # Espacio entre chevron e icono
        
        # Posicionar chevron a la izquierda del icono
        center_x = icon_left - spacing - chevron_size // 2
        center_y = option.rect.center().y()
        
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
            
            # Pintar chevron como triángulo (▶ cuando colapsado, ▼ cuando expandido)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(self._text_color, 1.5))
            painter.setBrush(QBrush(self._text_color))
            
            # Triángulo apuntando a la derecha (▶), rotado según el estado
            # Base: triángulo pequeño que apunta a la derecha
            half_size = chevron_size * 0.5
            points = [
                (center_x - half_size * 0.4, center_y - half_size),  # Izquierda arriba
                (center_x - half_size * 0.4, center_y + half_size),  # Izquierda abajo
                (center_x + half_size * 0.6, center_y)  # Punta derecha
            ]
            
            polygon = QPolygon([QPoint(int(p[0]), int(p[1])) for p in points])
            painter.drawPolygon(polygon)
        finally:
            painter.restore()

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
