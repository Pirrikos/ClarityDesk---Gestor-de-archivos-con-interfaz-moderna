"""
SearchManager - Manager for global workspace search.

Coordinates search mode state and emits signals to UI.
Separates search logic from UI. Executes searches off the UI thread.
"""

from PySide6.QtCore import QObject, Signal, QTimer
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, Future

from app.services.search_service import search_in_workspaces, SearchResult
from app.core.logger import get_logger


class SearchManager(QObject):
    """Manager for global workspace search."""
    
    search_mode_changed = Signal(bool)
    search_results_changed = Signal(list)
    
    def __init__(self, workspace_manager, tab_manager=None):
        super().__init__()
        self._workspace_manager = workspace_manager
        self._tab_manager = tab_manager
        self._is_search_mode = False
        self._current_query = ""
        self._current_results: List[SearchResult] = []
        self._cache: Dict[str, object] = {}
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1)
        self._current_future: Future | None = None
        self._last_request_id: int = 0
        self._logger = get_logger(__name__)
        
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
        self._last_request_id += 1
        request_id = self._last_request_id
        self._logger.info(f"search started | req={request_id} | query='{query}'")

        # Submit background search; we ignore stale results via request_id
        future = self._executor.submit(
            search_in_workspaces, query, self._workspace_manager, self._tab_manager, self._cache
        )
        self._current_future = future
        future.add_done_callback(lambda f, req=request_id: self._on_search_finished(req, f))

    def _on_search_finished(self, request_id: int, future: Future) -> None:
        """Handle completion of background search respecting request ordering."""
        if request_id != self._last_request_id:
            self._logger.info(f"search ignored (stale) | req={request_id} | last={self._last_request_id}")
            return
        try:
            results = future.result()
        except Exception as e:
            self._logger.error(f"search failed | req={request_id} | error={e}", exc_info=True)
            results = []

        # Emit results; Qt will queue cross-thread signals automatically because
        # SearchManager resides in the main thread.
        self._current_results = results
        self.search_results_changed.emit(results)
        self._logger.info(f"search completed | req={request_id} | results={len(results)}")
    
    def clear_search(self) -> None:
        """Clear search and return to previous context."""
        self._debounce_timer.stop()
        self._pending_query = ""
        
        if self._is_search_mode:
            self._is_search_mode = False
            self._current_query = ""
            self._current_results = []
            self.search_mode_changed.emit(False)
            # NO emitir search_results_changed aquí - ya se maneja con search_mode_changed(False)
    
    def is_search_mode(self) -> bool:
        """Check if in search mode."""
        return self._is_search_mode
    
    def get_current_results(self) -> List[SearchResult]:
        """Get current results."""
        return self._current_results.copy()

