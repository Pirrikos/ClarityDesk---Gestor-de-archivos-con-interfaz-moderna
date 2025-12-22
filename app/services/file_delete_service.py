"""
FileDeleteService - File deletion operations.

Handles safe file deletion using Windows recycle bin or TrashService.
Supports Desktop Focus (uses TrashService) and Trash Focus (permanent delete).
"""

import os
from typing import Optional

from app.core.logger import get_logger
from app.models.file_operation_result import FileOperationResult
from app.services.desktop_path_helper import is_desktop_focus
from app.services.file_path_utils import validate_file, validate_path
from app.services.trash_operations import delete_permanently, move_to_trash
from app.services.trash_storage import TRASH_FOCUS_PATH
from app.services.windows_recycle_bin_utils import (
    prepare_file_path_for_recycle_bin,
    move_to_recycle_bin_via_api
)

logger = get_logger(__name__)


def delete_file(
    file_path: str,
    watcher: Optional[object] = None,
    is_trash_focus: bool = False
) -> FileOperationResult:
    """
    Delete a file safely.
    
    - Desktop Focus: Uses TrashService (internal paperera)
    - Trash Focus: Uses TrashService.delete_permanently() (requires confirmation)
    - Normal folders: Uses Windows recycle bin

    Args:
        file_path: Full path to the file to delete.
        watcher: Optional watcher to block events during delete.
        is_trash_focus: True if deleting from Trash Focus (permanent delete).

    Returns:
        FileOperationResult with success status and error message if failed.
    """
    if not validate_path(file_path):
        return FileOperationResult.error(f"File does not exist: {file_path}")
    
    # Handle Trash Focus - permanent delete
    if is_trash_focus:
        return delete_permanently(file_path, watcher=watcher)
    
    # Handle Desktop Focus - use TrashService
    file_dir = os.path.dirname(os.path.abspath(file_path))
    if is_desktop_focus(file_dir):
        return move_to_trash(file_path, watcher=watcher)
    
    # Normal folder - use Windows recycle bin
    try:
        # Use Windows Shell API to send file to recycle bin
        # SHFileOperationW with FO_DELETE and FOF_ALLOWUNDO
        result = _send_to_recycle_bin(file_path)
        if result:
            logger.info(f"Deleted file to recycle bin: {file_path}")
            return FileOperationResult.ok()
        else:
            # Fallback to regular delete if recycle bin fails
            logger.warning(f"Recycle bin failed, using regular delete: {file_path}")
            os.remove(file_path)
            logger.info(f"Deleted file permanently: {file_path}")
            return FileOperationResult.ok()
    except PermissionError as e:
        logger.error(f"Permission denied deleting {file_path}: {e}")
        return FileOperationResult.error(f"Failed to delete file: {str(e)}")
    except OSError as e:
        logger.error(f"OS error deleting {file_path}: {e}")
        return FileOperationResult.error(f"Failed to delete file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error deleting {file_path}: {e}", exc_info=True)
        return FileOperationResult.error(f"Failed to delete file: {str(e)}")


def _send_to_recycle_bin(file_path: str) -> bool:
    """Send a file to Windows recycle bin using Shell API."""
    try:
        abs_path = os.path.abspath(file_path)
        file_path_unicode = prepare_file_path_for_recycle_bin(abs_path)
        result_code, was_aborted = move_to_recycle_bin_via_api(file_path_unicode)
        return result_code == 0 and not was_aborted
    except Exception:
        return False

