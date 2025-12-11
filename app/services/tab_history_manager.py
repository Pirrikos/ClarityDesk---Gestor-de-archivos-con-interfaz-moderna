"""
TabHistoryManager - Navigation history management for TabManager.

Manages linear navigation history with back/forward capabilities.
"""

from typing import List


class TabHistoryManager:
    """Manages navigation history for folder navigation."""
    
    def __init__(self):
        """Initialize empty history."""
        self._history: List[str] = []
        self._history_index: int = -1
        self._navigating_from_history: bool = False
    
    def initialize_with_path(self, folder_path: str) -> None:
        """
        Initialize history with a single folder path.
        
        Args:
            folder_path: Normalized folder path to initialize with.
        """
        self._history = [folder_path]
        self._history_index = 0
    
    def update_on_navigate(self, folder_path: str, normalize_func) -> None:
        """
        Update navigation history when user navigates to a folder.
        
        Args:
            folder_path: Folder path to add to history.
            normalize_func: Function to normalize paths.
        """
        # PROTECTION: Block history updates when navigating from history
        if self._navigating_from_history:
            return
        
        normalized_path = normalize_func(folder_path)
        
        if not self._history:
            self._history.append(normalized_path)
            self._history_index = 0
            return
        
        current_path = self._history[self._history_index] if self._history_index >= 0 else None
        if normalized_path == current_path:
            return
        
        # Truncate forward history if not at end
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]
        
        self._history.append(normalized_path)
        self._history_index = len(self._history) - 1
    
    def can_go_back(self) -> bool:
        """Check if back navigation is possible."""
        return self._history_index > 0
    
    def can_go_forward(self) -> bool:
        """Check if forward navigation is possible."""
        return (
            self._history_index >= 0
            and self._history_index < len(self._history) - 1
        )
    
    def get_back_path(self) -> str:
        """
        Get path for back navigation.
        
        Returns:
            Folder path one step back in history.
        """
        if not self.can_go_back():
            raise IndexError("Cannot go back: already at start of history")
        return self._history[self._history_index - 1]
    
    def get_forward_path(self) -> str:
        """
        Get path for forward navigation.
        
        Returns:
            Folder path one step forward in history.
        """
        if not self.can_go_forward():
            raise IndexError("Cannot go forward: already at end of history")
        return self._history[self._history_index + 1]
    
    def move_back(self) -> str:
        """
        Move one step back in history.
        
        Returns:
            Folder path at new position.
        """
        self._history_index -= 1
        return self._history[self._history_index]
    
    def move_forward(self) -> str:
        """
        Move one step forward in history.
        
        Returns:
            Folder path at new position.
        """
        self._history_index += 1
        return self._history[self._history_index]
    
    def set_navigating_flag(self, value: bool) -> None:
        """
        Set flag to prevent history updates during navigation.
        
        Args:
            value: True to block updates, False to allow.
        """
        self._navigating_from_history = value
    
    def get_history(self) -> List[str]:
        """
        Get current history list.
        
        Returns:
            List of folder paths in history.
        """
        return self._history.copy()
    
    def get_history_index(self) -> int:
        """
        Get current history index.
        
        Returns:
            Current index in history (-1 if empty).
        """
        return self._history_index
    
    def restore_history(self, history: List[str], index: int) -> None:
        """
        Restore history from saved state.
        
        Sets navigating flag to prevent updates during restoration.
        Caller must reset flag after restoration is complete.
        
        Args:
            history: List of folder paths to restore.
            index: Index to restore to.
        """
        self._history = history.copy() if history else []
        # Clamp index to valid range
        if self._history:
            self._history_index = max(0, min(index, len(self._history) - 1))
        else:
            self._history_index = -1

