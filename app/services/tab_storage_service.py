"""
TabStorageService - Tab state persistence.

Handles saving and loading tab state to/from JSON storage.
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from app.services.path_utils import normalize_path
from app.services.tab_helpers import validate_folder


def load_state(storage_path: Path, validate_func) -> tuple[List[str], int, bool]:
    """Load tabs and active index from JSON storage."""
    if not storage_path.exists():
        return [], -1, False

    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tabs = data.get('tabs', [])
        active_index = data.get('active_index', -1)
        valid_tabs = _validate_tabs(tabs, validate_func)
        needs_save = len(valid_tabs) != len(tabs)
        final_index, needs_save = _adjust_active_index(active_index, valid_tabs, needs_save)

        return valid_tabs, final_index, needs_save
    except (json.JSONDecodeError, IOError, OSError):
        return [], -1, False


def _validate_tabs(tabs: List[str], validate_func) -> List[str]:
    """Validate and filter existing folder tabs, preserving original case."""
    valid_tabs = []
    for tab_path in tabs:
        # Validar usando normalización pero preservar path original
        normalized = normalize_path(tab_path)
        if validate_func(normalized):
            valid_tabs.append(tab_path)
    return valid_tabs


def _adjust_active_index(active_index: int, valid_tabs: List[str], needs_save: bool) -> tuple[int, bool]:
    """Adjust active index based on valid tabs."""
    if valid_tabs and 0 <= active_index < len(valid_tabs):
        return active_index, needs_save
    elif valid_tabs:
        return 0, True
    else:
        return -1, True


def save_state(storage_path: Path, tabs: List[str], active_index: int) -> None:
    """
    Save tabs and active index to JSON storage.

    Args:
        storage_path: Path to JSON storage file.
        tabs: List of tab folder paths.
        active_index: Index of active tab.
    """
    data = {
        'tabs': tabs,
        'active_index': active_index
    }

    try:
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (IOError, OSError):
        # Silently fail if we can't write (permissions, disk full, etc.)
        pass


def load_app_state(storage_path: Path) -> Optional[dict]:
    """
    Load complete application state from JSON storage.
    
    Returns state dict with:
    - open_tabs: List of open tab paths
    - active_tab: Active tab path (or None)
    - history: Navigation history list
    - history_index: Current history index
    - focus_tree_paths: List of paths in focus tree
    - expanded_nodes: List of expanded node paths
    - root_folders_order: List of normalized root folder paths in visual order (optional)
    
    Args:
        storage_path: Path to JSON storage file.
        
    Returns:
        State dict or None if file doesn't exist or is invalid.
    """
    if not storage_path.exists():
        return None
    
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Support both old format (tabs/active_index) and new format
        state = {
            'open_tabs': data.get('open_tabs', data.get('tabs', [])),
            'active_tab': data.get('active_tab', None),
            'history': data.get('history', []),
            'history_index': data.get('history_index', -1),
            'focus_tree_paths': data.get('focus_tree_paths', []),
            'expanded_nodes': data.get('expanded_nodes', []),
            'root_folders_order': data.get('root_folders_order', [])
        }
        
        # If old format, derive active_tab from active_index
        if state['active_tab'] is None and 'active_index' in data:
            active_index = data.get('active_index', -1)
            tabs = state['open_tabs']
            if 0 <= active_index < len(tabs):
                state['active_tab'] = tabs[active_index]
        
        return state
    except (json.JSONDecodeError, IOError, OSError):
        return None


def save_app_state(storage_path: Path, state: dict) -> None:
    """
    Save complete application state to JSON storage.
    
    Args:
        storage_path: Path to JSON storage file.
        state: State dict with keys:
            - open_tabs: List of open tab paths
            - active_tab: Active tab path (or None)
            - history: Navigation history list
            - history_index: Current history index
            - focus_tree_paths: List of paths in focus tree
            - expanded_nodes: List of expanded node paths
            - root_folders_order: List of normalized root folder paths in visual order (optional)
    """
    try:
        # Backwards compatibility: incluir también 'tabs' y 'active_index'
        data = dict(state)
        open_tabs = data.get('open_tabs', [])
        active_tab = data.get('active_tab')
        active_index = -1
        if open_tabs and active_tab in open_tabs:
            try:
                active_index = open_tabs.index(active_tab)
            except ValueError:
                active_index = -1
        data['tabs'] = open_tabs
        data['active_index'] = active_index
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (IOError, OSError):
        # Silently fail if we can't write (permissions, disk full, etc.)
        pass
