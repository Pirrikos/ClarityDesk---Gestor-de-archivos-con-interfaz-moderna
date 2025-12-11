"""
TabNavigationHandler - Navigation logic for TabManager.

Handles back/forward navigation and history folder activation.
"""

from typing import Callable, Optional, Tuple

from app.services.tab_finder import find_tab_index
from app.services.tab_history_manager import TabHistoryManager
from app.services.tab_path_normalizer import normalize_path
from app.services.tab_validator import validate_folder


class TabNavigationHandler:
    """Handles navigation operations for TabManager."""
    
    def __init__(
        self,
        history_manager: TabHistoryManager,
        tabs: list,
        watcher,
        save_state_callback: Callable[[], None],
        watch_and_emit_callback: Callable[[str], None]
    ):
        """
        Initialize navigation handler.
        
        Args:
            history_manager: TabHistoryManager instance.
            tabs: Reference to tabs list (will be modified).
            watcher: FileSystemWatcherService instance.
            save_state_callback: Callback to save state.
            watch_and_emit_callback: Callback to watch and emit signal.
        """
        self._history_manager = history_manager
        self._tabs = tabs
        self._watcher = watcher
        self._save_state = save_state_callback
        self._watch_and_emit = watch_and_emit_callback
    
    def can_go_back(self) -> bool:
        """Check if back navigation is possible."""
        return self._history_manager.can_go_back()
    
    def can_go_forward(self) -> bool:
        """Check if forward navigation is possible."""
        return self._history_manager.can_go_forward()
    
    def go_back(self) -> Optional[int]:
        """
        Move one step back in history, activate that folder.
        
        Returns:
            New active index if navigation occurred, None otherwise.
        """
        if not self.can_go_back():
            return None
        
        folder_path = self._history_manager.move_back()
        return self._activate_history_folder(folder_path)
    
    def go_forward(self) -> Optional[int]:
        """
        Move one step forward in history, activate that folder.
        
        Returns:
            New active index if navigation occurred, None otherwise.
        """
        if not self.can_go_forward():
            return None
        
        folder_path = self._history_manager.move_forward()
        return self._activate_history_folder(folder_path)
    
    def _activate_history_folder(self, folder_path: str) -> Optional[int]:
        """
        Activate the given folder WITHOUT updating history.
        
        Used by go_back() and go_forward() to navigate through history
        without creating new history entries.
        
        Returns:
            New active index, or None if folder is invalid.
        """
        normalized_path = normalize_path(folder_path)
        
        # Validate folder exists before activating
        if not validate_folder(normalized_path):
            return None
        
        # PROTECTION: Set flag to prevent history updates during navigation
        self._history_manager.set_navigating_flag(True)
        try:
            # Find existing tab - do NOT add new tabs during navigation
            # Navigation should only activate existing Focus, not create new ones
            tab_index = find_tab_index(self._tabs, normalized_path)
            
            if tab_index is None:
                # Folder is not a Focus - navigation fails silently
                # This prevents automatic Focus creation from history navigation
                return None
            
            # Always update watcher and emit signal
            # This ensures the view refreshes when navigating through history
            self._watcher.stop_watching()
            self._save_state()
            self._watch_and_emit(normalized_path)
            
            return tab_index
        finally:
            self._history_manager.set_navigating_flag(False)
