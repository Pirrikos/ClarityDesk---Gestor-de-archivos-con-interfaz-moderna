"""
TabManagerState - State management for TabManager.

Handles loading, saving, and restoring tab state.
"""

from typing import List, Optional

from app.services.tab_finder import find_tab_index
from app.services.tab_path_normalizer import normalize_path


def load_state(state_manager, history_manager) -> tuple[List[str], int, bool]:
    """
    Load tabs and active index from JSON storage.
    
    Args:
        state_manager: TabStateManager instance.
        history_manager: TabHistoryManager instance.
    
    Returns:
        Tuple of (tabs list, active_index, needs_save).
    """
    tabs, active_index, needs_save = state_manager.load_tabs_and_index()
    
    if 0 <= active_index < len(tabs):
        active_folder = tabs[active_index]
        history_manager.initialize_with_path(active_folder)
    
    return tabs, active_index, needs_save


def save_state(state_manager, tabs: List[str], active_index: int) -> None:
    """Save tabs and active index to JSON storage."""
    state_manager.save_tabs_and_index(tabs, active_index)


def restore_state(
    tabs: List[str],
    active_tab_path: Optional[str],
    history: List[str],
    history_index: int,
    history_manager,
    watcher,
    watch_and_emit_func,
    tabs_changed_signal,
    active_tab_changed_signal
) -> tuple[List[str], int]:
    """
    Restore state from saved state without creating new history entries.
    
    Args:
        tabs: List of tab paths to restore.
        active_tab_path: Active tab path (or None).
        history: Navigation history to restore.
        history_index: History index to restore to.
        history_manager: TabHistoryManager instance.
        watcher: FileSystemWatcherService instance.
        watch_and_emit_func: Function to watch folder and emit signal.
        tabs_changed_signal: Signal to emit tabs changed.
        active_tab_changed_signal: Signal to emit active tab changed.
    
    Returns:
        Tuple of (restored_tabs, active_index).
    """
    history_manager.set_navigating_flag(True)
    try:
        restored_tabs = tabs.copy()
        history_manager.restore_history(history, history_index)
        
        if active_tab_path:
            tab_index = find_tab_index(restored_tabs, active_tab_path)
            if tab_index is not None:
                active_index = tab_index
                watcher.stop_watching()
                watch_and_emit_func(active_tab_path)
            else:
                active_index = -1
        else:
            active_index = -1
        
        tabs_changed_signal.emit(restored_tabs.copy())
        if active_index >= 0:
            active_tab_changed_signal.emit(active_index, restored_tabs[active_index])
        
        return restored_tabs, active_index
    finally:
        history_manager.set_navigating_flag(False)

