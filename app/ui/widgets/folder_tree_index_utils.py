"""
FolderTreeIndexUtils - Utilidades para trabajar con QModelIndex en árboles.

Funciones puras para manipulación de índices del árbol.
"""

from PySide6.QtCore import QModelIndex


def get_top_level_ancestor(index: QModelIndex) -> QModelIndex:
    """Subir hasta el ancestro de nivel 1 (sin padre)."""
    i = index
    while i.parent().isValid():
        i = i.parent()
    return i


def is_descendant_of(index: QModelIndex, ancestor: QModelIndex) -> bool:
    """Comprobar si index pertenece al subárbol de ancestor."""
    i = index
    while i.isValid():
        if i == ancestor:
            return True
        i = i.parent()
    return False


def is_direct_child_of(index: QModelIndex, parent_index: QModelIndex) -> bool:
    """Comprobar si index es hijo inmediato de parent_index."""
    return index.parent().isValid() and (index.parent() == parent_index)


def get_indent_depth(index: QModelIndex, indentation: int) -> int:
    """Calcular profundidad de indentación del índice."""
    depth = 0
    i = index
    while i.parent().isValid():
        depth += 1
        i = i.parent()
    return indentation * depth

