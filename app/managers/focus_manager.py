"""
FocusManager - Orchestrator for Focus (tab) creation and navigation.

Manages Focus instances identified by folder paths.
Delegates actual tab management to TabManager.
Notifies tree sidebar when Focus is opened.
"""

from typing import Optional

from PySide6.QtCore import QObject, Signal

from app.managers.tab_manager import TabManager


class FocusManager(QObject):
    """Orchestrator for Focus (tab) management via TabManager."""
    
    focus_opened = Signal(str)  # Emitted when Focus is opened (folder path)
    focus_removed = Signal(str)  # Emitted when Focus is removed (folder path)
    
    def __init__(self, tab_manager: TabManager, parent=None):
        """
        Initialize FocusManager with TabManager.
        
        Args:
            tab_manager: TabManager instance for tab operations.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._tab_manager = tab_manager
    
    def open_or_create_focus_for_path(self, path: str) -> None:
        """
        Open or create Focus (tab) for given folder path.
        
        Creates new tab if not exists, or activates existing one.
        Delegates to TabManager.add_tab() and emits focus_opened signal.
        
        Args:
            path: Folder path to open as Focus.
        """
        if not path:
            return
        
        self._tab_manager.add_tab(path)
        self.focus_opened.emit(path)
    
    def remove_focus(self, path: str) -> None:
        """
        Remove Focus (tab) for given folder path.
        
        Closes tab via TabManager.remove_tab_by_path() and emits focus_removed signal.
        Does NOT delete the folder from filesystem.
        
        Args:
            path: Folder path to remove from Focus.
        """
        if not path:
            return
        
        if self._tab_manager.remove_tab_by_path(path):
            self.focus_removed.emit(path)
    
    def open_focus(self, path: str) -> None:
        """Open or create Focus (tab) for given folder path."""
        if not path:
            return
        self.open_or_create_focus_for_path(path)
    
    def close_focus(self, tab_index: Optional[int] = None) -> None:
        """Close Focus (tab) by index or active tab."""
        if tab_index is None:
            tab_index = self._tab_manager.get_active_index()
        
        if tab_index < 0:
            return
        
        tabs = self._tab_manager.get_tabs()
        if not (0 <= tab_index < len(tabs)):
            return
        
        path = tabs[tab_index]
        self.remove_focus(path)
    
    def close_focus_by_path(self, path: str) -> None:
        """Close Focus (tab) by folder path."""
        if not path:
            return
        self.remove_focus(path)
    
    def reopen_last_focus(self) -> None:
        """Reopen last closed Focus from history if available."""
        history = self._tab_manager.get_history()
        if not history:
            return
        
        history_index = self._tab_manager.get_history_index()
        if history_index < 0 or history_index >= len(history):
            return
        
        last_path = history[history_index]
        self.open_focus(last_path)

