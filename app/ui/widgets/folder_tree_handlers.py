"""
FolderTreeHandlers - Event handlers for FolderTreeSidebar.

Handles tree clicks, context menu, and add button clicks.
"""

import os

from PySide6.QtCore import QModelIndex, QPoint, Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QFileDialog, QMenu, QTreeView
from app.services.tab_helpers import validate_folder


def handle_tree_click(
    index: QModelIndex,
    model: QStandardItemModel,
    tree_view: QTreeView
) -> str:
    if not index.isValid():
        return None
    
    item = model.itemFromIndex(index)
    if not item:
        return None
    
    # Expand/collapse node if it has children
    if item.rowCount() > 0:
        if tree_view.isExpanded(index):
            tree_view.collapse(index)
        else:
            tree_view.expand(index)
    
    return None


def resolve_folder_path(
    index: QModelIndex,
    model: QStandardItemModel
) -> str:
    if not index.isValid():
        return None
    item = model.itemFromIndex(index)
    if not item:
        return None
    folder_path = item.data(Qt.ItemDataRole.UserRole)
    if folder_path and validate_folder(folder_path):
        return folder_path
    return None


def handle_add_button_click(parent_widget) -> str:
    """Abrir selector de carpeta al hacer click en botón +."""
    folder_path = QFileDialog.getExistingDirectory(
        parent_widget,
        "Select Folder",
        "",
        QFileDialog.Option.ShowDirsOnly
    )
    
    return folder_path if folder_path else None


def handle_context_menu(
    position: QPoint,
    tree_view: QTreeView,
    model: QStandardItemModel
) -> str:
    """Obtener path de carpeta para menú contextual en item del árbol."""
    index = tree_view.indexAt(position)
    if not index.isValid():
        return None
    
    item = model.itemFromIndex(index)
    if not item:
        return None
    
    folder_path = item.data(Qt.ItemDataRole.UserRole)
    return folder_path if folder_path else None

