"""
GridLayoutEngine - Layout building for FileGridView.

Handles dock-style and normal grid layout construction.

This module orchestrates layout building by delegating to:
- grid_state_model.py: State calculation and diff
- grid_tile_manager.py: Tile lifecycle management
- grid_tile_positions.py: Position calculation
- grid_tile_animations.py: Tile animations
- grid_layout_config.py: Layout configuration
"""

from typing import Dict, List, Tuple, Union, TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout

from app.models.file_stack import FileStack
from app.ui.widgets.desktop_stack_tile import DesktopStackTile
from app.ui.widgets.dock_separator import DockSeparator
from app.ui.widgets.grid_layout_config import (
    setup_dock_layout_config,
    setup_normal_grid_config,
    calculate_expansion_height
)
from app.ui.widgets.grid_state_model import GridStateModel, GridDiff
from app.ui.widgets.grid_tile_animations import (
    animate_old_tiles_exit,
    animate_tiles_entrance
)
from app.ui.widgets.grid_tile_positions import (
    calculate_columns_for_normal_grid,
    get_col_offset_for_desktop_window,
    calculate_expanded_file_position
)
from app.ui.widgets.grid_tile_builder import create_file_tile, create_stack_tile
from app.ui.widgets.settings_stack_tile import SettingsStackTile

if TYPE_CHECKING:
    from app.ui.widgets.file_grid_view import FileGridView


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


def build_normal_grid(view: 'FileGridView', items_to_render: list, grid_layout: QGridLayout) -> None:
    """
    Build normal grid layout for non-Dock windows using state-based incremental updates.
    
    Uses GridStateModel to calculate diffs and TileManager for lifecycle management.
    """
    current_width = view.width()
    
    # Posponer cálculo de layout hasta que el widget tenga ancho válido
    # Evita layout inicial con ancho provisional que causa salto visual
    if current_width <= 0:
        # Ancho inválido: no construir layout, se construirá en resizeEvent
        return
    
    _emit_expansion_height(view)
    setup_normal_grid_config(grid_layout)
    
    col_offset = get_col_offset_for_desktop_window(view._is_desktop_window)
    
    # Cache de cálculo de columnas: solo recalcular si cambio significativo (>10px)
    if (view._cached_columns is None or 
        view._cached_width is None or 
        abs(current_width - view._cached_width) > 10):
        view._cached_columns = calculate_columns_for_normal_grid(current_width)
        view._cached_width = current_width
    
    columns = view._cached_columns
    
    # Verificar que columns es válido antes de continuar
    # Evita usar columnas inválidas que causan cálculo incorrecto de posiciones
    if columns is None or columns <= 0:
        return
    
    # Convert items to ordered tile_ids
    is_categorized = items_to_render and isinstance(items_to_render[0], tuple) if items_to_render and len(items_to_render) > 0 else False
    
    if is_categorized:
        # For categorized files, calculate positions accounting for headers
        ordered_ids, header_rows = _items_to_tile_ids_with_headers(items_to_render, columns)
        # Calculate positions with headers accounted for
        new_state_with_headers = _calculate_positions_with_headers(ordered_ids, header_rows, items_to_render, columns)
    else:
        ordered_ids = _items_to_tile_ids(items_to_render, view)
        header_rows = []
        # Calculate positions without headers
        new_state_with_headers = {}
        for index, tile_id in enumerate(ordered_ids):
            row = index // columns
            col = index % columns
            new_state_with_headers[tile_id] = (row, col)
    
    # Get old state (may have headers, we'll compare positions directly)
    old_state = getattr(view, '_grid_state', {}) or {}
    
    # Calculate diffs by comparing states
    old_ids = set(old_state.keys())
    new_ids = set(new_state_with_headers.keys())
    
    added = list(new_ids - old_ids)
    removed = list(old_ids - new_ids)
    
    moved = {}
    unchanged = []
    
    for tile_id in old_ids & new_ids:
        old_pos = old_state[tile_id]
        new_pos = new_state_with_headers[tile_id]
        if old_pos == new_pos:
            unchanged.append(tile_id)
        else:
            moved[tile_id] = (old_pos, new_pos)
    
    # Create diff object
    diff = GridDiff(
        added=added,
        removed=removed,
        moved=moved,
        unchanged=unchanged,
        new_state=new_state_with_headers
    )
    
    # Get tile manager
    tile_manager = view._tile_manager
    
    # Deshabilitar updates durante construcción masiva para evitar repaints redundantes
    content_widget = view._content_widget
    updates_enabled = content_widget.updatesEnabled()
    try:
        content_widget.setUpdatesEnabled(False)
        
        # Añadir headers ANTES de los tiles para evitar reflow del layout
        # Esto asegura que el layout se calcule correctamente desde el inicio
        if is_categorized and header_rows:
            _add_category_headers_at_rows(view, items_to_render, grid_layout, header_rows, columns, col_offset)
        
        # Apply changes incrementally
        # 1. Detach removed + moved
        for tile_id in diff.removed + list(diff.moved.keys()):
            tile = tile_manager.get_tile(tile_id)
            if tile:
                tile_manager.detach(tile)
        
        # 2. Destroy removed
        for tile_id in diff.removed:
            tile_manager.destroy(tile_id)
        
        # 3. Attach unchanged (same position)
        for tile_id in diff.unchanged:
            tile = tile_manager.get_or_create(tile_id)
            row, col = diff.new_state[tile_id]
            # Add col_offset for positioning
            tile_manager.attach(tile, row, col + col_offset)
        
        # 4. Attach moved (new position)
        for tile_id, (old_pos, new_pos) in diff.moved.items():
            tile = tile_manager.get_or_create(tile_id)
            row, col = new_pos
            tile_manager.attach(tile, row, col + col_offset)
        
        # 5. Create + attach added
        for tile_id in diff.added:
            tile = tile_manager.get_or_create(tile_id)
            row, col = diff.new_state[tile_id]
            tile_manager.attach(tile, row, col + col_offset)
        
    finally:
        content_widget.setUpdatesEnabled(updates_enabled)
    
    # Forzar cálculo del layout antes de revelar tiles
    # Esto asegura que las posiciones estén correctas desde el primer frame
    # Evita salto visual de vertical a horizontal
    grid_layout.activate()
    content_widget.updateGeometry()
    
    # Update state
    view._grid_state = diff.new_state


