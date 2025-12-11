"""
DragCommon - Shared drag and drop utilities.

Common functions for handling file drag operations across different views.
Supports Desktop Focus (uses TrashService).
"""

import os
from typing import Optional

from app.services.desktop_path_helper import is_desktop_focus
from app.services.file_delete_service import delete_file


def is_same_folder_drop(source_path: str, tab_manager) -> bool:
    """
    Check if source file/folder is in the same folder as active target folder.

    Args:
        source_path: Path to the source file or folder.
        tab_manager: TabManager instance for checking active folder.

    Returns:
        True if source and target are in the same folder, False otherwise.
    """
    if not tab_manager:
        return False
    
    active_folder = tab_manager.get_active_folder()
    if not active_folder:
        return False

    # If source is a folder, check if it's the same as active folder
    if os.path.isdir(source_path):
        source_abs = os.path.abspath(source_path)
        active_abs = os.path.abspath(active_folder)
        return source_abs == active_abs
    
    # If source is a file, check if it's in the active folder
    source_dir = os.path.dirname(os.path.abspath(source_path))
    active_dir = os.path.abspath(active_folder)
    
    return source_dir == active_dir


def check_files_after_drag(
    original_file_paths: list[str],
    original_dir: str,
    emit_file_deleted,
    watcher: Optional[object] = None,
    tab_manager: Optional[object] = None
) -> None:
    """
    Check file status after drag and emit signals for moved/deleted files.
    
    Args:
        original_file_paths: List of file paths that were dragged.
        original_dir: Original directory where files were located.
        emit_file_deleted: Callback function to emit file_deleted signal.
        watcher: Optional watcher to block events during delete.
    """
    for file_path in original_file_paths:
        if os.path.exists(file_path):
            current_dir = os.path.dirname(os.path.abspath(file_path))
            if current_dir == original_dir:
                _delete_if_dragged_out(file_path, emit_file_deleted, watcher, tab_manager)
            else:
                emit_file_deleted(file_path)
        else:
            emit_file_deleted(file_path)


def _delete_if_dragged_out(
    file_path: str,
    emit_file_deleted,
    watcher: Optional[object] = None,
    tab_manager: Optional[object] = None
) -> None:
    """Delete file if it was dragged outside (still in same directory)."""
    # Check if file is on Desktop Focus - use TrashService
    file_dir = os.path.dirname(os.path.abspath(file_path))
    is_desktop = is_desktop_focus(file_dir)
    
    result = delete_file(file_path, watcher=watcher, is_trash_focus=False)
    if result.success:
        emit_file_deleted(file_path)

