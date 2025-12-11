"""
FolderTreeHandlers - Event handlers for FolderTreeSidebar.

Handles tree clicks, context menu, and add button clicks.
"""

import os

from PySide6.QtCore import QModelIndex, QPoint, Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QFileDialog, QMenu, QTreeView


def handle_tree_click(
    index: QModelIndex,
    model: QStandardItemModel,
    tree_view: QTreeView
) -> str:
    """
    Handle tree item click - expand node and return folder path.
    
    Args:
        index: Clicked model index.
        model: QStandardItemModel instance.
        tree_view: QTreeView instance.
        
    Returns:
        Folder path if valid, None otherwise.
    """
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
    
    folder_path = item.data(Qt.ItemDataRole.UserRole)
    if folder_path and os.path.isdir(folder_path):
        return folder_path
    
    return None


def handle_add_button_click(parent_widget) -> str:
    """
    Handle + button click - open folder picker.
    
    Args:
        parent_widget: Parent widget for dialog.
        
    Returns:
        Selected folder path, or None if cancelled.
    """
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
    """
    Handle context menu request on tree item.
    
    Args:
        position: Menu position.
        tree_view: QTreeView instance.
        model: QStandardItemModel instance.
        
    Returns:
        Folder path for context menu, or None if invalid.
    """
    index = tree_view.indexAt(position)
    if not index.isValid():
        return None
    
    item = model.itemFromIndex(index)
    if not item:
        return None
    
    folder_path = item.data(Qt.ItemDataRole.UserRole)
    return folder_path if folder_path else None

