"""
TabStateManager - State management helpers for TabManager.

Handles loading and saving tab state and complete application state.
"""

from typing import List, Optional, Tuple

from app.services.path_utils import normalize_path, is_state_context_path
from app.services.tab_helpers import validate_folder
from app.services.tab_storage_service import load_app_state, load_state, save_app_state, save_state
from app.services.desktop_path_helper import is_system_desktop


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
        # NO normalizar al cargar - preservar paths originales (case-preserving)
        # La normalización solo se usa para comparaciones internas
        return tabs, index, needs_save
    
    def save_tabs_and_index(self, tabs: List[str], active_index: int) -> None:
        """
        Save tabs and active index to storage.
        
        Args:
            tabs: List of tab paths.
            active_index: Active tab index.
        """
        save_state(self._storage_path, tabs, active_index)
    
    def _validate_and_preserve_paths(self, paths: List[str]) -> List[str]:
        """
        Validar paths usando normalización pero preservar originales.
        
        Args:
            paths: Lista de paths a validar.
            
        Returns:
            Lista de paths originales válidos (case-preserving).
        """
        valid_paths = []
        for path in paths:
            # Prohibir Escritorio del sistema
            if is_system_desktop(path):
                continue
            normalized = normalize_path(path)
            if validate_folder(normalized):
                valid_paths.append(path)
        return valid_paths
    
    def build_app_state(
        self,
        tabs: List[str],
        active_tab_path: Optional[str],
        history: List[str],
        history_index: int,
        focus_tree_paths: List[str],
        expanded_nodes: List[str],
        root_folders_order: Optional[List[str]] = None
    ) -> dict:
        """
        Build complete application state dict from current state.
        
        REGLA CRÍTICA: Los paths virtuales de estado (@state://...) NO se guardan como tabs activos.
        Si active_tab_path es un path virtual, se guarda como None.
        
        Args:
            tabs: List of open tab paths.
            active_tab_path: Currently active tab path (or None).
            history: Navigation history list.
            history_index: Current history index.
            focus_tree_paths: List of paths in focus tree.
            expanded_nodes: List of expanded node paths.
            root_folders_order: List of normalized root folder paths in visual order.
            
        Returns:
            State dict ready for persistence.
        """
        # REGLA CRÍTICA: No guardar paths virtuales como active_tab
        # Los contextos de estado se manejan por separado, no como tabs
        if active_tab_path and is_state_context_path(active_tab_path):
            active_tab_path = None
        
        # NO normalizar al guardar - preservar paths originales (case-preserving)
        # Los paths ya vienen case-preserving desde TabManager
        # La normalización solo se usa para comparaciones internas
        # root_folders_order ya viene normalizado (solo para orden interno)
        state = {
            'open_tabs': tabs,
            'active_tab': active_tab_path,
            'history': history,
            'history_index': history_index,
            'focus_tree_paths': focus_tree_paths,
            'expanded_nodes': expanded_nodes
        }
        if root_folders_order is not None:
            state['root_folders_order'] = root_folders_order
        return state
    
    def apply_app_state(self, state: dict) -> dict:
        """
        Apply saved application state, returning validated state.
        
        Validates paths using normalization but preserves original case.
        Returns dict with:
        - open_tabs: Validated tabs (case-preserving)
        - active_tab: Validated active tab (case-preserving)
        - history: Validated history (case-preserving)
        - history_index: Validated history index
        - focus_tree_paths: Validated tree paths (case-preserving)
        - expanded_nodes: Validated expanded nodes (case-preserving)
        
        Args:
            state: State dict from load_app_state().
            
        Returns:
            Validated state dict with case-preserving paths.
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
        
        # Validate tabs (usar normalización solo para validar, preservar path original)
        open_tabs = state.get('open_tabs', [])
        valid_tabs = self._validate_and_preserve_paths(open_tabs)
        
        # Get active tab (preservar path original)
        active_tab = state.get('active_tab')
        if active_tab:
            normalized_active = normalize_path(active_tab)
            # Buscar el tab activo usando normalización para comparar
            found = False
            for tab in valid_tabs:
                if normalize_path(tab) == normalized_active:
                    active_tab = tab
                    found = True
                    break
            if not found:
                active_tab = valid_tabs[0] if valid_tabs else None
        elif valid_tabs:
            active_tab = valid_tabs[0]
        
        # Validate history (preservar paths originales)
        history = state.get('history', [])
        valid_history = self._validate_and_preserve_paths(history)
        
        # Validate history index
        history_index = state.get('history_index', -1)
        if valid_history:
            history_index = max(0, min(history_index, len(valid_history) - 1))
        else:
            history_index = -1
        
        # Validate focus tree paths (preservar paths originales)
        focus_tree_paths = state.get('focus_tree_paths', [])
        valid_tree_paths = self._validate_and_preserve_paths(focus_tree_paths)
        
        # Validate expanded nodes (preservar paths originales)
        expanded_nodes = state.get('expanded_nodes', [])
        valid_expanded = self._validate_and_preserve_paths(expanded_nodes)
        
        # Validate root_folders_order (ya viene normalizado, solo validar existencia)
        root_folders_order = state.get('root_folders_order', [])
        valid_root_order = []
        for normalized_path in root_folders_order:
            # Prohibir Escritorio del sistema
            if is_system_desktop(normalized_path):
                continue
            if validate_folder(normalized_path):
                valid_root_order.append(normalized_path)
        
        result = {
            'open_tabs': valid_tabs,
            'active_tab': active_tab,
            'history': valid_history,
            'history_index': history_index,
            'focus_tree_paths': valid_tree_paths,
            'expanded_nodes': valid_expanded
        }
        if valid_root_order:
            result['root_folders_order'] = valid_root_order
        return result
    
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

