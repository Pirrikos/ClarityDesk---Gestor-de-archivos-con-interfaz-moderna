"""
TabStateManager - State management helpers for TabManager.

Handles loading and saving tab state and complete application state.
"""

from typing import List, Optional, Tuple

from app.services.path_utils import normalize_path
from app.services.tab_helpers import validate_folder
from app.services.tab_storage_service import load_app_state, load_state, save_app_state, save_state


class TabStateManager:
    """Manages tab state persistence and complete application state."""
    
    def __init__(self, storage_path):
        """
        Initialize state manager.
        
        Args:
            storage_path: Path to storage file.
        """
        self._storage_path = storage_path
    
    def load_tabs_and_index(self) -> Tuple[List[str], int, bool]:
        """
        Load tabs and active index from storage.
        
        Returns:
            Tuple of (tabs list, active index, needs_save flag).
        """
        tabs, index, needs_save = load_state(self._storage_path, validate_folder)
        # Normalize all loaded tabs
        normalized_tabs = [normalize_path(tab) for tab in tabs]
        return normalized_tabs, index, needs_save
    
    def save_tabs_and_index(self, tabs: List[str], active_index: int) -> None:
        """
        Save tabs and active index to storage.
        
        Args:
            tabs: List of tab paths.
            active_index: Active tab index.
        """
        save_state(self._storage_path, tabs, active_index)
    
    def build_app_state(
        self,
        tabs: List[str],
        active_tab_path: Optional[str],
        history: List[str],
        history_index: int,
        focus_tree_paths: List[str],
        expanded_nodes: List[str]
    ) -> dict:
        """
        Build complete application state dict from current state.
        
        Args:
            tabs: List of open tab paths.
            active_tab_path: Currently active tab path (or None).
            history: Navigation history list.
            history_index: Current history index.
            focus_tree_paths: List of paths in focus tree.
            expanded_nodes: List of expanded node paths.
            
        Returns:
            State dict ready for persistence.
        """
        # Normalize all paths
        normalized_tabs = [normalize_path(tab) for tab in tabs]
        normalized_active = normalize_path(active_tab_path) if active_tab_path else None
        normalized_history = [normalize_path(path) for path in history]
        normalized_tree_paths = [normalize_path(path) for path in focus_tree_paths]
        normalized_expanded = [normalize_path(path) for path in expanded_nodes]
        
        return {
            'open_tabs': normalized_tabs,
            'active_tab': normalized_active,
            'history': normalized_history,
            'history_index': history_index,
            'focus_tree_paths': normalized_tree_paths,
            'expanded_nodes': normalized_expanded
        }
    
    def apply_app_state(self, state: dict) -> dict:
        """
        Apply saved application state, returning validated state.
        
        Validates and normalizes all paths. Returns dict with:
        - open_tabs: Validated and normalized tabs
        - active_tab: Validated active tab (or None)
        - history: Validated and normalized history
        - history_index: Validated history index
        - focus_tree_paths: Validated and normalized tree paths
        - expanded_nodes: Validated and normalized expanded nodes
        
        Args:
            state: State dict from load_app_state().
            
        Returns:
            Validated state dict with normalized paths.
        """
        if not state:
            return {
                'open_tabs': [],
                'active_tab': None,
                'history': [],
                'history_index': -1,
                'focus_tree_paths': [],
                'expanded_nodes': []
            }
        
        # Validate and normalize tabs
        open_tabs = state.get('open_tabs', [])
        valid_tabs = []
        for tab_path in open_tabs:
            normalized = normalize_path(tab_path)
            if validate_folder(normalized):
                valid_tabs.append(normalized)
        
        # Get active tab (normalized)
        active_tab = state.get('active_tab')
        if active_tab:
            active_tab = normalize_path(active_tab)
            # Ensure active tab is in valid tabs
            if active_tab not in valid_tabs:
                active_tab = valid_tabs[0] if valid_tabs else None
        elif valid_tabs:
            active_tab = valid_tabs[0]
        
        # Validate and normalize history
        history = state.get('history', [])
        valid_history = []
        for path in history:
            normalized = normalize_path(path)
            if validate_folder(normalized):
                valid_history.append(normalized)
        
        # Validate history index
        history_index = state.get('history_index', -1)
        if valid_history:
            history_index = max(0, min(history_index, len(valid_history) - 1))
        else:
            history_index = -1
        
        # Validate and normalize focus tree paths
        focus_tree_paths = state.get('focus_tree_paths', [])
        valid_tree_paths = []
        for path in focus_tree_paths:
            normalized = normalize_path(path)
            if validate_folder(normalized):
                valid_tree_paths.append(normalized)
        
        # Validate and normalize expanded nodes
        expanded_nodes = state.get('expanded_nodes', [])
        valid_expanded = []
        for path in expanded_nodes:
            normalized = normalize_path(path)
            if validate_folder(normalized):
                valid_expanded.append(normalized)
        
        return {
            'open_tabs': valid_tabs,
            'active_tab': active_tab,
            'history': valid_history,
            'history_index': history_index,
            'focus_tree_paths': valid_tree_paths,
            'expanded_nodes': valid_expanded
        }
    
    def load_app_state(self) -> Optional[dict]:
        """
        Load complete application state from storage.
        
        Returns:
            State dict or None if not available.
        """
        return load_app_state(self._storage_path)
    
    def save_app_state(self, state: dict) -> None:
        """
        Save complete application state to storage.
        
        Args:
            state: State dict from build_app_state().
        """
        save_app_state(self._storage_path, state)

