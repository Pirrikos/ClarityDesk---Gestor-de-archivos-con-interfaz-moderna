"""
TabManager - Manager for folder tabs and file listings.

Manages tabs (folder paths), active tab selection, state persistence,
and filtered file listings from the active folder.
"""

from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import QObject, Signal

from app.core.logger import get_logger
from app.services.file_extensions import SUPPORTED_EXTENSIONS

import os

logger = get_logger(__name__)

from app.services.desktop_path_helper import DESKTOP_FOCUS_PATH, is_desktop_focus
from app.services.trash_storage import TRASH_FOCUS_PATH
from app.services.tab_helpers import get_tab_display_name, find_tab_index

from app.managers.tab_manager_state import load_state, save_state, restore_state as state_restore_state
from app.managers.tab_manager_actions import (
    add_tab as action_add_tab,
    remove_tab as action_remove_tab,
    remove_tab_by_path as action_remove_tab_by_path,
    select_tab as action_select_tab,
    get_files_from_active_tab,
    activate_tab as action_activate_tab
)
from app.managers.tab_manager_signals import on_folder_changed, watch_and_emit as signal_watch_and_emit
from app.managers.tab_manager_init import initialize_tab_manager
from app.managers.tab_manager_restore import restore_tab_manager_state

if TYPE_CHECKING:
    from app.services.tab_state_manager import TabStateManager
    from app.services.filesystem_watcher_service import FileSystemWatcherService