def _items_to_tile_ids(
    items_to_render: Union[List[str], List[FileStack], List[Tuple[str, List[str]]]],
    view: 'FileGridView'
) -> List[str]:
    """
    Convert items to ordered list of tile_ids.
    
    Args:
        items_to_render: List of files, stacks, or categorized tuples
        view: FileGridView instance
        
    Returns:
        Ordered list of tile_ids (file_path or f"stack:{stack_type}")
    """
    tile_ids = []
    
    if not items_to_render:
        return tile_ids
    
    # Check if categorized (list of tuples)
    if isinstance(items_to_render[0], tuple):
        # Categorized files: (category_label, files)
        for category_label, files in items_to_render:
            # Add file paths (headers are handled separately)
            tile_ids.extend(files)
    elif isinstance(items_to_render[0], FileStack):
        # Stacks
        for stack in items_to_render:
            tile_ids.append(f"stack:{stack.stack_type}")
    else:
        # Plain file list
        tile_ids.extend(items_to_render)
    
    return tile_ids


def _items_to_tile_ids_with_headers(
    items_to_render: List[Tuple[str, List[str]]],
    columns: int
) -> Tuple[List[str], List[int]]:
    """
    Convert categorized items to tile_ids, tracking header positions.
    
    Returns:
        Tuple of (ordered_tile_ids, header_rows)
    """
    tile_ids = []
    header_rows = []
    current_row = 0
    
    for category_label, files in items_to_render:
        if not files:  # Skip empty categories
            continue
        
        # Header goes at current_row
        header_rows.append(current_row)
        current_row += 1
        
        # Files go after header
        tile_ids.extend(files)
        
        # Calculate rows needed for this category (without header)
        files_rows = (len(files) + columns - 1) // columns
        current_row += files_rows
    
    return tile_ids, header_rows


def _calculate_positions_with_headers(
    ordered_ids: List[str],
    header_rows: List[int],
    items_to_render: List[Tuple[str, List[str]]],
    columns: int
) -> Dict[str, Tuple[int, int]]:
    """
    Calculate tile positions accounting for category headers.
    
    Headers are inserted at header_rows, so tiles need their row adjusted.
    """
    state = {}
    category_index = 0
    
    for category_label, files in items_to_render:
        if not files:
            continue
        
        # Header is at header_rows[category_index]
        header_row = header_rows[category_index]
        # Tiles start at row after header
        tile_start_row = header_row + 1
        
        # Calculate positions for files in this category
        for file_idx, file_path in enumerate(files):
            # Position within category (0-based)
            row_in_category = file_idx // columns
            col_in_category = file_idx % columns
            
            # Final position: tile_start_row + row_in_category
            final_row = tile_start_row + row_in_category
            final_col = col_in_category
            
            state[file_path] = (final_row, final_col)
        
        category_index += 1
    
    return state


def _add_category_headers_at_rows(
    view: 'FileGridView',
    items_to_render: List[Tuple[str, List[str]]],
    grid_layout: QGridLayout,
    header_rows: List[int],
    columns: int,
    col_offset: int
) -> None:
    """
    Add category section headers at specified rows.
    
    First removes any existing headers to avoid duplicates.
    
    Args:
        view: FileGridView instance
        items_to_render: List of (category_label, files) tuples
        grid_layout: Grid layout
        header_rows: List of row numbers where headers should be placed
        columns: Number of columns
        col_offset: Column offset
    """
    from app.ui.widgets.category_section_header import CategorySectionHeader
    
    # Remove existing headers first to avoid duplicates
    _remove_existing_headers(grid_layout)
    
    category_idx = 0
    for category_label, files in items_to_render:
        if not files:  # Skip empty categories
            continue
        
        if category_idx < len(header_rows):
            header_row = header_rows[category_idx]
            header = CategorySectionHeader(category_label, view._content_widget)
            grid_layout.addWidget(header, header_row, col_offset, 1, columns)
            category_idx += 1


def _remove_existing_headers(grid_layout: QGridLayout) -> None:
    """
    Remove all existing CategorySectionHeader widgets from grid layout.
    
    Args:
        grid_layout: Grid layout to clean
    """
    from app.ui.widgets.category_section_header import CategorySectionHeader
    
    # Collect headers to remove (process in reverse to avoid index issues)
    headers_to_remove = []
    for i in range(grid_layout.count()):
        item = grid_layout.itemAt(i)
        if item and item.widget():
            widget = item.widget()
            if isinstance(widget, CategorySectionHeader):
                headers_to_remove.append(widget)
    
    # Remove headers
    for header in headers_to_remove:
        grid_layout.removeWidget(header)
        # Eliminar directamente sin cambiar parent para evitar top-level temporal
        header.deleteLater()


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
