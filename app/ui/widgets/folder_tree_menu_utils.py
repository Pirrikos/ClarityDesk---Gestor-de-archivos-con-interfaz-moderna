"""
FolderTreeMenuUtils - Utilidades para cálculo de coordenadas del menú contextual.

Funciones compartidas para crear opciones de estilo desde índices del árbol.
"""

from PySide6.QtCore import QModelIndex, QRect
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem, QTreeView

from app.ui.widgets.folder_tree_constants import ROOT_ITEM_TOP_SPACING


def create_option_from_index(
    tree_view: QTreeView,
    index: QModelIndex
) -> tuple[QStyleOptionViewItem | None, QRect | None]:
    """Crear QStyleOptionViewItem desde índice aplicando ajustes de espaciado para items raíz."""
    visual_rect = tree_view.visualRect(index)
    if not visual_rect.isValid():
        return None, None
    
    option = QStyleOptionViewItem()
    option.initFrom(tree_view)
    option.rect = visual_rect
    option.state = QStyle.State.State_Enabled
    
    is_root = not index.parent().isValid()
    if is_root:
        adjusted_rect = QRect(visual_rect)
        adjusted_rect.setTop(visual_rect.top() + ROOT_ITEM_TOP_SPACING)
        adjusted_rect.setHeight(visual_rect.height() - ROOT_ITEM_TOP_SPACING)
        option.rect = adjusted_rect
        return option, adjusted_rect
    
    return option, visual_rect

