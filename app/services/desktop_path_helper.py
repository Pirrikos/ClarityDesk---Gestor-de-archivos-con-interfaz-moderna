"""
DesktopPathHelper - Desktop path detection and normalization.

Helper functions for detecting Desktop Focus and normalizing paths.
"""

import os

from app.services.path_utils import normalize_path


# Virtual path identifier for Desktop Focus
DESKTOP_FOCUS_PATH = "__CLARITY_DESKTOP__"


def get_desktop_path() -> str:
    """
    Get Windows Desktop folder path.
    
    Returns:
        Desktop folder path as string.
    """
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        desktop_path = winreg.QueryValueEx(key, "Desktop")[0]
        winreg.CloseKey(key)
        return desktop_path
    except Exception:
        return os.path.join(os.path.expanduser("~"), "Desktop")


def is_desktop_focus(path: str) -> bool:
    """
    Check if path is Desktop Focus (real Desktop or virtual identifier).
    
    Args:
        path: Path to check.
        
    Returns:
        True if Desktop Focus, False otherwise.
    """
    if not path:
        return False
    
    if path == DESKTOP_FOCUS_PATH:
        return True
    
    normalized_path = normalize_path(path)
    desktop_path = normalize_path(get_desktop_path())
    
    # Check if it's the desktop folder itself
    if normalized_path == desktop_path:
        return True
    
    return False

