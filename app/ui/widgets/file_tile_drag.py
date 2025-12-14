"""
FileTileDrag - Drag & drop handling for FileTile.

Handles drag enter, move, and drop events for folder tiles.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent

from app.services.desktop_path_helper import get_desktop_path, is_desktop_focus
from app.services.desktop_operations import is_file_in_dock, move_out_of_desktop
from app.services.file_move_service import move_file
from app.ui.widgets.drag_common import get_watcher_from_view, is_folder_inside_itself

if TYPE_CHECKING:
    from app.ui.widgets.file_tile import FileTile


def handle_drag_enter(tile: 'FileTile', event: QDragEnterEvent) -> None:
    """Handle drag enter on folder tile."""
    if not os.path.isdir(tile._file_path):
        event.ignore()
        return
    
    mime_data = event.mimeData()
    if mime_data.hasUrls():
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path and os.path.exists(file_path):
                if os.path.isdir(file_path):
                    if is_folder_inside_itself(file_path, tile._file_path):
                        event.ignore()
                        return
                event.acceptProposedAction()
                return
    event.ignore()


def handle_drag_move(tile: 'FileTile', event: QDragMoveEvent) -> None:
    """Handle drag move on folder tile."""
    if not os.path.isdir(tile._file_path):
        event.ignore()
        return
    
    mime_data = event.mimeData()
    if mime_data.hasUrls():
        event.accept()
    else:
        event.ignore()


def handle_drop(tile: 'FileTile', event: QDropEvent) -> None:
    """Handle file drop on folder tile."""
    if not os.path.isdir(tile._file_path):
        event.ignore()
        return
    
    mime_data = event.mimeData()
    if not mime_data.hasUrls():
        event.ignore()
        return
    
    moved_any = False
    for url in mime_data.urls():
        file_path = url.toLocalFile()
        if not file_path or not os.path.exists(file_path):
            continue
        
        if os.path.isdir(file_path):
            if is_folder_inside_itself(file_path, tile._file_path):
                continue
        
        watcher = _get_watcher(tile)
        file_dir = os.path.dirname(os.path.abspath(file_path))
        is_folder = os.path.isdir(file_path)
        
        # If file is from dock, always move (not copy) when dropping into folders
        if is_file_in_dock(file_path):
            result = move_file(file_path, tile._file_path, watcher=watcher)
        elif is_desktop_focus(file_dir):
            result = move_out_of_desktop(file_path, tile._file_path, watcher=watcher)
        else:
            result = move_file(file_path, tile._file_path, watcher=watcher)
        
        if result.success:
            moved_any = True
            # Calculate new path if folder was moved
            if is_folder:
                new_path = str(Path(tile._file_path) / Path(file_path).name)
                if tile._parent_view and hasattr(tile._parent_view, 'folder_moved'):
                    tile._parent_view.folder_moved.emit(file_path, new_path)
            if tile._parent_view and hasattr(tile._parent_view, 'file_deleted'):
                tile._parent_view.file_deleted.emit(file_path)
    
    if moved_any:
        event.accept()
    else:
        event.ignore()


def _get_watcher(tile: 'FileTile') -> Optional[object]:
    """Get filesystem watcher from parent view."""
    if tile._parent_view:
        return get_watcher_from_view(tile._parent_view)
    return None

