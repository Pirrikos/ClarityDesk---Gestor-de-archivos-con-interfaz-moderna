"""
TabValidator - Tab path validation.

Handles validation of folder paths for tabs.
Supports Desktop Focus and Trash Focus.
"""

from pathlib import Path

from app.services.desktop_path_helper import DESKTOP_FOCUS_PATH, is_desktop_focus
from app.services.trash_storage import TRASH_FOCUS_PATH


def validate_folder(folder_path: str) -> bool:
    """
    Validate that a folder path exists and is accessible.
    Allows Desktop Focus and Trash Focus (virtual paths).

    Args:
        folder_path: Path to validate.

    Returns:
        True if valid folder, False otherwise.
    """
    if not folder_path or not isinstance(folder_path, str):
        return False

    # Allow Desktop Focus (real Desktop or virtual identifier)
    if is_desktop_focus(folder_path):
        return True
    
    # Allow Trash Focus (virtual identifier)
    if folder_path == TRASH_FOCUS_PATH:
        return True

    try:
        path = Path(folder_path)
        return path.exists() and path.is_dir()
    except (OSError, ValueError):
        return False

