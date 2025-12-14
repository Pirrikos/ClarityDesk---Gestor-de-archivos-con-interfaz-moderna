"""
FileRenameService - File rename operations.

Handles renaming files with conflict resolution.
Supports Desktop Focus (uses DesktopRealService).
"""

import os
from pathlib import Path
from typing import Optional

from app.core.logger import get_logger
from app.models.file_operation_result import FileOperationResult
from app.services.desktop_path_helper import is_desktop_focus
from app.services.desktop_operations import rename_desktop_file
from app.services.file_path_utils import resolve_conflict, validate_file

logger = get_logger(__name__)


def rename_file(
    file_path: str,
    new_name: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Rename a file safely, handling conflicts.
    Supports Desktop Focus (uses DesktopRealService).

    Args:
        file_path: Full path to the file to rename.
        new_name: New filename (without path).
        watcher: Optional watcher to block events during rename.

    Returns:
        FileOperationResult with success status and error message if failed.
    """
    if not validate_file(file_path):
        return FileOperationResult.error(f"File does not exist: {file_path}")

    if not new_name or not new_name.strip():
        return FileOperationResult.error("New name cannot be empty")

    # Sanitize new name to prevent path traversal
    new_name = os.path.basename(new_name.strip())
    if not new_name:
        return FileOperationResult.error("Invalid new name")
    
    # Handle Desktop Focus specially
    file_dir = os.path.dirname(os.path.abspath(file_path))
    if is_desktop_focus(file_dir):
        return rename_desktop_file(file_path, new_name, watcher=watcher)

    source_path = Path(file_path)
    dest_path = source_path.parent / new_name

    # If same name, no-op
    if source_path == dest_path:
        return FileOperationResult.ok()

    # Handle conflict by appending number
    dest_path = resolve_conflict(dest_path)

    # Block watcher events during rename
    if watcher and hasattr(watcher, 'ignore_events'):
        watcher.ignore_events(True)

    try:
        source_path.rename(dest_path)
        logger.info(f"Renamed file: {file_path} -> {dest_path}")
        result = FileOperationResult.ok()
    except PermissionError as e:
        logger.error(f"Permission denied renaming {file_path} to {new_name}: {e}")
        result = FileOperationResult.error(f"Failed to rename file: {str(e)}")
    except OSError as e:
        logger.error(f"OS error renaming {file_path} to {new_name}: {e}")
        result = FileOperationResult.error(f"Failed to rename file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error renaming {file_path} to {new_name}: {e}", exc_info=True)
        result = FileOperationResult.error(f"Failed to rename file: {str(e)}")
    finally:
        if watcher and hasattr(watcher, 'ignore_events'):
            watcher.ignore_events(False)
    
    return result

