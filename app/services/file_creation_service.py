"""
FileCreationService - Service for creating files in the filesystem.

Handles file creation with validation and error handling.
Pure functions - no state, no class instantiation needed.
"""

from pathlib import Path
from typing import Optional

from app.core.logger import get_logger
from app.models.file_operation_result import FileOperationResult
from app.services.folder_creation_service import validate_folder_name
from app.services.file_path_utils import validate_parent_path_for_creation

logger = get_logger(__name__)


def validate_file_name(file_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate file name (without extension) for Windows filesystem.
    
    Reuses folder name validation since rules are the same.
    
    Args:
        file_name: Name to validate (without extension).
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    return validate_folder_name(file_name)


def create_text_file(parent_path: str, file_name: str) -> FileOperationResult:
    """
    Create a text file (.txt) in the specified parent path.
    
    Args:
        parent_path: Path where the file will be created.
        file_name: Name of the file to create (without extension).
        
    Returns:
        FileOperationResult with success status and error message if failed.
    """
    return _create_file(
        parent_path=parent_path,
        file_name=file_name,
        extension="txt",
        content=""
    )


def create_markdown_file(parent_path: str, file_name: str) -> FileOperationResult:
    """
    Create a Markdown file (.md) in the specified parent path.
    
    Creates file with basic header template.
    
    Args:
        parent_path: Path where the file will be created.
        file_name: Name of the file to create (without extension).
        
    Returns:
        FileOperationResult with success status and error message if failed.
    """
    return _create_file(
        parent_path=parent_path,
        file_name=file_name,
        extension="md",
        content="# \n"
    )


def create_docx_file(parent_path: str, file_name: str) -> FileOperationResult:
    """
    Create a Word document (.docx) in the specified parent path.
    
    Creates a minimal valid DOCX file using python-docx.
    
    Args:
        parent_path: Path where the file will be created.
        file_name: Name of the file to create (without extension).
        
    Returns:
        FileOperationResult with success status and error message if failed.
    """
    # Validar ruta padre
    parent, error_msg = validate_parent_path_for_creation(parent_path)
    if error_msg:
        logger.error(f"Error validando ruta padre {parent_path}: {error_msg}")
        return FileOperationResult.error(error_msg)
    
    # Validar nombre de archivo
    is_valid, error_msg = validate_file_name(file_name)
    if not is_valid:
        return FileOperationResult.error(error_msg)
    
    # Crear ruta completa
    file_path = parent / f"{file_name.strip()}.docx"
    
    # Verificar si ya existe
    if file_path.exists():
        return FileOperationResult.error(f"Ya existe un archivo con el nombre '{file_name}.docx'.")
    
    # Crear documento Word
    try:
        from docx import Document
        
        doc = Document()
        doc.add_paragraph("")  # Párrafo vacío inicial
        doc.save(str(file_path))
        
        logger.info(f"Documento Word creado exitosamente: {file_path}")
        return FileOperationResult.ok()
    except ImportError:
        logger.error("python-docx no está disponible")
        return FileOperationResult.error("Error al crear documento Word: python-docx no está instalado.")
    except PermissionError:
        logger.error(f"Sin permisos para crear archivo en {parent_path}")
        return FileOperationResult.error(f"No tienes permisos para crear archivos en esta ubicación.")
    except OSError as e:
        logger.error(f"Error del sistema al crear archivo {file_path}: {e}")
        return FileOperationResult.error(f"Error al crear el archivo: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al crear documento Word {file_path}: {e}")
        return FileOperationResult.error(f"Error inesperado: {str(e)}")


def _create_file(
    parent_path: str,
    file_name: str,
    extension: str,
    content: str
) -> FileOperationResult:
    """
    Internal helper to create text-based files (.txt, .md).
    
    Args:
        parent_path: Path where the file will be created.
        file_name: Name of the file to create (without extension).
        extension: File extension (without dot).
        content: Initial content for the file.
        
    Returns:
        FileOperationResult with success status and error message if failed.
    """
    # Validar ruta padre
    parent, error_msg = validate_parent_path_for_creation(parent_path)
    if error_msg:
        logger.error(f"Error validando ruta padre {parent_path}: {error_msg}")
        return FileOperationResult.error(error_msg)
    
    # Validar nombre de archivo
    is_valid, error_msg = validate_file_name(file_name)
    if not is_valid:
        return FileOperationResult.error(error_msg)
    
    # Crear ruta completa
    file_path = parent / f"{file_name.strip()}.{extension}"
    
    # Verificar si ya existe
    if file_path.exists():
        return FileOperationResult.error(f"Ya existe un archivo con el nombre '{file_name}.{extension}'.")
    
    # Crear archivo
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Archivo creado exitosamente: {file_path}")
        return FileOperationResult.ok()
    except PermissionError:
        logger.error(f"Sin permisos para crear archivo en {parent_path}")
        return FileOperationResult.error(f"No tienes permisos para crear archivos en esta ubicación.")
    except OSError as e:
        logger.error(f"Error del sistema al crear archivo {file_path}: {e}")
        return FileOperationResult.error(f"Error al crear el archivo: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al crear archivo {file_path}: {e}")
        return FileOperationResult.error(f"Error inesperado: {str(e)}")

