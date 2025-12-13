from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QTreeView, QStyle
import os


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

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()
        try:
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
        finally:
            painter.restore()
        super().paint(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        """Mantener tamaño estándar; delegar en comportamiento por defecto."""
        return super().sizeHint(option, index)

    def _compute_group_block_rect_immediate_children(self, top_index) -> QRect:
        """Unir rects visibles del título y de hijos inmediatos, con padding, recortando margen izquierdo."""
        view = self._view
        if view is None:
            return QRect()
        rect = view.visualRect(top_index)
        model = top_index.model()
        union_rect = QRect(rect)
        viewport_rect = view.viewport().rect()
        min_label_left = rect.left() + 8
        if view.isExpanded(top_index):
            rows = model.rowCount(top_index)
            for r in range(rows):
                child = model.index(r, 0, top_index)
                child_rect = view.visualRect(child)
                if child_rect.isValid() and viewport_rect.intersects(child_rect):
                    union_rect = union_rect.united(child_rect)
                    label_left = child_rect.left() + 8
                    if label_left < min_label_left:
                        min_label_left = label_left
        # Añadir padding y redondeo
        union_rect.adjust(-self._padding, -self._padding, self._padding, self._padding)
        union_rect.setLeft(min_label_left)
        # Asegurar que el bloque no sobresale del viewport
        return union_rect.intersected(viewport_rect)

    def _get_active_parent_index(self):
        """Item padre activo según la carpeta abierta; si no se determina, devolver None."""
        view = self._view
        # Buscar TabManager en la cadena de padres del sidebar
        parent = view.parent()
        tab_manager = None
        while parent:
            if hasattr(parent, "_tab_manager"):
                tab_manager = parent._tab_manager
                break
            parent = parent.parent()
        if not tab_manager or not hasattr(tab_manager, "get_active_folder"):
            return None
        active_path = tab_manager.get_active_folder()
        if not active_path:
            return None
        normalized_active = os.path.normpath(active_path)
        # Buscar en el modelo el top-level item cuyo UserRole coincide con la ruta activa
        model = view.model()
        if not model or not hasattr(model, "invisibleRootItem"):
            return None
        root = model.invisibleRootItem()
        for i in range(root.rowCount()):
            item = root.child(i)
            if not item:
                continue
            item_path = item.data(Qt.ItemDataRole.UserRole)
            if item_path and os.path.normpath(item_path) == normalized_active:
                return model.indexFromItem(item)
        return None

    def _is_direct_child_of(self, index, top_index) -> bool:
        """Comprobar si index es hijo inmediato de top_index."""
        return index.parent().isValid() and (index.parent() == top_index)

    def _indent_for(self, index) -> int:
        depth = 0
        i = index
        while i.parent().isValid():
            depth += 1
            i = i.parent()
        return self._view.indentation() * depth

    def _get_top_level_ancestor(self, index):
        """Subir hasta el ancestro de nivel 1 (sin padre)."""
        i = index
        while i.parent().isValid():
            i = i.parent()
        return i

    def _is_descendant_of(self, index, ancestor) -> bool:
        """Comprobar si index pertenece al subárbol de ancestor."""
        i = index
        while i.isValid():
            if i == ancestor:
                return True
            i = i.parent()
        return False

    def _preferred_font_family(self) -> str:
        """Familia de fuente preferida según disponibilidad del sistema."""
        # Nota: Qt elegirá la primera fuente disponible; mantener orden profesional
        return "Inter"
