"""
GridTilePositions - Tile position calculation for grid layouts.

Handles column calculation, row/col positioning, and layout offsets.
"""

from PySide6.QtWidgets import QGridLayout

from app.ui.widgets.grid_tile_builder import create_file_tile, create_stack_tile


def calculate_columns_for_normal_grid(view_width: int) -> int:
    """
    Calculate number of columns for normal grid layout.
    
    Args:
        view_width: Width of the view widget.
        
    Returns:
        Number of columns that fit in the available width.
    """
    if view_width < 100:
        view_width = 800
    
    available_width = max(0, view_width - 40)
    tile_width = 70
    tile_spacing = 12
    return max(1, available_width // (tile_width + tile_spacing))


def get_col_offset_for_desktop_window(is_desktop_window: bool) -> int:
    """
    Get column offset based on window type.
    
    Args:
        is_desktop_window: True if DesktopWindow, False if Focus window.
        
    Returns:
        Column offset (3 for desktop, 0 for focus).
    """
    return 3 if is_desktop_window else 0


def calculate_expanded_file_position(
    file_idx: int,
    files_per_row: int,
    total_files: int,
    total_stacks: int,
    col_offset: int
) -> tuple[int, int]:
    """
    Calculate row and column position for expanded file tile.
    
    Args:
        file_idx: Index of file in expanded files list.
        files_per_row: Number of files per row.
        total_files: Total number of files.
        total_stacks: Total number of stacks.
        col_offset: Column offset based on window type.
        
    Returns:
        Tuple of (row, col) position.
    """
    file_row = file_idx // files_per_row
    file_col_in_row = file_idx % files_per_row
    
    files_in_this_row = min(files_per_row, total_files - (file_row * files_per_row))
    row_col_offset = (total_stacks - files_in_this_row) // 2
    file_col = row_col_offset + file_col_in_row + col_offset
    
    return file_row, file_col


def add_tile_to_normal_grid(
    view,
    items_to_render: list,
    grid_layout: QGridLayout,
    columns: int,
    col_offset: int
) -> None:
    """
    Add tiles to normal grid layout.
    
    Args:
        view: FileGridView instance.
        items_to_render: List of items (files or stacks) to render.
        grid_layout: Grid layout to add tiles to.
        columns: Number of columns in grid.
        col_offset: Column offset for positioning.
    """
    for idx, item in enumerate(items_to_render):
        if view._stacks:
            tile = create_stack_tile(item, view, view._icon_service)
            tile.stack_clicked.connect(view._on_stack_clicked)
            tile.open_file.connect(view.open_file.emit)
        else:
            tile = create_file_tile(
                item, view, view._icon_service, view._state_manager,
                dock_style=True
            )
        row = idx // columns
        col = (idx % columns) + col_offset
        grid_layout.addWidget(tile, row, col)

