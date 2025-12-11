"""
TrashStorage - Trash storage and metadata management.

Handles trash folder paths and metadata persistence.
"""

import json
import os
from pathlib import Path
from typing import Optional


# Virtual path identifier for Trash Focus
TRASH_FOCUS_PATH = "__CLARITY_TRASH__"

# Trash limits
MAX_TRASH_AGE_DAYS = 30
MAX_TRASH_SIZE_MB = 2048


def get_trash_path() -> Path:
    """
    Get trash folder path (storage/trash/files).
    
    Returns:
        Path object to trash folder.
    """
    trash_dir = Path(__file__).parent.parent.parent / "storage" / "trash" / "files"
    trash_dir.mkdir(parents=True, exist_ok=True)
    return trash_dir


def get_trash_metadata_path() -> Path:
    """
    Get trash metadata file path.
    
    Returns:
        Path object to metadata.json.
    """
    metadata_dir = Path(__file__).parent.parent.parent / "storage" / "trash"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    return metadata_dir / "metadata.json"


def load_trash_metadata() -> dict:
    """
    Load trash metadata from JSON file.
    
    Returns:
        Dictionary mapping filename to metadata dict.
    """
    metadata_path = get_trash_metadata_path()
    if not metadata_path.exists():
        return {}
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_trash_metadata(metadata: dict) -> None:
    """
    Save trash metadata to JSON file.
    
    Args:
        metadata: Dictionary mapping filename to metadata dict.
    """
    metadata_path = get_trash_metadata_path()
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def list_trash_files() -> list[str]:
    """
    List files in trash (returns paths in trash folder).
    
    Returns:
        List of file paths in trash folder.
    """
    trash_dir = get_trash_path()
    if not trash_dir.exists():
        return []
    
    files = []
    try:
        for item in trash_dir.iterdir():
            if item.is_file() or item.is_dir():
                files.append(str(item))
    except (OSError, PermissionError):
        return []
    
    return sorted(files)


def get_trash_metadata_for_file(trash_file_path: str) -> Optional[dict]:
    """
    Get metadata for a file in trash.
    
    Args:
        trash_file_path: Path to file in trash folder.
        
    Returns:
        Metadata dict with 'original_path' and 'deleted_date', or None.
    """
    metadata = load_trash_metadata()
    filename = os.path.basename(trash_file_path)
    return metadata.get(filename)

