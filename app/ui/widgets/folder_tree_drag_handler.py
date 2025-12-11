"""
FolderTreeDragHandler - Drag and drop handler for FolderTreeSidebar.

Handles drag and drop operations on tree nodes.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QTreeView

from app.services.file_move_service import move_file


def handle_drag_enter(event) -> None:
    """Handle drag enter on tree view."""
    mime_data = event.mimeData()
    if mime_data.hasUrls():
        # Check if at least one valid file/folder
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path and os.path.exists(file_path):
                event.acceptProposedAction()
                return
    event.ignore()


def handle_drag_move(event, tree_view: QTreeView, model: QStandardItemModel) -> None:
    """Handle drag move over tree view."""
    # Convert widget coordinates to tree view coordinates
    tree_pos = tree_view.mapFromParent(event.pos())
    index = tree_view.indexAt(tree_pos)
    if not index.isValid():
        event.ignore()
        return
    
    item = model.itemFromIndex(index)
    if not item:
        event.ignore()
        return
    
    target_path = item.data(Qt.ItemDataRole.UserRole)
    if not target_path or not os.path.isdir(target_path):
        event.ignore()
        return
    
    mime_data = event.mimeData()
    if mime_data.hasUrls():
        # Validate that we're not dropping into source folder
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path and os.path.exists(file_path):
                if os.path.isdir(file_path):
                    source_abs = os.path.abspath(file_path)
                    target_abs = os.path.abspath(target_path)
                    if source_abs == target_abs or source_abs.startswith(target_abs + os.sep):
                        event.ignore()
                        return
        event.accept()
    else:
        event.ignore()


def handle_drop(event, tree_view: QTreeView, model: QStandardItemModel, watcher=None) -> list[str]:
    """
    Handle file drop on tree node - move files to target folder.
    
    Args:
        event: Drop event.
        tree_view: QTreeView instance.
        model: QStandardItemModel instance.
        watcher: Optional FileSystemWatcherService to block events during move.
        
    Returns:
        List of successfully moved file paths, empty if none moved.
    """
    target_path = get_drop_target_path(event, tree_view, model)
    if not target_path:
        return []
    
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        return []
    
    return _process_dropped_files(mime_data, target_path, watcher)


def get_drop_target_path(event, tree_view: QTreeView, model: QStandardItemModel) -> str:
    """Get target folder path from drop event (public for reuse)."""
    """Get target folder path from drop event."""
    tree_pos = tree_view.mapFromParent(event.pos())
    index = tree_view.indexAt(tree_pos)
    if not index.isValid():
        return None
    
    item = model.itemFromIndex(index)
    if not item:
        return None
    
    target_path = item.data(Qt.ItemDataRole.UserRole)
    if not target_path or not os.path.isdir(target_path):
        return None
    
    return target_path


def _process_dropped_files(mime_data, target_path: str, watcher=None) -> list[str]:
    """
    Process dropped files and return list of successfully moved paths.
    
    Args:
        mime_data: MimeData from drop event.
        target_path: Target folder path.
        watcher: Optional FileSystemWatcherService to block events during move.
        
    Returns:
        List of successfully moved file paths.
    """
    moved_paths = []
    
    for url in mime_data.urls():
        file_path = url.toLocalFile()
        if not file_path or not os.path.exists(file_path):
            continue
        
        # Skip if trying to move folder into itself
        if os.path.isdir(file_path):
            source_abs = os.path.abspath(file_path)
            target_abs = os.path.abspath(target_path)
            if source_abs == target_abs or source_abs.startswith(target_abs + os.sep):
                continue
        
        # Check if file is from Desktop Focus
        from app.services.desktop_path_helper import is_desktop_focus
        from app.services.desktop_operations import move_out_of_desktop
        file_dir = os.path.dirname(os.path.abspath(file_path))
        if is_desktop_focus(file_dir):
            result = move_out_of_desktop(file_path, target_path, watcher=watcher)
        else:
            result = move_file(file_path, target_path, watcher=watcher)
        if result.success:
            moved_paths.append(file_path)
    
    return moved_paths