class TabManager(QObject):
    """Manages folder tabs, active tab selection, and file listings."""

    tabsChanged = Signal(list)  # Emitted when tabs list changes
    activeTabChanged = Signal(int, str)  # Emitted when active tab changes (index, path)
    files_changed = Signal()  # Emitted when files in active folder change
    focus_cleared = Signal()  # Emitted when active focus is removed (no active tab)

    # Supported file extensions (from constants)
    SUPPORTED_EXTENSIONS = SUPPORTED_EXTENSIONS

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize TabManager and load saved state."""
        super().__init__()
        self._workspace_manager = None
        _, _, self._watcher = initialize_tab_manager(
            self, storage_path, self._load_state, self._watch_and_emit_internal
        )
    
    def set_workspace_manager(self, workspace_manager) -> None:
        """
        Set WorkspaceManager instance for state coordination.
        
        Args:
            workspace_manager: WorkspaceManager instance.
        """
        self._workspace_manager = workspace_manager

    def add_tab(self, folder_path: str) -> bool:
        """Add a folder as a tab and make it active."""
        # Store old index to avoid double emission
        old_index = self._active_index
        success, new_tabs, new_index = action_add_tab(
            self, folder_path, self._tabs, self._active_index,
            self._history_manager, self._save_state, self._watch_and_emit_internal,
            self.tabsChanged, self.activeTabChanged
        )
        if success:
            self._tabs = new_tabs
            self._active_index = new_index
            # If index changed, ensure watch_and_emit is called with updated index
            # This ensures activeTabChanged is emitted with correct index after state update
            if self._active_index != old_index and self._active_index >= 0:
                if self._active_index < len(self._tabs):
                    self._watch_and_emit_internal(self._tabs[self._active_index])
            self._save_full_app_state()
        return success

    def remove_tab(self, index: int) -> bool:
        """Remove a tab by index."""
        success, new_tabs, new_index = action_remove_tab(
            self, index, self._tabs, self._active_index,
            self._watcher, self._save_state, self._watch_and_emit_internal,
            self.tabsChanged, self.activeTabChanged, self.focus_cleared
        )
        if success:
            self._tabs = new_tabs
            self._active_index = new_index
            self._save_state()
            self._save_full_app_state()
        return success
    
    def remove_tab_by_path(self, folder_path: str) -> bool:
        """Remove a tab by folder path."""
        success, new_tabs, new_index = action_remove_tab_by_path(
            self, folder_path, self._tabs, self._active_index,
            self._watcher, self._save_state, self._watch_and_emit_internal,
            self.tabsChanged, self.activeTabChanged, self.focus_cleared
        )
        if success:
            self._tabs = new_tabs
            self._active_index = new_index
            self._save_state()
            self._save_full_app_state()
        return success

    def select_tab(self, index: int) -> bool:
        """Select a tab as active."""
        success, new_tabs, new_index = action_select_tab(
            self, index, self._tabs, self._active_index,
            self._history_manager, self._watcher,
            self._save_state, self._watch_and_emit_internal
        )
        if success:
            self._tabs = new_tabs
            self._active_index = new_index
            self._save_full_app_state()
        return success

    def get_active_folder(self) -> Optional[str]:
        """Get the path of the currently active folder."""
        if 0 <= self._active_index < len(self._tabs):
            return self._tabs[self._active_index]
        return None

    def get_tabs(self) -> List[str]:
        """Get list of all tab folder paths."""
        return self._tabs.copy()

    def get_active_index(self) -> int:
        """Get the index of the currently active tab."""
        return self._active_index
    
    def get_state_manager(self) -> 'TabStateManager':
        """Get TabStateManager instance."""
        return self._state_manager

    def get_files(self, extensions: Optional[set] = None, use_stacks: bool = False) -> List:
        """Get filtered file list from active folder."""
        return get_files_from_active_tab(
            self.get_active_folder(), extensions or self.SUPPORTED_EXTENSIONS, use_stacks
        )
    

    def _load_state(self) -> None:
        """Load tabs and active index from JSON storage."""
        # Si hay WorkspaceManager, NO cargar desde archivo antiguo
        # El estado se cargará desde el workspace activo en MainWindow
        if self._workspace_manager:
            self._tabs = []
            self._active_index = -1
            return
        
        # Backward compatibility: cargar desde archivo antiguo si no hay WorkspaceManager
        self._tabs, self._active_index, needs_save = load_state(
            self._state_manager, self._history_manager
        )
        if needs_save:
            self._save_state()
    
    def _save_state(self) -> None:
        """Save tabs and active index to JSON storage."""
        save_state(self._state_manager, self._tabs, self._active_index)
    
    def _save_full_app_state(self) -> None:
        """Save complete application state (open_tabs, active_tab, history) to JSON."""
        # Si hay WorkspaceManager, notificarle para que guarde en el workspace activo
        if self._workspace_manager:
            # WorkspaceManager recopilará el estado cuando sea necesario
            # No guardamos directamente aquí
            return
        
        # Fallback: guardar directamente si no hay WorkspaceManager (backward compatibility)
        try:
            state = self._state_manager.build_app_state(
                tabs=self._tabs,
                active_tab_path=self.get_active_folder(),
                history=self.get_history(),
                history_index=self.get_history_index(),
                focus_tree_paths=[],
                expanded_nodes=[]
            )
            self._state_manager.save_app_state(state)
        except Exception as e:
            logger.error(f"Failed to save full app state: {e}", exc_info=True)
    
    def get_current_state(self) -> dict:
        """
        Get current state (tabs and active_tab, without history).
        
        Returns:
            Dict with keys: tabs, active_tab
        """
        return {
            'tabs': self._tabs.copy(),
            'active_tab': self.get_active_folder()
        }
    
    def load_workspace_state(self, state: dict, emit_signals: bool = True) -> None:
        """
        Load workspace state (tabs and active_tab, without history).
        
        Args:
            state: Dict with keys: tabs, active_tab
            emit_signals: If True, emit signals after loading. If False, only update internal state.
        """
        tabs = state.get('tabs', [])
        active_tab = state.get('active_tab')
        
        # Detener watcher ANTES de cambiar estado (igual que en restore_state)
        if self._watcher:
            self._watcher.stop_watching()
        
        # Restaurar tabs sin crear entradas de historial
        self._tabs = tabs.copy() if tabs else []
        
        # Encontrar índice del tab activo
        if active_tab and active_tab in self._tabs:
            self._active_index = self._tabs.index(active_tab)
        elif self._tabs:
            self._active_index = 0
        else:
            self._active_index = -1
        
        # Emitir señales solo si se solicita
        if emit_signals:
            self.tabsChanged.emit(self._tabs.copy())
            if self._active_index >= 0 and self._active_index < len(self._tabs):
                # _watch_and_emit_internal emite activeTabChanged e inicia el watcher
                self._watch_and_emit_internal(self._tabs[self._active_index])

    def _on_folder_changed(self, folder_path: str) -> None:
        """Handle folder change event from watcher."""
        on_folder_changed(self, folder_path, self.files_changed)

    def _watch_and_emit_internal(self, folder_path: str) -> None:
        """Start watching folder and emit active tab changed signal."""
        try:
            idx = find_tab_index(self._tabs, folder_path)
            if idx is not None:
                self._active_index = idx
        except Exception as e:
            logger.warning(f"Failed to find tab index for {folder_path}: {e}")
        signal_watch_and_emit(folder_path, self._active_index, self._watcher, self.activeTabChanged)
    
    def get_watcher(self) -> Optional['FileSystemWatcherService']:
        """Get FileSystemWatcherService instance."""
        return self._watcher

    def can_go_back(self) -> bool:
        """Check if back navigation is possible."""
        return self._history_manager.can_go_back()

    def can_go_forward(self) -> bool:
        """Check if forward navigation is possible."""
        return self._history_manager.can_go_forward()

    def go_back(self) -> bool:
        """Move one step back in history, activate that folder."""
        if not self.can_go_back():
            return False
        
        # Obtener path del historial anterior
        folder_path = self._history_manager.get_back_path()
        
        # Encontrar índice del tab correspondiente
        tab_index = find_tab_index(self._tabs, folder_path)
        if tab_index is None:
            return False
        
        # Activar flag ANTES de mover historial y llamar select_tab
        # Esto evita que select_tab actualice el historial durante la navegación
        self._history_manager.set_navigating_flag(True)
        try:
            # Mover índice del historial
            self._history_manager.move_back()
            # Activar tab usando la función única responsable
            return self.select_tab(tab_index)
        finally:
            self._history_manager.set_navigating_flag(False)

    def go_forward(self) -> bool:
        """Move one step forward in history, activate that folder."""
        if not self.can_go_forward():
            return False
        
        # Obtener path del historial siguiente
        folder_path = self._history_manager.get_forward_path()
        
        # Encontrar índice del tab correspondiente
        tab_index = find_tab_index(self._tabs, folder_path)
        if tab_index is None:
            return False
        
        # Activar flag ANTES de mover historial y llamar select_tab
        # Esto evita que select_tab actualice el historial durante la navegación
        self._history_manager.set_navigating_flag(True)
        try:
            # Mover índice del historial
            self._history_manager.move_forward()
            # Activar tab usando la función única responsable
            return self.select_tab(tab_index)
        finally:
            self._history_manager.set_navigating_flag(False)
    
    def get_history(self) -> List[str]:
        """Get current navigation history."""
        return self._history_manager.get_history()
    
    def get_history_index(self) -> int:
        """Get current navigation history index."""
        return self._history_manager.get_history_index()
    
    def activate_tab(self, index: int) -> None:
        """Activate tab by index with validation."""
        action_activate_tab(self, index, self.get_tabs, self.select_tab)
    
    def restore_state(
        self,
        tabs: List[str],
        active_tab_path: Optional[str],
        history: List[str],
        history_index: int
    ) -> None:
        """Restore state from saved state without creating new history entries."""
        self._tabs, self._active_index = restore_tab_manager_state(
            self, tabs, active_tab_path, history, history_index,
            self._history_manager, self._watcher, self._watch_and_emit_internal,
            self.tabsChanged, self.activeTabChanged
        )

    def get_tab_display_name(self, folder_path: str) -> str:
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
        return get_tab_display_name(folder_path)
