"""
FocusDockWidget - Vertical dock widget for Focus tiles.

Displays list of Focus tiles with scroll support.
Integrates with TabManager to show and manage Focus tabs.
"""

from typing import Optional

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.managers.tab_manager import TabManager
from app.services.icon_service import IconService
from app.ui.widgets.focus_stack_tile import FocusStackTile
from app.ui.widgets.subfolder_overlay import SubfolderOverlay
from app.ui.widgets.focus_dock_layout import (
    setup_dock_widget,
    setup_buttons,
    setup_scroll_area,
    setup_tiles_container
)
from app.ui.widgets.focus_dock_update_helpers import (
    remove_old_tiles,
    create_new_tile,
    update_container_size,
    force_widget_update
)
from app.ui.widgets.focus_dock_handlers import (
    handle_focus_click,
    handle_add_click,
    handle_remove_click,
    handle_focus_remove_request,
    handle_overlay_request,
    handle_file_dropped_in_overlay
)


class FocusDockWidget(QWidget):
    """Vertical dock widget displaying Focus tiles."""

    focus_selected = Signal(str)  # Emitted when Focus is clicked (folder_path)
    focus_added = Signal(str)  # Emitted when + button is clicked (folder_path)
    files_dropped_on_focus = Signal(str, list)  # Emitted when files dropped (folder_path, file_paths)

    def __init__(
        self,
        tab_manager: TabManager,
        icon_service: IconService,
        parent=None
    ):
        """Initialize Focus dock widget."""
        super().__init__(parent)
        self._tab_manager = tab_manager
        self._icon_service = icon_service
        self._tiles: dict[str, FocusStackTile] = {}
        self._overlay: Optional[SubfolderOverlay] = None
        self._setup_ui()
        self._connect_tab_manager()

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        setup_dock_widget(self)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 6, 6)
        layout.setSpacing(4)
        
        self._add_button, self._remove_button, buttons_layout = setup_buttons()
        self._add_button.clicked.connect(self._on_add_clicked)
        self._remove_button.clicked.connect(self._on_remove_clicked)
        layout.addLayout(buttons_layout)
        
        scroll_area = setup_scroll_area(self)
        self._tiles_container, self._tiles_layout = setup_tiles_container(self)
        scroll_area.setWidget(self._tiles_container)
        layout.addWidget(scroll_area, 1)
        
        self.raise_()

    def _connect_tab_manager(self) -> None:
        """Connect to TabManager signals."""
        self._tab_manager.tabsChanged.connect(self._on_tabs_changed)
        self._tab_manager.activeTabChanged.connect(self._on_active_tab_changed)
        # Initial update
        self._update_tiles()
        self._update_remove_button_state()

    def _on_tabs_changed(self, tabs: list) -> None:
        """Handle tabs list change from TabManager."""
        # Use the tabs from the signal, not get_tabs() which might be stale
        self._update_tiles(tabs=tabs)
        self._update_remove_button_state()

    def _on_active_tab_changed(self, index: int, path: str) -> None:
        """Handle active tab change from TabManager."""
        self._update_active_state()

    def _update_tiles(self, tabs: list = None) -> None:
        """Update tiles based on current tabs."""
        if tabs is None:
            tabs = self._tab_manager.get_tabs()
        active_index = self._tab_manager.get_active_index()
        active_path = tabs[active_index] if 0 <= active_index < len(tabs) else None
        
        self._remove_old_tiles(tabs)
        self._create_new_tiles(tabs, active_path)
        update_container_size(self._tiles_container, len(tabs))
        
        self._update_active_state()
        force_widget_update(self._tiles_container)
        force_widget_update(self)
    
    def _remove_old_tiles(self, tabs: list) -> None:
        """Remove tiles for tabs that no longer exist."""
        current_paths = set(tabs)
        remove_old_tiles(self._tiles, current_paths)
    
    def _create_new_tiles(self, tabs: list, active_path: str) -> None:
        """Create or update tiles for current tabs."""
        for idx, folder_path in enumerate(tabs):
            is_active = (folder_path == active_path)
            if folder_path in self._tiles:
                self._tiles[folder_path].set_active(is_active)
            else:
                tile = create_new_tile(
                    folder_path,
                    is_active,
                    self._tiles_container,
                    self._icon_service
                )
                tile.focus_clicked.connect(self._on_focus_clicked)
                tile.overlay_requested.connect(self._on_overlay_requested)
                tile.focus_remove_requested.connect(self._on_focus_remove_requested)
                self._tiles[folder_path] = tile
                self._tiles_layout.insertWidget(idx, tile)
                force_widget_update(tile)

    def _update_active_state(self) -> None:
        """Update active state of all tiles."""
        tabs = self._tab_manager.get_tabs()
        active_index = self._tab_manager.get_active_index()
        active_path = tabs[active_index] if 0 <= active_index < len(tabs) else None
        
        for folder_path, tile in self._tiles.items():
            is_active = (folder_path == active_path)
            tile.set_active(is_active)

    def _on_focus_clicked(self, folder_path: str) -> None:
        """Handle Focus tile click - switch to that Focus."""
        handle_focus_click(self._tab_manager, folder_path)
        self.focus_selected.emit(folder_path)

    def _on_add_clicked(self) -> None:
        """Handle + button click - open folder picker."""
        folder_path = handle_add_click(self._tab_manager)
        if folder_path:
            self.focus_added.emit(folder_path)
    
    def _on_remove_clicked(self) -> None:
        """Handle - button click - remove active tab."""
        handle_remove_click(self._tab_manager)
    
    def _on_focus_remove_requested(self, folder_path: str) -> None:
        """Handle remove request from a Focus tile."""
        handle_focus_remove_request(self._tab_manager, folder_path)
    
    def _update_remove_button_state(self) -> None:
        """Update remove button enabled state based on number of tabs."""
        tabs = self._tab_manager.get_tabs()
        # Disable if no tabs or only one tab remaining
        self._remove_button.setEnabled(len(tabs) > 1)

    def _on_overlay_requested(self, folder_path: str, global_pos: QPoint) -> None:
        """Handle overlay request - show subfolder overlay."""
        self._overlay = handle_overlay_request(
            folder_path,
            global_pos,
            self._overlay,
            self
        )
        self._overlay.file_dropped.connect(self._on_file_dropped_in_overlay)
        self._overlay.show_at_position(global_pos)
    
    def close_overlay(self) -> None:
        """Close overlay if open."""
        if self._overlay:
            self._overlay.close()
            self._overlay = None

    def _on_file_dropped_in_overlay(self, source_path: str, target_path: str) -> None:
        """Handle file drop in overlay - move file using file_move_service."""
        handle_file_dropped_in_overlay(
            source_path,
            target_path,
            self._tab_manager
        )
    
    # No custom paintEvent - let Qt handle background via QPalette

