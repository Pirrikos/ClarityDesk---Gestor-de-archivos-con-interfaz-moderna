"""
FileDeletionService - Service for moving files to Windows recycle bin.

Pure service without UI, dialogs, or QMessageBox.
Handles moving files and folders to Windows recycle bin using Shell API.
"""

import os
from pathlib import Path
from typing import Optional

from app.core.logger import get_logger
from app.models.file_operation_result import FileOperationResult
from app.services.file_path_utils import validate_path
from app.services.windows_recycle_bin_utils import (
    prepare_file_path_for_recycle_bin,
    move_to_recycle_bin_via_api
)

logger = get_logger(__name__)


def move_to_windows_recycle_bin(file_path: str) -> FileOperationResult:
    """
    Move file or folder to Windows recycle bin using Shell API.
    
    Pure service method - no UI, no dialogs, no QMessageBox.
    
    Args:
        file_path: Path to file or folder to move to recycle bin.
        
    Returns:
        FileOperationResult with success status and error message if failed.
    """
    if not validate_path(file_path):
        return FileOperationResult.error(f"El archivo o carpeta no existe: {file_path}")
    
    try:
        abs_path = os.path.abspath(file_path)
        file_path_unicode = prepare_file_path_for_recycle_bin(abs_path)
        result_code, was_aborted = move_to_recycle_bin_via_api(file_path_unicode)
        
        if result_code == 0 and not was_aborted:
            logger.info(f"Archivo movido a papelera: {file_path}")
            return FileOperationResult.ok()
        else:
            error_msg = f"No se pudo mover a la papelera: código de error {result_code}"
            logger.error(f"{error_msg} - {file_path}")
            return FileOperationResult.error(error_msg)
    except PermissionError as e:
        logger.error(f"Sin permisos para mover a papelera {file_path}: {e}")
        return FileOperationResult.error(f"No tienes permisos para mover este archivo a la papelera.")
    except OSError as e:
        logger.error(f"Error del sistema al mover a papelera {file_path}: {e}")
        return FileOperationResult.error(f"Error al mover a la papelera: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al mover a papelera {file_path}: {e}", exc_info=True)
        return FileOperationResult.error(f"Error inesperado: {str(e)}")


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

