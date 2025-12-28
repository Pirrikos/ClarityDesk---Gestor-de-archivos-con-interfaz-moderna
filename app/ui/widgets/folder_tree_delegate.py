from PySide6.QtCore import QModelIndex, QPoint, QRect, QSize, Qt, QEasingCurve, QTimer, QVariantAnimation
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QMouseEvent, QPainter, QPen, QTransform
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QTreeView, QStyle

from app.ui.widgets.folder_tree_constants import (
    CONTROLS_AREA_PAD_X_RIGHT,
    CONTROLS_AREA_PADDING,
    CONTROLS_AREA_OFFSET,
    CONTROLS_AREA_BUTTON_SIZE,
    CONTROLS_AREA_SEPARATOR_MARGIN,
    CONTROLS_AREA_TOTAL_OFFSET,
    CHEVRON_CLICKABLE_WIDTH,
    CHEVRON_CLICKABLE_HEIGHT,
    CHEVRON_VERTICAL_OFFSET,
    SEPARATOR_VERTICAL_COLOR,
    SEPARATOR_VERTICAL_MARGIN_TOP,
    SEPARATOR_VERTICAL_MARGIN_BOTTOM,
    SEPARATOR_VERTICAL_TEXT_MARGIN,
    ROOT_ITEM_TOP_SPACING,
)
from app.core.constants import TEXT_SUBFOLDER
from app.ui.widgets.folder_tree_styles import TEXT_PRIMARY


