"""
TrashOperations - Trash file operations.

Handles moving files to trash, restoring, and permanent deletion.
Only service authorized to delete files permanently.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models.file_operation_result import FileOperationResult
from app.services.desktop_path_helper import get_desktop_path
from app.services.file_path_utils import resolve_conflict, validate_path
from app.services.trash_storage import (
    get_trash_path,
    load_trash_metadata,
    save_trash_metadata,
)


def move_to_trash(
    file_path: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Move file to trash (internal paperera).
    
    Args:
        file_path: Path to file to move to trash.
        watcher: Optional watcher to block events during move.
        
    Returns:
        FileOperationResult with success status.
    """
    if not validate_path(file_path):
        return FileOperationResult.error(f"File does not exist: {file_path}")
    
    trash_dir = get_trash_path()
    source_path = Path(file_path)
    dest_path = trash_dir / source_path.name
    dest_path = resolve_conflict(dest_path)
    
    metadata = load_trash_metadata()
    filename = dest_path.name
    metadata[filename] = {
        "original_path": str(source_path),
        "deleted_date": datetime.now().isoformat()
    }
    save_trash_metadata(metadata)
    
    if watcher and hasattr(watcher, 'ignore_events'):
        watcher.ignore_events(True)
    
    try:
        shutil.move(str(source_path), str(dest_path))
        result = FileOperationResult.ok()
    except (OSError, shutil.Error, PermissionError) as e:
        metadata.pop(filename, None)
        save_trash_metadata(metadata)
        result = FileOperationResult.error(f"Failed to move to trash: {str(e)}")
    finally:
        if watcher and hasattr(watcher, 'ignore_events'):
            watcher.ignore_events(False)
    
    return result


def restore_from_trash(
    trash_file_path: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Restore file from trash to original location.
    
    If original location doesn't exist, restores to Desktop.
    
    Args:
        trash_file_path: Path to file in trash folder.
        watcher: Optional watcher to block events during restore.
        
    Returns:
        FileOperationResult with success status.
    """
    if not validate_path(trash_file_path):
        return FileOperationResult.error(f"Trash file does not exist: {trash_file_path}")
    
    metadata = load_trash_metadata()
    filename = os.path.basename(trash_file_path)
    file_metadata = metadata.get(filename)
    
    if not file_metadata:
        return FileOperationResult.error("Metadata not found for trash file")
    
    original_path = file_metadata.get("original_path")
    if not original_path:
        return FileOperationResult.error("Original path not found in metadata")
    
    original_dir = os.path.dirname(original_path)
    if not os.path.isdir(original_dir):
        original_dir = get_desktop_path()
        original_path = os.path.join(original_dir, os.path.basename(original_path))
    
    source_path = Path(trash_file_path)
    dest_path = Path(original_path)
    dest_path = resolve_conflict(dest_path)
    
    if watcher and hasattr(watcher, 'ignore_events'):
        watcher.ignore_events(True)
    
    try:
        shutil.move(str(source_path), str(dest_path))
        metadata.pop(filename, None)
        save_trash_metadata(metadata)
        result = FileOperationResult.ok()
    except (OSError, shutil.Error, PermissionError) as e:
        result = FileOperationResult.error(f"Failed to restore from trash: {str(e)}")
    finally:
        if watcher and hasattr(watcher, 'ignore_events'):
            watcher.ignore_events(False)
    
    return result


def delete_permanently(
    trash_file_path: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Permanently delete file from trash (irreversible).
    
    Args:
        trash_file_path: Path to file in trash folder.
        watcher: Optional watcher to block events during delete.
        
    Returns:
        FileOperationResult with success status.
    """
    if not validate_path(trash_file_path):
        return FileOperationResult.error(f"Trash file does not exist: {trash_file_path}")
    
    metadata = load_trash_metadata()
    filename = os.path.basename(trash_file_path)
    
    if watcher and hasattr(watcher, 'ignore_events'):
        watcher.ignore_events(True)
    
    try:
        file_path = Path(trash_file_path)
        if file_path.is_dir():
            shutil.rmtree(str(file_path))
        else:
            os.remove(str(file_path))
        
        metadata.pop(filename, None)
        save_trash_metadata(metadata)
        result = FileOperationResult.ok()
    except (OSError, PermissionError) as e:
        result = FileOperationResult.error(f"Failed to delete permanently: {str(e)}")
    finally:
        if watcher and hasattr(watcher, 'ignore_events'):
            watcher.ignore_events(False)
    
    return result

