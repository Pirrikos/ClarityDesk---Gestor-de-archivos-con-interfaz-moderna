"""
FileDeletionService - Utility for checking folder emptiness.

Provides utility function for checking if folders are empty.
File deletion operations are handled by file_delete_service.py.
"""

from pathlib import Path

from app.services.file_path_utils import validate_path


def is_folder_empty(folder_path: str) -> bool:
    """
    Check if a folder is empty (has no files or subfolders).
    
    Args:
        folder_path: Path to folder to check.
        
    Returns:
        True if folder is empty, False if it has content or if path is invalid.
    """
    if not validate_path(folder_path):
        return False
    
    try:
        path = Path(folder_path)
        if not path.is_dir():
            return False
        
        # Usar iterdir() para verificar si hay contenido
        # next() con default evita cargar toda la lista en memoria
        return next(path.iterdir(), None) is None
    except (OSError, PermissionError):
        return False

