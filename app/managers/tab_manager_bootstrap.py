"""
Initialization helpers for TabManager.

Handles TabManager initialization and setup.
"""

from typing import Optional

from app.services.tab_history_manager import TabHistoryManager
from app.services.tab_state_manager import TabStateManager


def initialize_tab_manager(
    manager,
    storage_path: Optional[str] = None,
    load_state_callback=None,
    watch_and_emit_callback=None
) -> tuple[TabHistoryManager, TabStateManager, object]:
    """
    Initialize TabManager components.
    
    Returns:
        Tuple of (history_manager, state_manager, watcher)
    """
    manager._tabs: list = []
    manager._active_index: int = -1
    history_manager = TabHistoryManager()

    from app.services.tab_state_initializer import get_storage_path, setup_watcher_and_timer
    
    storage_path_obj = get_storage_path(storage_path)
    state_manager = TabStateManager(storage_path_obj)
    watcher, _, _ = setup_watcher_and_timer(manager)
    
    # Assign managers to instance BEFORE calling load_state_callback
    manager._history_manager = history_manager
    manager._state_manager = state_manager
    manager._watcher = watcher  # Assign watcher BEFORE calling watch_and_emit_callback
    
    # Load basic state (tabs and active_index) - will be overridden by MainWindow if full state exists
    load_state_callback()
    
    # Watch active folder if exists
    if 0 <= manager._active_index < len(manager._tabs):
        active_folder = manager._tabs[manager._active_index]
        if active_folder:
            watch_and_emit_callback(active_folder)
    
    return history_manager, state_manager, watcher
