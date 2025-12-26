"""
SearchManager - Manager for global workspace search.

Coordinates search mode state and emits signals to UI.
Separates search logic from UI.
"""

from PySide6.QtCore import QObject, Signal, QTimer
from typing import List

from app.services.search_service import search_in_workspaces, SearchResult


class SearchManager(QObject):
    """Manager for global workspace search."""
    
    search_mode_changed = Signal(bool)
    search_results_changed = Signal(list)
    
    def __init__(self, workspace_manager):
        super().__init__()
        self._workspace_manager = workspace_manager
        self._is_search_mode = False
        self._current_query = ""
        self._current_results: List[SearchResult] = []
        
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._execute_search)
        self._pending_query = ""
    
    def search(self, query: str) -> None:
        """
        Execute search with debounce.
        
        Args:
            query: Text to search
        """
        self._pending_query = query.strip()
        
        if not self._pending_query:
            self.clear_search()
            return
        
        if not self._is_search_mode:
            self._is_search_mode = True
            self.search_mode_changed.emit(True)
        
        self._debounce_timer.stop()
        self._debounce_timer.start(300)
    
    def _execute_search(self) -> None:
        """Execute actual search (called by debounce timer)."""
        query = self._pending_query
        if not query:
            return
        
        self._current_query = query
        results = search_in_workspaces(query, self._workspace_manager)
        self._current_results = results
        self.search_results_changed.emit(results)
    
    def clear_search(self) -> None:
        """Clear search and return to previous context."""
        self._debounce_timer.stop()
        self._pending_query = ""
        
        if self._is_search_mode:
            self._is_search_mode = False
            self._current_query = ""
            self._current_results = []
            self.search_mode_changed.emit(False)
            self.search_results_changed.emit([])
    
    def is_search_mode(self) -> bool:
        """Check if in search mode."""
        return self._is_search_mode
    
    def get_current_results(self) -> List[SearchResult]:
        """Get current results."""
        return self._current_results.copy()

