"""
TabManager - Manager for folder tabs and file listings.

Manages tabs (folder paths), active tab selection, state persistence,
and filtered file listings from the active folder.
"""

from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from app.services.file_extensions import SUPPORTED_EXTENSIONS

import os

from app.services.desktop_path_helper import DESKTOP_FOCUS_PATH, is_desktop_focus
from app.services.trash_storage import TRASH_FOCUS_PATH
from app.services.tab_utils import get_tab_display_name

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
        _, _, self._nav_handler, self._watcher = initialize_tab_manager(
            self, storage_path, self._load_state, self._watch_and_emit_internal
        )

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
    
    def get_state_manager(self):
        """Get TabStateManager instance."""
        return self._state_manager

    def get_files(self, extensions: Optional[set] = None, use_stacks: bool = False) -> List:
        """Get filtered file list from active folder."""
        return get_files_from_active_tab(
            self.get_active_folder(), extensions or self.SUPPORTED_EXTENSIONS, use_stacks
        )
    

    def _load_state(self) -> None:
        """Load tabs and active index from JSON storage."""
        self._tabs, self._active_index, needs_save = load_state(
            self._state_manager, self._history_manager
        )
        if needs_save:
            self._save_state()
    
    def _save_state(self) -> None:
        """Save tabs and active index to JSON storage."""
        save_state(self._state_manager, self._tabs, self._active_index)

    def _on_folder_changed(self, folder_path: str) -> None:
        """Handle folder change event from watcher."""
        on_folder_changed(self, folder_path, self.files_changed)

    def _watch_and_emit_internal(self, folder_path: str) -> None:
        """Start watching folder and emit active tab changed signal."""
        signal_watch_and_emit(folder_path, self._active_index, self._watcher, self.activeTabChanged)
    
    def get_watcher(self):
        """Get FileSystemWatcherService instance."""
        return self._watcher

    def can_go_back(self) -> bool:
        """Check if back navigation is possible."""
        return self._nav_handler.can_go_back()

    def can_go_forward(self) -> bool:
        """Check if forward navigation is possible."""
        return self._nav_handler.can_go_forward()

    def go_back(self) -> bool:
        """Move one step back in history, activate that folder."""
        new_index = self._nav_handler.go_back()
        if new_index is not None:
            self._active_index = new_index
            return True
        return False

    def go_forward(self) -> bool:
        """Move one step forward in history, activate that folder."""
        new_index = self._nav_handler.go_forward()
        if new_index is not None:
            self._active_index = new_index
            return True
        return False
    
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