"""
FileScanService - File scanning operations.

Handles reading files from filesystem, Desktop Focus, and Trash Focus.
"""

import os

from app.services.desktop_path_helper import is_desktop_focus
from app.services.desktop_operations import load_desktop_files
from app.services.file_path_utils import validate_folder
from app.services.trash_storage import TRASH_FOCUS_PATH, list_trash_files


def scan_folder_files(folder_path: str) -> list[str]:
    """
    Scan files from a normal folder (not Desktop or Trash).
    
    Args:
        folder_path: Path to folder to scan.
        
    Returns:
        List of file and folder paths.
    """
    if not validate_folder(folder_path):
        return []
    
    files = []
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path) or os.path.isfile(item_path):
                files.append(item_path)
    except (OSError, PermissionError):
        return []
    
    return files


def scan_desktop_files() -> list[str]:
    """
    Scan files from Desktop Focus.
    
    Returns:
        List of file paths from Desktop.
    """
    return load_desktop_files()


def scan_trash_files() -> list[str]:
    """
    Scan files from Trash Focus.
    
    Returns:
        List of file paths from Trash.
    """
    return list_trash_files()


def scan_files(folder_path: str) -> list[str]:
    """
    Scan files from folder, Desktop Focus, or Trash Focus.
    
    Args:
        folder_path: Path to folder or virtual path (Desktop/Trash).
        
    Returns:
        List of file paths.
    """
    if not folder_path:
        return []
    
    if is_desktop_focus(folder_path):
        return scan_desktop_files()
    elif folder_path == TRASH_FOCUS_PATH:
        return scan_trash_files()
    else:
        return scan_folder_files(folder_path)

