"""
FileMoveService - File move operations.

Handles moving files between folders with conflict resolution.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from app.models.file_operation_result import FileOperationResult
from app.services.file_path_utils import resolve_conflict, validate_file, validate_folder, validate_path


def move_file(
    source: str,
    destination_folder: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Move a file or folder from source to destination folder.

    Args:
        source: Full path to source file or folder.
        destination_folder: Destination folder path.

    Returns:
        FileOperationResult with success status and error message if failed.
    """
    if not validate_path(source):
        return FileOperationResult.error(f"Source path does not exist: {source}")

    if not validate_folder(destination_folder):
        return FileOperationResult.error(f"Destination folder does not exist: {destination_folder}")

    source_path = Path(source)
    dest_path = Path(destination_folder) / source_path.name

    # Handle destination conflict by appending number
    dest_path = resolve_conflict(dest_path)

    # Block watcher events during move operation
    if watcher and hasattr(watcher, 'ignore_events'):
        watcher.ignore_events(True)
    
    try:
        shutil.move(str(source_path), str(dest_path))
        result = FileOperationResult.ok()
    except (OSError, shutil.Error, PermissionError) as e:
        result = FileOperationResult.error(f"Failed to move: {str(e)}")
    finally:
        # Unblock watcher events
        if watcher and hasattr(watcher, 'ignore_events'):
            watcher.ignore_events(False)
    
    return result


def copy_file(
    source: str,
    destination_folder: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Copy a file to destination folder (used for email/attach operations).

    Args:
        source: Full path to source file.
        destination_folder: Destination folder path.

    Returns:
        FileOperationResult with success status and error message if failed.
    """
    if not validate_file(source):
        return FileOperationResult.error(f"Source file does not exist: {source}")

    if not validate_folder(destination_folder):
        return FileOperationResult.error(f"Destination folder does not exist: {destination_folder}")

    source_path = Path(source)
    dest_path = Path(destination_folder) / source_path.name

    # Handle destination conflict by appending number
    dest_path = resolve_conflict(dest_path)

    # Block watcher events during copy operation
    if watcher and hasattr(watcher, 'ignore_events'):
        watcher.ignore_events(True)
    
    try:
        shutil.copy2(str(source_path), str(dest_path))
        result = FileOperationResult.ok()
    except (OSError, shutil.Error, PermissionError) as e:
        result = FileOperationResult.error(f"Failed to copy file: {str(e)}")
    finally:
        # Unblock watcher events
        if watcher and hasattr(watcher, 'ignore_events'):
            watcher.ignore_events(False)
    
    return result

