"""
State restoration helpers for TabManager.

Handles restoring TabManager state from saved state.
"""

from typing import List, Optional

from app.managers.tab_manager_state import restore_state as state_restore_state


def restore_tab_manager_state(
    manager,
    tabs: List[str],
    active_tab_path: Optional[str],
    history: List[str],
    history_index: int,
    history_manager,
    watcher,
    watch_and_emit_callback,
    tabs_changed_signal,
    active_tab_changed_signal
) -> tuple[List[str], int]:
    """Restore state from saved state without creating new history entries."""
    new_tabs, new_active_index = state_restore_state(
        tabs,
        active_tab_path,
        history,
        history_index,
        history_manager,
        watcher,
        watch_and_emit_callback,
        tabs_changed_signal,
        active_tab_changed_signal
    )
    return new_tabs, new_active_index

