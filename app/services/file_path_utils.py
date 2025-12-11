"""
FilePathUtils - Path validation and conflict resolution utilities.

Pure utility functions for validating paths and resolving filename conflicts.
No Qt dependencies.
"""

from pathlib import Path


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

