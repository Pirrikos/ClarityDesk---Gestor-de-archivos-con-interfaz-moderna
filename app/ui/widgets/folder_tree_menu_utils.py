"""
FolderTreeMenuUtils - Utilidades para el botón de menú (tres puntitos).

Funciones compartidas para cálculo de coordenadas del menú.
"""

from PySide6.QtCore import QModelIndex, QRect
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem, QTreeView


def calculate_menu_rect_viewport(
    menu_rect: QRect,
    visual_rect: QRect
) -> QRect:
    return QRect(
        visual_rect.left() + menu_rect.left(),
        visual_rect.top() + menu_rect.top(),
        menu_rect.width(),
        menu_rect.height()
    )


def create_option_from_index(
    tree_view: QTreeView,
    index: QModelIndex
) -> tuple[QStyleOptionViewItem | None, QRect | None]:
    visual_rect = tree_view.visualRect(index)
    if not visual_rect.isValid():
        return None, None
    
    option = QStyleOptionViewItem()
    option.initFrom(tree_view)
    option.rect = visual_rect
    option.state = QStyle.State.State_Enabled
    
    return option, visual_rect

