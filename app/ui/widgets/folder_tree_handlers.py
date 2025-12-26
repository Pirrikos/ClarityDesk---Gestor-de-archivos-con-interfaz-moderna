"""
FolderTreeHandlers - Event handlers for FolderTreeSidebar.

Handles tree clicks and path resolution.
"""

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QTreeView
from app.services.tab_helpers import validate_folder


def handle_tree_click(
    index: QModelIndex,
    model: QStandardItemModel,
    tree_view: QTreeView
) -> str:
    """Expand/collapse node if it has children."""
    if not index.isValid():
        return None
    
    item = model.itemFromIndex(index)
    if not item:
        return None
    
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
    """Resolve folder path from tree index."""
    if not index.isValid():
        return None
    item = model.itemFromIndex(index)
    if not item:
        return None
    folder_path = item.data(Qt.ItemDataRole.UserRole)
    if folder_path and validate_folder(folder_path):
        return folder_path
    return None

