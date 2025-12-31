"""
FilePathUtils - Path validation and conflict resolution utilities.

Pure utility functions for validating paths and resolving filename conflicts.
No Qt dependencies.
"""

import os
from pathlib import Path
from typing import Optional


def validate_file(file_path: str) -> bool:
    """
    Validate that a file path exists and is a file.

    Returns False for directories or missing paths to prevent accidents.
    """
    if not file_path or not isinstance(file_path, str):
        return False

    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except (OSError, ValueError):
        return False


def validate_folder(folder_path: str) -> bool:
    """
    Validate that a folder path exists and is a directory.
    """
    if not folder_path or not isinstance(folder_path, str):
        return False

    try:
        path = Path(folder_path)
        return path.exists() and path.is_dir()
    except (OSError, ValueError):
        return False


def validate_parent_path_for_creation(parent_path: str) -> tuple[Optional[Path], Optional[str]]:
    """
    Validate parent path exists and is a directory for file/folder creation.
    
    Returns Path object if valid, or error message string if invalid.
    Used by file and folder creation services.
    
    Args:
        parent_path: Path to validate.
        
    Returns:
        Tuple of (Path object, None) if valid, or (None, error_message) if invalid.
    """
    if not parent_path or not isinstance(parent_path, str):
        return None, "La ruta no es válida."
    
    try:
        parent = Path(parent_path)
        if not parent.exists():
            return None, f"La ruta no existe: {parent_path}"
        if not parent.is_dir():
            return None, f"La ruta no es una carpeta: {parent_path}"
        return parent, None
    except Exception as e:
        return None, f"Error validando ruta: {str(e)}"


def validate_path(path: str) -> bool:
    """
    Validate that a path exists (file or folder).
    """
    if not path or not isinstance(path, str):
        return False

    try:
        p = Path(path)
        return p.exists()
    except (OSError, ValueError):
        return False


def is_office_temp_file(file_path: str) -> bool:
    """
    Check if a file is a Microsoft Office temporary file.

    Office creates temporary lock files when documents are opened:
    - ~$*.docx, ~$*.xlsx, ~$*.pptx (lock files for Word, Excel, PowerPoint)
    - ~WRL*.tmp (Word recovery files)
    - *.tmp in general Office temp files

    These should be hidden from the UI but are legitimate filesystem files.

    Args:
        file_path: Path to check.

    Returns:
        True if file is an Office temporary file, False otherwise.
    """
    if not file_path or not isinstance(file_path, str):
        return False

    try:
        filename = os.path.basename(file_path)

        # Lock files: ~$documento.docx, ~$hoja.xlsx, ~$presentacion.pptx
        if filename.startswith('~$'):
            return True

        # Word recovery files: ~WRL0001.tmp, ~WRL0002.tmp, etc.
        if filename.startswith('~WRL') and filename.endswith('.tmp'):
            return True

        # General Office temp files (be more specific to avoid false positives)
        # Check for ~*.tmp pattern (tilde prefix + .tmp extension)
        if filename.startswith('~') and filename.endswith('.tmp'):
            return True

        return False
    except Exception:
        return False


def resolve_conflict(target_path: Path) -> Path:
    """
    Resolve filename/foldername conflicts by appending a number.

    If target exists, tries target (1), target (2), etc. until finding
    an available name. Works for both files and folders.
    """
    if not target_path.exists():
        return target_path

    # Handle folders (no suffix) and files (with suffix)
    if target_path.is_dir():
        # For folders, use the full name as stem
        stem = target_path.name
        suffix = ""
    else:
        stem = target_path.stem
        suffix = target_path.suffix

    parent = target_path.parent

    counter = 1
    while True:
        new_name = f"{stem} ({counter}){suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1

        # Safety limit to prevent infinite loops
        if counter > 10000:
            return target_path

