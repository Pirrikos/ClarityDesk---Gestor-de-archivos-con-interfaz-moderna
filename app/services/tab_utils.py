"""
TabUtils - Utility functions for tab management.

Helper functions for tab display names and related utilities.
"""

import os

from app.services.desktop_path_helper import is_desktop_focus
from app.services.trash_storage import TRASH_FOCUS_PATH


def get_tab_display_name(folder_path: str) -> str:
    """
    Get display name for a tab path.
    
    Converts virtual paths to user-friendly names:
    - Desktop Focus -> "Escritorio"
    - Trash Focus -> "Papelera"
    - Normal paths -> basename
    
    Args:
        folder_path: Folder path (can be virtual).
        
    Returns:
        Display name string.
    """
    if not folder_path:
        return ""
    
    # Desktop Focus
    if is_desktop_focus(folder_path):
        return "Escritorio"
    
    # Trash Focus
    if folder_path == TRASH_FOCUS_PATH:
        return "Papelera"
    
    # Normal path
    return os.path.basename(folder_path) or folder_path

