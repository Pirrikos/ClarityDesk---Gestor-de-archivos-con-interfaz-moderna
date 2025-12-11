"""
DesktopDragOps - Desktop drag and drop operations.

Handles file copy, move, and rename operations on Windows Desktop.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from app.models.file_operation_result import FileOperationResult
from app.services.desktop_path_helper import get_desktop_path
from app.services.tab_path_normalizer import normalize_path
from app.services.file_path_utils import resolve_conflict, validate_path
from app.services.desktop_operations_scan import _get_dock_storage_path


def _block_watcher_events(watcher: Optional[object], block: bool) -> None:
    """Block or unblock watcher events."""
    if watcher and hasattr(watcher, 'ignore_events'):
        watcher.ignore_events(block)


def _execute_with_watcher_block(watcher: Optional[object], operation) -> FileOperationResult:
    """Execute operation with watcher events blocked."""
    _block_watcher_events(watcher, True)
    try:
        return operation()
    finally:
        _block_watcher_events(watcher, False)


def copy_into_dock(
    file_path: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Copy file into dock storage folder.
    
    Files are copied (not moved) so originals remain on desktop.
    
    Args:
        file_path: Source file path to copy.
        watcher: Optional watcher to block events during copy.
        
    Returns:
        FileOperationResult with success status.
    """
    if not validate_path(file_path):
        return FileOperationResult.error(f"Source path does not exist: {file_path}")
    
    dock_storage = _get_dock_storage_path()
    if not dock_storage.exists():
        dock_storage.mkdir(parents=True, exist_ok=True)
    
    source_path = Path(file_path)
    dest_path = dock_storage / source_path.name
    dest_path = resolve_conflict(dest_path)
    
    def _do_copy():
        if os.path.isdir(file_path):
            shutil.copytree(str(source_path), str(dest_path), dirs_exist_ok=True)
        else:
            shutil.copy2(str(source_path), str(dest_path))
        return FileOperationResult.ok()
    
    try:
        return _execute_with_watcher_block(watcher, _do_copy)
    except (OSError, shutil.Error, PermissionError) as e:
        return FileOperationResult.error(f"Failed to copy to dock: {str(e)}")


def move_into_desktop(
    file_path: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Move file into Desktop folder.
    
    Args:
        file_path: Source file path to move.
        watcher: Optional watcher to block events during move.
        
    Returns:
        FileOperationResult with success status.
    """
    if not validate_path(file_path):
        return FileOperationResult.error(f"Source path does not exist: {file_path}")
    
    desktop_path = get_desktop_path()
    if not os.path.isdir(desktop_path):
        return FileOperationResult.error(f"Desktop folder does not exist: {desktop_path}")
    
    source_path = Path(file_path)
    dest_path = Path(desktop_path) / source_path.name
    dest_path = resolve_conflict(dest_path)
    
    def _do_move():
        shutil.move(str(source_path), str(dest_path))
        return FileOperationResult.ok()
    
    try:
        return _execute_with_watcher_block(watcher, _do_move)
    except (OSError, shutil.Error, PermissionError) as e:
        return FileOperationResult.error(f"Failed to move to Desktop: {str(e)}")


def move_out_of_desktop(
    file_path: str,
    target_dir: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Move file out of Desktop to target directory.
    
    Args:
        file_path: File path on Desktop to move.
        target_dir: Target directory path.
        watcher: Optional watcher to block events during move.
        
    Returns:
        FileOperationResult with success status.
    """
    if not validate_path(file_path):
        return FileOperationResult.error(f"Source file does not exist: {file_path}")
    
    if not os.path.isdir(target_dir):
        return FileOperationResult.error(f"Target directory does not exist: {target_dir}")
    
    desktop_path = normalize_path(get_desktop_path())
    file_dir = normalize_path(os.path.dirname(file_path))
    
    if file_dir != desktop_path:
        return FileOperationResult.error("File is not on Desktop")
    
    source_path = Path(file_path)
    dest_path = Path(target_dir) / source_path.name
    dest_path = resolve_conflict(dest_path)
    
    def _do_move():
        shutil.move(str(source_path), str(dest_path))
        return FileOperationResult.ok()
    
    try:
        return _execute_with_watcher_block(watcher, _do_move)
    except (OSError, shutil.Error, PermissionError) as e:
        return FileOperationResult.error(f"Failed to move from Desktop: {str(e)}")


def rename_desktop_file(
    file_path: str,
    new_name: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Rename file on Desktop.
    
    Args:
        file_path: Current file path on Desktop.
        new_name: New filename (without path).
        watcher: Optional watcher to block events during rename.
        
    Returns:
        FileOperationResult with success status.
    """
    if not validate_path(file_path):
        return FileOperationResult.error(f"File does not exist: {file_path}")
    
    desktop_path = normalize_path(get_desktop_path())
    file_dir = normalize_path(os.path.dirname(file_path))
    
    if file_dir != desktop_path:
        return FileOperationResult.error("File is not on Desktop")
    
    if not new_name or not new_name.strip():
        return FileOperationResult.error("New name cannot be empty")
    
    new_name = os.path.basename(new_name.strip())
    if not new_name:
        return FileOperationResult.error("Invalid new name")
    
    source_path = Path(file_path)
    dest_path = source_path.parent / new_name
    
    if source_path == dest_path:
        return FileOperationResult.ok()
    
    dest_path = resolve_conflict(dest_path)
    
    def _do_rename():
        source_path.rename(dest_path)
        return FileOperationResult.ok()
    
    try:
        return _execute_with_watcher_block(watcher, _do_rename)
    except (OSError, PermissionError) as e:
        return FileOperationResult.error(f"Failed to rename Desktop file: {str(e)}")

