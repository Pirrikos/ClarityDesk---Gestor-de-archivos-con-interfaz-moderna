"""
FolderTreeWidgetUtils - Utilidades para widgets del árbol de carpetas.

Funciones para buscar TabManager y otras utilidades compartidas.
"""

from typing import Optional


def find_tab_manager(widget) -> Optional[object]:
    """Buscar TabManager en la cadena de padres del widget."""
    parent = widget.parent()
    while parent:
        if hasattr(parent, '_tab_manager'):
            return parent._tab_manager
        parent = parent.parent()
    return None


def find_sidebar(widget) -> Optional[object]:
    """Buscar FolderTreeSidebar en la cadena de padres del widget."""
    parent = widget.parent()
    while parent:
        if hasattr(parent, '_show_root_menu') and hasattr(parent, '_hovered_menu_index'):
            return parent
        parent = parent.parent()
    return None

