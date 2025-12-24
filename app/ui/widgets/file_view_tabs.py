"""
FileViewTabs - Tab synchronization for FileViewContainer.

Handles TabManager signal connections and tab change events.
"""

from app.managers.tab_manager import TabManager
from app.ui.widgets.file_view_sync import update_files


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
        # Reset views before loading new folder to avoid residual selections/expansions
        # skip_render=True evita renderizar vacío antes de cargar nuevos datos
        container.clear_current_focus(skip_render=True)
        # ÚNICA ruta de refresco al cambiar de tab
        # Actualizar breadcrumb con la ruta activa
        if hasattr(container, "_focus_panel") and hasattr(container._focus_panel, "update_path"):
            container._focus_panel.update_path(path)
        update_files(container)
        # Animación de transición suave (<300ms)
        if hasattr(container, "_animate_content_transition"):
            container._animate_content_transition()
    container._update_nav_buttons_state()


def on_files_changed(container) -> None:
    """Handle filesystem change event - only refresh if already in a tab."""
    # Solo refrescar si hay un tab activo (no cuando se está cambiando de tab)
    # Esto evita doble refresh cuando watch_folder emite inmediatamente después de cambiar de tab
    if container._tab_manager.get_active_index() >= 0:
        update_files(container)


def update_nav_buttons_state(container) -> None:
    """Update navigation buttons enabled state based on TabManager history."""
    can_back = container._tab_manager.can_go_back()
    can_forward = container._tab_manager.can_go_forward()
    # Buscar target: toolbar interna > workspace_selector > header
    target = None
    if hasattr(container, "_toolbar") and container._toolbar:
        target = container._toolbar
    elif hasattr(container, "_workspace_selector") and container._workspace_selector and hasattr(container._workspace_selector, "set_nav_enabled"):
        target = container._workspace_selector
    elif hasattr(container, "_header") and container._header and hasattr(container._header, "set_nav_enabled"):
        target = container._header
    if target:
        target.set_nav_enabled(can_back, can_forward)


def on_nav_back(container) -> None:
    """Handle back navigation button click."""
    container._tab_manager.go_back()
    update_nav_buttons_state(container)


def on_nav_forward(container) -> None:
    """Handle forward navigation button click."""
    container._tab_manager.go_forward()
    update_nav_buttons_state(container)

