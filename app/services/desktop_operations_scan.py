"""
DesktopOperationsScan - Desktop file scanning operations.

Handles loading files from Windows Desktop and dock storage detection.
"""

import os
from pathlib import Path

from app.services.desktop_path_helper import get_desktop_path, get_clarity_folder_path
from app.services.desktop_visibility import is_system_file, is_hidden_file
from app.services.path_utils import normalize_path


def _get_dock_storage_path() -> Path:
    """Get path to dock files storage folder (legacy - deprecated)."""
    dock_dir = Path(__file__).parent.parent.parent / "storage" / "dock_files"
    dock_dir.mkdir(parents=True, exist_ok=True)
    return dock_dir


def is_file_in_dock(file_path: str) -> bool:
    """
    Check if file is in dock storage folder (Clarity folder).
    
    CRÍTICO: Ahora los archivos del dock están en Escritorio/Clarity/
    no en storage/dock_files.
    
    Args:
        file_path: Path to check.
        
    Returns:
        True if file is in Clarity folder (dock storage), False otherwise.
    """
    try:
        # Verificar si está en Clarity (nuevo almacenamiento del dock)
        clarity_path = normalize_path(get_clarity_folder_path())
        file_abs = normalize_path(os.path.abspath(file_path))
        clarity_abs = normalize_path(os.path.abspath(clarity_path))
        
        # Verificar si el archivo está dentro de Clarity
        if file_abs.startswith(clarity_abs + os.sep) or file_abs == clarity_abs:
            return True
        
        # Verificar legacy storage (por compatibilidad)
        dock_storage = _get_dock_storage_path()
        dock_abs = normalize_path(os.path.abspath(str(dock_storage)))
        if file_abs.startswith(dock_abs + os.sep) or file_abs == dock_abs:
            return True
        
        return False
    except Exception:
        return False


def load_desktop_files(include_hidden: bool = True) -> list[str]:
    """
    Load files from Windows Desktop folder.
    
    Returns all files and folders from the actual Windows Desktop,
    not from dock storage. This allows Desktop Focus to show all
    desktop files, not just those copied to dock storage.
    
    Args:
        include_hidden: If False, skip hidden files (default: True).
    
    Returns:
        List of file paths from Windows Desktop folder.
    """
    files = []
    try:
        desktop_path = get_desktop_path()
        
        if not os.path.isdir(desktop_path):
            return []
        
        for item in os.listdir(desktop_path):
            if is_system_file(item):
                continue
            
            item_path = os.path.join(desktop_path, item)
            
            if not include_hidden and is_hidden_file(item_path):
                continue
            
            if os.path.isfile(item_path) or os.path.isdir(item_path):
                files.append(item_path)
    except (OSError, PermissionError):
        return []
    
    return sorted(files)

