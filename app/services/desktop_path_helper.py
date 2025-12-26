"""
DesktopPathHelper - Desktop path detection and normalization.

Helper functions for detecting Desktop Focus and normalizing paths.
"""

import os

from app.services.path_utils import normalize_path


DESKTOP_FOCUS_PATH = "__CLARITY_DESKTOP__"

_desktop_path_cache: str | None = None


def get_desktop_path() -> str:
    """
    Get Windows Desktop folder path.
    
    Returns:
        Desktop folder path as string.
    """
    global _desktop_path_cache
    
    if _desktop_path_cache is not None:
        return _desktop_path_cache
    
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        desktop_path = winreg.QueryValueEx(key, "Desktop")[0]
        winreg.CloseKey(key)
        _desktop_path_cache = desktop_path
        return desktop_path
    except Exception:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        _desktop_path_cache = desktop_path
        return desktop_path


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

