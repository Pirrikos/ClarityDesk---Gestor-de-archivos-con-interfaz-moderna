"""
FileViewTabs - Tab synchronization for FileViewContainer.

Handles TabManager signal connections and tab change events.
"""

from app.managers.tab_manager import TabManager


def connect_tab_signals(container, tab_manager: TabManager) -> None:
    """Connect to TabManager signals."""
    tab_manager.activeTabChanged.connect(container._on_active_tab_changed)
    # files_changed solo para cambios en filesystem, NO para cambio de tab
    # Se mantiene para actualizar cuando los archivos cambian mientras estás en el mismo tab
    tab_manager.files_changed.connect(container._on_files_changed)
    tab_manager.focus_cleared.connect(container._on_focus_cleared)


def on_active_tab_changed(container, index: int, path: str) -> None:
    """Handle active tab change from TabManager - ÚNICA ruta de refresco al cambiar de tab."""
    # If no active tab (index == -1), clear the views
    if index < 0 or not path:
        container.clear_current_focus()
    else:
        # ÚNICA ruta de refresco al cambiar de tab
        container._update_files()
    container._update_nav_buttons_state()


def on_files_changed(container) -> None:
    """Handle filesystem change event - only refresh if already in a tab."""
    # Solo refrescar si hay un tab activo (no cuando se está cambiando de tab)
    # Esto evita doble refresh cuando watch_folder emite inmediatamente después de cambiar de tab
    if container._tab_manager.get_active_index() >= 0:
        container._update_files()


def update_nav_buttons_state(container) -> None:
    """Update navigation buttons enabled state based on TabManager history."""
    can_back = container._tab_manager.can_go_back()
    can_forward = container._tab_manager.can_go_forward()
    container._toolbar.set_nav_enabled(can_back, can_forward)


def on_nav_back(container) -> None:
    """Handle back navigation button click."""
    container._tab_manager.go_back()
    update_nav_buttons_state(container)


def on_nav_forward(container) -> None:
    """Handle forward navigation button click."""
    container._tab_manager.go_forward()
    update_nav_buttons_state(container)

