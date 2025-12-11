"""
FolderTreeModel - Tree model management for FolderTreeSidebar.

Handles tree node insertion, removal, and parent finding logic.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel


def add_focus_path_to_model(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    path: str
) -> QStandardItem:
    """
    Add Focus path to navigation history tree.
    
    Inserts path under its parent ONLY if parent exists in tree.
    Otherwise inserts as root node.
    Skips if path already exists in tree.
    
    Args:
        model: QStandardItemModel instance.
        path_to_item: Dictionary mapping paths to items.
        path: Folder path to add.
        
    Returns:
        Created QStandardItem if added, None if skipped.
    """
    if not path or not os.path.isdir(path):
        return None
    
    normalized_path = os.path.normpath(path)
    
    # Skip if already exists
    if normalized_path in path_to_item:
        return None
    
    # Create item
    folder_name = os.path.basename(normalized_path) or normalized_path
    item = QStandardItem(folder_name)
    # Añadir icono de carpeta
    from PySide6.QtWidgets import QFileIconProvider
    from PySide6.QtCore import QFileInfo
    icon_provider = QFileIconProvider()
    folder_icon = icon_provider.icon(QFileInfo(normalized_path))
    item.setIcon(folder_icon)
    item.setData(normalized_path, Qt.ItemDataRole.UserRole)
    item.setEditable(False)
    
    # Find parent (only if exists, don't create)
    parent_item = find_parent_item(model, path_to_item, normalized_path)
    
    # Insert under parent (or root)
    parent_item.appendRow(item)
    path_to_item[normalized_path] = item
    
    return item


def find_parent_item(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    path: str
) -> QStandardItem:
    """
    Find parent item in tree if exists, otherwise return root.
    
    Does NOT create parents automatically.
    Only returns existing parent nodes.
    
    Args:
        model: QStandardItemModel instance.
        path_to_item: Dictionary mapping paths to items.
        path: Child folder path.
        
    Returns:
        Parent QStandardItem if exists, otherwise root.
    """
    parent_path = os.path.dirname(path)
    if not parent_path or parent_path == path:
        return model.invisibleRootItem()
    
    normalized_parent = os.path.normpath(parent_path)
    
    # Return existing parent if found
    if normalized_parent in path_to_item:
        return path_to_item[normalized_parent]
    
    # Parent doesn't exist - return root
    return model.invisibleRootItem()


def remove_focus_path_from_model(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    path: str
) -> None:
    """
    Remove Focus path from navigation history tree.
    
    Removes node and all its children (breadcrumb hierarchy).
    Does NOT delete folder from filesystem.
    
    Args:
        model: QStandardItemModel instance.
        path_to_item: Dictionary mapping paths to items.
        path: Folder path to remove.
    """
    normalized_path = os.path.normpath(path)
    
    if normalized_path not in path_to_item:
        return
    
    item = path_to_item[normalized_path]
    
    # Remove all children recursively from dict first
    _remove_item_recursive(path_to_item, normalized_path)
    
    # Remove item from model
    parent = item.parent()
    if parent:
        parent.removeRow(item.row())
    else:
        root = model.invisibleRootItem()
        root.removeRow(item.row())


def _remove_item_recursive(path_to_item: dict[str, QStandardItem], path: str) -> None:
    """
    Remove item and all children from path_to_item dict recursively.
    
    Args:
        path_to_item: Dictionary mapping paths to items.
        path: Root path to remove.
    """
    if path not in path_to_item:
        return
    
    item = path_to_item[path]
    
    # Remove all children first
    for i in range(item.rowCount()):
        child_item = item.child(i)
        if child_item:
            child_path = child_item.data(Qt.ItemDataRole.UserRole)
            if child_path:
                _remove_item_recursive(path_to_item, child_path)
    
    # Remove this item
    del path_to_item[path]

