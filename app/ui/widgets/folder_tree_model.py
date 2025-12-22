"""
FolderTreeModel - Tree model management for FolderTreeSidebar.

Handles tree node insertion, removal, and parent finding logic.
"""

import os

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QTreeView

from app.ui.widgets.folder_tree_icon_utils import load_folder_icon_with_fallback, FOLDER_ICON_SIZE


def add_focus_path_to_model(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    path: str
) -> QStandardItem:
    if not path or not os.path.isdir(path):
        return None
    
    normalized_path = os.path.normpath(path)
    
    # Skip if already exists
    if normalized_path in path_to_item:
        return None
    
    folder_name = os.path.basename(normalized_path) or normalized_path
    item = QStandardItem(folder_name)
    
    # Find parent (only if exists, don't create)
    parent_item = find_parent_item(model, path_to_item, normalized_path)
    
    is_root = parent_item == model.invisibleRootItem()
    if is_root:
        try:
            icon = load_folder_icon_with_fallback(FOLDER_ICON_SIZE)
            item.setIcon(icon)
        except Exception:
            item.setIcon(QIcon())
    else:
        # No asignar icono para carpetas hijas
        item.setIcon(QIcon())
    
    item.setData(normalized_path, Qt.ItemDataRole.UserRole)
    item.setEditable(False)
    
    parent_item.appendRow(item)
    path_to_item[normalized_path] = item
    
    return item


def find_parent_item(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    path: str
) -> QStandardItem:
    parent_path = os.path.dirname(path)
    if not parent_path or parent_path == path:
        return model.invisibleRootItem()
    
    normalized_parent = os.path.normpath(parent_path)
    
    if normalized_parent in path_to_item:
        return path_to_item[normalized_parent]
    
    return model.invisibleRootItem()


def remove_focus_path_from_model(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    path: str
) -> None:
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


def collect_children_paths(item: QStandardItem) -> list[str]:
    children_paths = []
    for i in range(item.rowCount()):
        child = item.child(i)
        if child:
            child_path = child.data(Qt.ItemDataRole.UserRole)
            if child_path:
                children_paths.append(child_path)
                children_paths.extend(collect_children_paths(child))
    return children_paths


def _collect_expanded_recursive(
    item: QStandardItem,
    path: str,
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    tree_view: QTreeView,
    expanded_paths: list[str]
) -> None:
    """Recursively collect expanded items."""
    if item is None:
        return
    
    if path in path_to_item:
        index = model.indexFromItem(item)
        if index.isValid() and tree_view.isExpanded(index):
            expanded_paths.append(path)
    
    for i in range(item.rowCount()):
        child = item.child(i)
        if child:
            child_path = child.data(Qt.ItemDataRole.UserRole)
            if child_path:
                _collect_expanded_recursive(child, child_path, model, path_to_item, tree_view, expanded_paths)


def collect_expanded_paths(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    tree_view: QTreeView,
    root_item: QStandardItem
) -> list[str]:
    """Recursively collect all expanded node paths from root item."""
    expanded_paths = []
    
    for i in range(root_item.rowCount()):
        item = root_item.child(i)
        if item:
            item_path = item.data(Qt.ItemDataRole.UserRole)
            if item_path:
                _collect_expanded_recursive(item, item_path, model, path_to_item, tree_view, expanded_paths)
    
    return expanded_paths


def is_root_folder_item(item: QStandardItem, model: QStandardItemModel) -> bool:
    if not item:
        return False
    
    parent = item.parent()
    return parent is None or parent == model.invisibleRootItem()


def get_root_folder_items(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem]
) -> list[QStandardItem]:
    root = model.invisibleRootItem()
    root_items = []
    
    for i in range(root.rowCount()):
        item = root.child(i)
        if item and is_root_folder_item(item, model):
            root_items.append(item)
    
    return root_items


def get_root_folder_paths(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem]
) -> list[str]:
    root_items = get_root_folder_items(model, path_to_item)
    paths = []
    
    for item in root_items:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            paths.append(path)
    
    return paths


def reorder_root_folders(
    model: QStandardItemModel,
    path_to_item: dict[str, QStandardItem],
    source_path: str,
    target_path: str
) -> bool:
    normalized_source = os.path.normpath(source_path)
    normalized_target = os.path.normpath(target_path)
    
    if normalized_source not in path_to_item or normalized_target not in path_to_item:
        return False
    
    source_item = path_to_item[normalized_source]
    target_item = path_to_item[normalized_target]
    
    if not is_root_folder_item(source_item, model) or not is_root_folder_item(target_item, model):
        return False
    
    if source_item == target_item:
        return False
    
    root = model.invisibleRootItem()
    source_parent = source_item.parent()
    target_parent = target_item.parent()
    
    if (source_parent and source_parent != root) or (target_parent and target_parent != root):
        return False
    
    source_row = source_item.row()
    target_row = target_item.row()
    
    if source_row < 0 or target_row < 0:
        return False
    
    source_row_data = root.takeRow(source_row)
    adjusted_target_row = target_row if target_row < source_row else target_row - 1
    target_row_data = root.takeRow(adjusted_target_row)
    
    root.insertRow(target_row, source_row_data[0])
    root.insertRow(source_row, target_row_data[0])
    
    if not is_root_folder_item(source_row_data[0], model) or not is_root_folder_item(target_row_data[0], model):
        root.removeRow(target_row)
        root.removeRow(source_row)
        root.insertRow(source_row, source_row_data[0])
        root.insertRow(target_row, target_row_data[0])
        return False
    
    return True