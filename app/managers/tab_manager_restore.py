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
    """
    Restore state from saved state without creating new history entries.
    
    REGLA OBLIGATORIA: Toda navegación a un path físico debe limpiar siempre el contexto de estado.
    """
    # REGLA OBLIGATORIA: Limpiar contexto de estado antes de restaurar paths físicos
    if hasattr(manager, '_current_state_context') and manager._current_state_context:
        manager.clear_state_context()
        # Restaurar modo del workspace al volver a carpeta normal
        if hasattr(manager, '_workspace_manager') and manager._workspace_manager:
            workspace_mode = manager._workspace_manager.get_view_mode()
            manager._current_view_mode = workspace_mode
            if hasattr(manager, 'view_mode_changed'):
                manager.view_mode_changed.emit(workspace_mode)
    
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

