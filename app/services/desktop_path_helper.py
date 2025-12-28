"""
DesktopPathHelper - Desktop path detection and normalization.

Helper functions for detecting Desktop Focus and normalizing paths.
"""

import os
from pathlib import Path

from app.services.path_utils import normalize_path


DESKTOP_FOCUS_PATH = "__CLARITY_DESKTOP__"

_desktop_path_cache: str | None = None
_clarity_path_cache: str | None = None


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
    except (OSError, PermissionError, FileNotFoundError):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        _desktop_path_cache = desktop_path
        return desktop_path


def get_clarity_folder_path() -> str:
    """
    Get Clarity folder path in Desktop.
    
    Creates folder if it doesn't exist.
    Uses cache to avoid repeated path calculations.
    
    Returns:
        Path to Clarity folder as string.
    """
    global _clarity_path_cache
    
    if _clarity_path_cache is not None:
        return _clarity_path_cache
    
    desktop_path = get_desktop_path()
    clarity_path = os.path.join(desktop_path, "Clarity")
    
    # Validate desktop exists and is accessible before creating
    if os.path.isdir(desktop_path):
        try:
            Path(clarity_path).mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            # Silently fail - return path anyway
            pass
    
    _clarity_path_cache = clarity_path
    return clarity_path


def is_desktop_focus(path: str) -> bool:
    """
    Check if path is Desktop Focus (real Desktop, Clarity folder, or virtual identifier).
    
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
    
    # Check if it's the Clarity folder (dock storage)
    clarity_path = normalize_path(get_clarity_folder_path())
    if normalized_path == clarity_path:
        return True
    
    return False


def is_system_desktop(path: str) -> bool:
    """
    Verificar si una ruta es el Escritorio del sistema.
    
    Detecta el Escritorio del sistema independientemente de:
    - Idioma del sistema (Desktop/Escritorio)
    - Mayúsculas/minúsculas
    - Separadores de ruta
    """
    if not path:
        return False
    
    # Resolver path real (sigue symlinks, normaliza)
    try:
        resolved_path = Path(path).resolve()
        normalized_path = normalize_path(str(resolved_path))
    except (OSError, ValueError):
        # Si no se puede resolver, usar path original normalizado
        normalized_path = normalize_path(path)
    
    # Obtener ruta del Escritorio normalizada
    desktop_path = normalize_path(get_desktop_path())
    
    # Verificar si es exactamente el Escritorio
    if normalized_path == desktop_path:
        return True
    
    return False
