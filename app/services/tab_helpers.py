"""
TabHelpers - Utility functions for tab management.

Consolidated helpers for tab path normalization, search, validation, and display.
All functions related to tab management in one place for easier maintenance.
"""

import os
from pathlib import Path
from typing import List, Optional

from app.services.path_utils import normalize_path
from app.services.desktop_path_helper import DESKTOP_FOCUS_PATH, is_desktop_focus
from app.services.trash_storage import TRASH_FOCUS_PATH
from app.services.file_path_utils import validate_folder as validate_folder_base


# ============================================================================
# SECTION 2: TAB SEARCH
# ============================================================================

def find_tab_index(tabs: List[str], folder_path: str) -> Optional[int]:
    """
    Find tab index by normalized path comparison.
    
    Args:
        tabs: List of tab paths.
        folder_path: Folder path to search for.
        
    Returns:
        Tab index if found, None otherwise.
    """
    normalized_path = normalize_path(folder_path)
    for idx, tab_path in enumerate(tabs):
        if normalize_path(tab_path) == normalized_path:
            return idx
    return None


def find_or_add_tab(tabs: List[str], folder_path: str) -> int:
    """
    Find tab index or add tab if not found.
    
    Args:
        tabs: List of tab paths (will be modified if tab not found).
        folder_path: Folder path to find or add.
        
    Returns:
        Tab index (existing or newly added).
    """
    normalized_path = normalize_path(folder_path)
    tab_index = find_tab_index(tabs, normalized_path)
    
    if tab_index is None:
        tabs.append(normalized_path)
        tab_index = len(tabs) - 1
    
    return tab_index


# ============================================================================
# SECTION 3: TAB VALIDATION
# ============================================================================

def validate_folder(folder_path: str) -> bool:
    """
    Validate that a folder path exists and is accessible.
    Allows Desktop Focus and Trash Focus (virtual paths).
    
    Usa file_path_utils.validate_folder como base y agrega soporte para paths virtuales.

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

    # Usar validación base de file_path_utils
    return validate_folder_base(folder_path)


# ============================================================================
# SECTION 4: TAB DISPLAY
# ============================================================================

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