class FolderTreeSectionDelegate(QStyledItemDelegate):
    """Delegate de pintura para agrupar visualmente la sección activa como bloque tipo tarjeta."""

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
        viewport_width = self._view.viewport().width()
        
        item = index.model().itemFromIndex(index) if hasattr(index.model(), 'itemFromIndex') else None
        has_chevron = item and item.rowCount() > 0
        is_root = not index.parent().isValid()
        should_draw_separator = has_chevron or is_root
        
        # Ajustar rectángulo para items raíz: desplazar contenido hacia abajo
        if is_root:
            adjusted_rect = QRect(option.rect)
            adjusted_rect.setTop(option.rect.top() + ROOT_ITEM_TOP_SPACING)
            adjusted_rect.setHeight(option.rect.height() - ROOT_ITEM_TOP_SPACING)
            option.rect = adjusted_rect
        
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
            if bg_highlight_opacity > 0.0:
                highlight_color = QColor(255, 255, 255, int(bg_highlight_opacity * 255))
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(highlight_color))
                painter.drawRoundedRect(option.rect, 6, 6)
            
            pad_x_right = CONTROLS_AREA_PAD_X_RIGHT
            separator_x = self._calculate_separator_line_x(viewport_width)
            left = 0
            right = viewport_width - pad_x_right
            top = option.rect.top()
            bottom = option.rect.bottom()
            
            feedback_rect = None
            if right > left and bottom > top:
                feedback_rect = QRect(left, top, right - left, bottom - top)
            
            if option.state & QStyle.State.State_Selected and feedback_rect:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(self._selected_bg))
                painter.drawRect(feedback_rect)
            
            if option.state & QStyle.State.State_MouseOver and feedback_rect:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(self._hover_bg))
                painter.drawRect(feedback_rect)
            
            separator_y = option.rect.bottom()
            horizontal_right = viewport_width - pad_x_right
            
            # Líneas horizontales temporalmente invisibles
            # painter.setPen(QPen(self.SEPARATOR_HORIZONTAL_COLOR, 1))
            # painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            # painter.drawLine(0, separator_y, horizontal_right, separator_y)
            
            if should_draw_separator:
                painter.setPen(QPen(SEPARATOR_VERTICAL_COLOR, 1))
                painter.drawLine(
                    int(separator_x), 
                    int(option.rect.top() + SEPARATOR_VERTICAL_MARGIN_TOP), 
                    int(separator_x), 
                    int(option.rect.bottom() - SEPARATOR_VERTICAL_MARGIN_BOTTOM)
                )
            
            if is_child_anim and opacity < 1.0:
                painter.setOpacity(opacity)
            
            if abs(icon_rotation) > 0.01:
                painter.save()
                style = self._view.style()
                deco_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemDecoration, option, self._view)
                if deco_rect.isValid():
                    icon_center_x = deco_rect.center().x()
                    icon_center_y = deco_rect.center().y()
                    icon_transform = QTransform()
                    icon_transform.translate(icon_center_x, icon_center_y)
                    icon_transform.rotate(icon_rotation * 0.5)
                    icon_transform.translate(-icon_center_x, -icon_center_y)
                    painter.setTransform(icon_transform, combine=True)
            
            original_state = option.state
            option.state = option.state & ~QStyle.State.State_Selected
            
            icon = index.data(Qt.ItemDataRole.DecorationRole)
            has_icon = icon and isinstance(icon, QIcon) and not icon.isNull()
            is_subfolder = index.parent().isValid()
            
            palette = option.palette
            font = option.font
            if is_subfolder:
                palette.setColor(palette.ColorRole.Text, QColor(TEXT_SUBFOLDER))
                font.setWeight(QFont.Weight.Normal)
            else:
                palette.setColor(palette.ColorRole.Text, QColor(TEXT_PRIMARY))
                font.setWeight(QFont.Weight.Medium)
            option.palette = palette
            option.font = font
            
            original_rect = option.rect
            if not has_icon and is_subfolder:
                icon_size = self._view.iconSize()
                if icon_size.isValid():
                    icon_space = icon_size.width() + 4
                    option.rect = option.rect.adjusted(icon_space, 0, 0, 0)
            
            if should_draw_separator:
                text_clip_right = separator_x - SEPARATOR_VERTICAL_TEXT_MARGIN
                if option.rect.right() > text_clip_right:
                    option.rect.setRight(text_clip_right)
            
            super().paint(painter, option, index)
            option.state = original_state
            option.rect = original_rect
            
            # Pintar flecha minimalista al lado derecho si el item tiene hijos
            if has_chevron:
                is_expanded = self._view.isExpanded(index)
                rotation = 90.0 if is_expanded else 0.0  # 0° = derecha, 90° = abajo
                self._paint_chevron_right(painter, option, index, rotation, chevron_opacity)
            
            # Restaurar estado del icono si se aplicó rotación
            if abs(icon_rotation) > 0.01:
                painter.restore()
        finally:
            painter.restore()
    
    def _calculate_chevron_center(self, option: QStyleOptionViewItem, index: QModelIndex) -> tuple[int, int]:
        viewport_width = self._view.viewport().width()
        center_x = viewport_width - CONTROLS_AREA_PAD_X_RIGHT - CONTROLS_AREA_PADDING - CONTROLS_AREA_OFFSET - (CONTROLS_AREA_BUTTON_SIZE // 2)
        # Centro vertical absoluto del item
        center_y = option.rect.top() + (option.rect.height() // 2) + CHEVRON_VERTICAL_OFFSET
        
        return center_x, center_y
    
    def _get_chevron_clickable_rect(self, option: QStyleOptionViewItem, index: QModelIndex) -> QRect:
        clickable_width = CHEVRON_CLICKABLE_WIDTH
        clickable_height = CHEVRON_CLICKABLE_HEIGHT
        
        center_x, center_y = self._calculate_chevron_center(option, index)
        
        chevron_x_rel = center_x - option.rect.left() - clickable_width // 2
        chevron_y_rel = center_y - option.rect.top() - 8
        
        viewport_width = self._view.viewport().width()
        line_x = self._calculate_separator_line_x(viewport_width)
        line_x_rel = line_x - option.rect.left()
        
        if chevron_x_rel < line_x_rel + 2:
            chevron_x_rel = line_x_rel + 2
        
        chevron_x_rel = max(chevron_x_rel, 0)
        chevron_y_rel = max(chevron_y_rel, 0)
        
        available_width = option.rect.width() - chevron_x_rel
        available_height = option.rect.height() - chevron_y_rel
        clickable_width = min(clickable_width, available_width)
        clickable_height = min(clickable_height, available_height)
        
        return QRect(chevron_x_rel, chevron_y_rel, clickable_width, clickable_height)
    
    def _paint_chevron_right(self, painter: QPainter, option: QStyleOptionViewItem, index, rotation: float, opacity: float) -> None:
        """Pintar tres puntos violetas centrados que indican que el item tiene hijos."""
        center_x, center_y = self._calculate_chevron_center(option, index)
        
        painter.save()
        try:
            if opacity < 1.0:
                painter.setOpacity(opacity)
            
            dot_color = QColor(138, 43, 226)
            dot_color.setAlpha(int(255 * opacity))
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(dot_color))
            
            dot_radius = 2.0
            dot_spacing = 5
            
            painter.drawEllipse(
                QPoint(int(center_x), int(center_y - dot_spacing)),
                int(dot_radius), int(dot_radius)
            )
            painter.drawEllipse(
                QPoint(int(center_x), int(center_y)),
                int(dot_radius), int(dot_radius)
            )
            painter.drawEllipse(
                QPoint(int(center_x), int(center_y + dot_spacing)),
                int(dot_radius), int(dot_radius)
            )
        finally:
            painter.restore()

    def _calculate_separator_line_x(self, viewport_width: int) -> int:
        return viewport_width - CONTROLS_AREA_TOTAL_OFFSET
    
    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        """Aumentar altura para items raíz para crear espacio arriba."""
        base_size = super().sizeHint(option, index)
        is_root = not index.parent().isValid()
        if is_root:
            return QSize(base_size.width(), base_size.height() + ROOT_ITEM_TOP_SPACING)
        return base_size
