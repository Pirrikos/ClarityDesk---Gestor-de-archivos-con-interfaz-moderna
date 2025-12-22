"""
FolderCreationService - Service for creating folders in the filesystem.

Handles folder creation with validation and error handling.
Pure functions - no state, no class instantiation needed.
"""

import re
from pathlib import Path
from typing import Optional

from app.core.logger import get_logger
from app.models.file_operation_result import FileOperationResult
from app.services.file_path_utils import validate_parent_path_for_creation

logger = get_logger(__name__)

# Caracteres inválidos en nombres de carpeta en Windows
INVALID_CHARS = r'[<>:"|?*\\/]'


def validate_folder_name(folder_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate folder name for Windows filesystem.
    
    Args:
        folder_name: Name to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if not folder_name or not folder_name.strip():
        return False, "El nombre de la carpeta no puede estar vacío."
    
    folder_name = folder_name.strip()
    
    # Verificar caracteres inválidos
    if re.search(INVALID_CHARS, folder_name):
        return False, f"El nombre contiene caracteres inválidos: < > : \" | ? * \\ /"
    
    # Verificar nombres reservados de Windows
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    if folder_name.upper() in reserved_names:
        return False, f"'{folder_name}' es un nombre reservado de Windows."
    
    # Verificar longitud máxima (260 caracteres para ruta completa en Windows)
    if len(folder_name) > 255:
        return False, "El nombre de la carpeta es demasiado largo (máximo 255 caracteres)."
    
    # Verificar puntos finales o espacios finales
    if folder_name.endswith('.') or folder_name.endswith(' '):
        return False, "El nombre no puede terminar con punto o espacio."
    
    return True, None


def create_folder(parent_path: str, folder_name: str) -> FileOperationResult:
    """
    Create a folder in the specified parent path.
    
    Args:
        parent_path: Path where the folder will be created.
        folder_name: Name of the folder to create.
        
    Returns:
        FileOperationResult with success status and error message if failed.
    """
    # Validar ruta padre
    parent, error_msg = validate_parent_path_for_creation(parent_path)
    if error_msg:
        logger.error(f"Error validando ruta padre {parent_path}: {error_msg}")
        return FileOperationResult.error(error_msg)
    
    # Validar nombre de carpeta
    is_valid, error_msg = validate_folder_name(folder_name)
    if not is_valid:
        return FileOperationResult.error(error_msg)
    
    # Crear ruta completa
    folder_path = parent / folder_name.strip()
    
    # Verificar si ya existe
    if folder_path.exists():
        return FileOperationResult.error(f"Ya existe una carpeta con el nombre '{folder_name}'.")
    
    # Crear carpeta
    try:
        folder_path.mkdir(parents=False, exist_ok=False)
        logger.info(f"Carpeta creada exitosamente: {folder_path}")
        return FileOperationResult.ok()
    except FileExistsError:
        return FileOperationResult.error(f"La carpeta '{folder_name}' ya existe.")
    except PermissionError:
        logger.error(f"Sin permisos para crear carpeta en {parent_path}")
        return FileOperationResult.error(f"No tienes permisos para crear carpetas en esta ubicación.")
    except OSError as e:
        logger.error(f"Error del sistema al crear carpeta {folder_path}: {e}")
        return FileOperationResult.error(f"Error al crear la carpeta: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al crear carpeta {folder_path}: {e}")
        return FileOperationResult.error(f"Error inesperado: {str(e)}")

