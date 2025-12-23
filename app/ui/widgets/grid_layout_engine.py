"""
GridLayoutEngine - Layout building for FileGridView.

Handles dock-style and normal grid layout construction.

This module orchestrates layout building by delegating to:
- grid_tile_positions.py: Position calculation
- grid_tile_animations.py: Tile animations
- grid_layout_config.py: Layout configuration
"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout

from app.ui.widgets.desktop_stack_tile import DesktopStackTile
from app.ui.widgets.dock_separator import DockSeparator
from app.ui.widgets.grid_layout_config import (
    setup_dock_layout_config,
    setup_normal_grid_config,
    calculate_expansion_height
)
from app.ui.widgets.grid_tile_animations import (
    animate_old_tiles_exit,
    animate_tiles_entrance
)
from app.ui.widgets.grid_tile_positions import (
    calculate_columns_for_normal_grid,
    get_col_offset_for_desktop_window,
    calculate_expanded_file_position,
    add_tile_to_normal_grid
)
from app.ui.widgets.grid_tile_builder import create_file_tile, create_stack_tile
from app.ui.widgets.settings_stack_tile import SettingsStackTile


def _connect_desktop_tile_signals(desktop_tile: DesktopStackTile, view) -> None:
    """Connect desktop tile click to DesktopWindow's open_main_window signal."""
    parent = view.parent()
    while parent:
        if parent.__class__.__name__ == 'DesktopWindow':
            desktop_tile.clicked.connect(parent.open_main_window.emit)
            return
        parent = parent.parent()


def build_dock_layout(
    view,
    items_to_render: list,
    old_expanded_tiles_to_animate: dict,
    grid_layout: QGridLayout
) -> None:
    """Build Dock-style layout with stacks and expanded files."""
    _emit_expansion_height(view)
    setup_dock_layout_config(grid_layout)
    
    # Deshabilitar updates durante construcción masiva para evitar repaints redundantes
    content_widget = view._content_widget
    updates_enabled = content_widget.updatesEnabled()
    try:
        content_widget.setUpdatesEnabled(False)
        animate_old_tiles_exit(view, old_expanded_tiles_to_animate)
        stack_col_map = _build_stack_tiles(view, items_to_render, grid_layout)
        _build_expanded_files(view, stack_col_map, grid_layout)
    finally:
        content_widget.setUpdatesEnabled(updates_enabled)


def build_normal_grid(view, items_to_render: list, grid_layout: QGridLayout) -> None:
    """Build normal grid layout for non-Dock windows."""
    _emit_expansion_height(view)
    setup_normal_grid_config(grid_layout)
    
    col_offset = get_col_offset_for_desktop_window(view._is_desktop_window)
    
    # Cache de cálculo de columnas: solo recalcular si cambio significativo (>10px)
    current_width = view.width()
    if (view._cached_columns is None or 
        view._cached_width is None or 
        abs(current_width - view._cached_width) > 10):
        view._cached_columns = calculate_columns_for_normal_grid(current_width)
        view._cached_width = current_width
    
    columns = view._cached_columns
    
    # Deshabilitar updates durante construcción masiva para evitar repaints redundantes
    content_widget = view._content_widget
    updates_enabled = content_widget.updatesEnabled()
    try:
        content_widget.setUpdatesEnabled(False)
        add_tile_to_normal_grid(view, items_to_render, grid_layout, columns, col_offset)
    finally:
        content_widget.setUpdatesEnabled(updates_enabled)


def _build_stack_tiles(view, items_to_render: list, grid_layout: QGridLayout) -> dict:
    """Build stack tiles and return column map."""
    stack_col_map = {}
    stack_row = 0
    col_offset = get_col_offset_for_desktop_window(view._is_desktop_window)
    
    if view._is_desktop_window:
        desktop_tile = DesktopStackTile(view)
        _connect_desktop_tile_signals(desktop_tile, view)
        grid_layout.addWidget(desktop_tile, stack_row, 0)
        
        settings_tile = SettingsStackTile(view)
        grid_layout.addWidget(settings_tile, stack_row, 1)
        
        separator = DockSeparator(view)
        grid_layout.addWidget(separator, stack_row, 2)
        
        col_offset = 3
    
    for idx, item in enumerate(items_to_render):
        col = idx + col_offset
        if view._stacks:
            stack = item
            tile = create_stack_tile(stack, view, view._icon_service)
            tile.stack_clicked.connect(view._on_stack_clicked)
            tile.open_file.connect(view.open_file.emit)
            grid_layout.addWidget(tile, stack_row, col)
            stack_col_map[stack.stack_type] = col
            QTimer.singleShot(0, tile.update_badge_count)
        else:
            tile = create_file_tile(
                item, view, view._icon_service, view._state_manager,
                dock_style=view._is_desktop_window
            )
            grid_layout.addWidget(tile, stack_row, col)
    
    return stack_col_map


def _build_expanded_files(view, stack_col_map: dict, grid_layout: QGridLayout) -> None:
    """Build expanded files grid below stacks."""
    if not (view._stacks and view._expanded_stacks):
        return
    
    total_stacks = len(view._stacks)
    old_expanded_tiles = view._expanded_file_tiles.copy()
    view._expanded_file_tiles = {}
    
    col_offset = get_col_offset_for_desktop_window(view._is_desktop_window)
    
    for stack_type, expanded_files in view._expanded_stacks.items():
        if stack_type in stack_col_map:
            stack_tiles = _create_expanded_file_tiles(
                view, expanded_files, total_stacks, stack_col_map[stack_type],
                col_offset, grid_layout
            )
            view._expanded_file_tiles[stack_type] = stack_tiles
            animate_tiles_entrance(stack_tiles)


def _create_expanded_file_tiles(
    view,
    expanded_files: list,
    total_stacks: int,
    stack_col: int,
    col_offset: int,
    grid_layout: QGridLayout
) -> list:
    """Create file tiles for expanded stack and add to layout."""
    total_files = len(expanded_files)
    files_per_row = min(total_files, total_stacks)
    stack_tiles = []
    stack_row = 0
    
    for file_idx, file_path in enumerate(expanded_files):
        file_tile = create_file_tile(
            file_path, view, view._icon_service, view._state_manager,
            dock_style=view._is_desktop_window
        )
        file_row, file_col = calculate_expanded_file_position(
            file_idx, files_per_row, total_files, total_stacks, col_offset
        )
        
        grid_layout.addWidget(file_tile, stack_row + 1 + file_row, file_col)
        stack_tiles.append(file_tile)
    
    return stack_tiles


def _emit_expansion_height(view) -> None:
    """Calculate and emit the height needed for expanded stacks."""
    height = calculate_expansion_height(
        view._is_desktop_window,
        view._stacks,
        view._expanded_stacks
    )
    view.expansion_height_changed.emit(height)
