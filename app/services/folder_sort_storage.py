"""
Folder Sort Storage - Persistent storage for folder sorting preferences.

Stores sort column and order for each folder path.
"""

import json
import os
from typing import Optional, Tuple
from PySide6.QtCore import Qt

STORAGE_FILE = "storage/folder_sort_preferences.json"


def _ensure_storage_dir() -> None:
    """Ensure storage directory exists."""
    os.makedirs("storage", exist_ok=True)


def _load_preferences() -> dict:
    """Load sort preferences from storage."""
    _ensure_storage_dir()
    if not os.path.exists(STORAGE_FILE):
        return {}

    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_preferences(preferences: dict) -> None:
    """Save sort preferences to storage."""
    _ensure_storage_dir()
    try:
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(preferences, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def get_folder_sort(folder_path: str) -> Optional[Tuple[int, Qt.SortOrder]]:
    """
    Get saved sort preferences for a folder.

    Args:
        folder_path: Absolute path to folder.

    Returns:
        Tuple of (column_index, sort_order) or None if no preference saved.
    """
    if not folder_path:
        return None

    preferences = _load_preferences()

    # Normalize path for consistent lookup
    from app.services.path_utils import normalize_path
    normalized = normalize_path(folder_path)

    if normalized not in preferences:
        return None

    pref = preferences[normalized]
    column = pref.get('column')
    order_str = pref.get('order')

    if column is None or order_str is None:
        return None

    # Convert string to Qt.SortOrder
    sort_order = (
        Qt.SortOrder.AscendingOrder
        if order_str == 'asc'
        else Qt.SortOrder.DescendingOrder
    )

    return (column, sort_order)


def set_folder_sort(folder_path: str, column: int, sort_order: Qt.SortOrder) -> None:
    """
    Save sort preferences for a folder.

    Args:
        folder_path: Absolute path to folder.
        column: Column index (1-4).
        sort_order: Qt.SortOrder value.
    """
    if not folder_path:
        return

    # Normalize path for consistent storage
    from app.services.path_utils import normalize_path
    normalized = normalize_path(folder_path)

    preferences = _load_preferences()

    # Convert Qt.SortOrder to string
    order_str = 'asc' if sort_order == Qt.SortOrder.AscendingOrder else 'desc'

    preferences[normalized] = {
        'column': column,
        'order': order_str
    }

    _save_preferences(preferences)


def clear_folder_sort(folder_path: str) -> None:
    """
    Clear sort preferences for a folder.

    Args:
        folder_path: Absolute path to folder.
    """
    if not folder_path:
        return

    from app.services.path_utils import normalize_path
    normalized = normalize_path(folder_path)

    preferences = _load_preferences()

    if normalized in preferences:
        del preferences[normalized]
        _save_preferences(preferences)
