"""
FileDeleteService - File deletion operations.

Handles safe file deletion using Windows recycle bin or TrashService.
Supports Desktop Focus (uses TrashService) and Trash Focus (permanent delete).
"""

import os
from typing import Optional
from ctypes import windll, wintypes

from app.models.file_operation_result import FileOperationResult
from app.services.desktop_path_helper import is_desktop_focus
from app.services.file_path_utils import validate_file, validate_path
from app.services.trash_operations import delete_permanently, move_to_trash
from app.services.trash_storage import TRASH_FOCUS_PATH


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
            return FileOperationResult.ok()
        else:
            # Fallback to regular delete if recycle bin fails
            os.remove(file_path)
            return FileOperationResult.ok()
    except (OSError, PermissionError) as e:
        return FileOperationResult.error(f"Failed to delete file: {str(e)}")


def _send_to_recycle_bin(file_path: str) -> bool:
    """Send a file to Windows recycle bin using Shell API."""
    try:
        abs_path = os.path.abspath(file_path)
        file_path_unicode = _prepare_file_path_for_recycle_bin(abs_path)
        fileop = _create_fileop_structure(file_path_unicode)
        
        shell32 = windll.shell32
        result = shell32.SHFileOperationW(wintypes.byref(fileop))
        return result == 0 and not fileop.fAnyOperationsAborted
    except Exception:
        return False


def _prepare_file_path_for_recycle_bin(abs_path: str) -> str:
    """Prepare file path with double-null termination for Windows API."""
    return abs_path.replace('/', '\\') + '\0\0'


def _create_fileop_structure(file_path_unicode: str):
    """Create and configure SHFILEOPSTRUCTW structure for recycle bin operation."""
    FO_DELETE = 0x0003
    FOF_ALLOWUNDO = 0x0040
    FOF_SILENT = 0x0004
    FOF_NOCONFIRMATION = 0x0010
    
    class SHFILEOPSTRUCTW(wintypes.Structure):
        _fields_ = [
            ("hWnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", wintypes.WORD),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", wintypes.LPVOID),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]
    
    fileop = SHFILEOPSTRUCTW()
    fileop.hWnd = None
    fileop.wFunc = FO_DELETE
    fileop.pFrom = file_path_unicode
    fileop.pTo = None
    fileop.fFlags = FOF_ALLOWUNDO | FOF_SILENT | FOF_NOCONFIRMATION
    fileop.fAnyOperationsAborted = wintypes.BOOL(False)
    fileop.hNameMappings = None
    fileop.lpszProgressTitle = None
    return fileop

