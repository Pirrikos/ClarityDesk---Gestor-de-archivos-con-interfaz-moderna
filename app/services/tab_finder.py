"""
TabFinder - Tab search utilities for TabManager.

Provides normalized tab search functionality.
"""

from typing import List, Optional

from app.services.tab_path_normalizer import normalize_path


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

