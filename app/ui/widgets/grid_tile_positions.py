"""
GridTilePositions - Tile position calculation for grid layouts.

Handles column calculation, row/col positioning, and layout offsets.
"""

from typing import List, Tuple, Union, TYPE_CHECKING

from PySide6.QtWidgets import QGridLayout


if TYPE_CHECKING:
    from app.ui.widgets.file_grid_view import FileGridView

TILE_WIDTH = 70
TILE_SPACING = 12
GRID_HORIZONTAL_MARGIN = 40


def calculate_columns_for_normal_grid(view_width: int) -> int:
    """
    Calculate number of columns for normal grid layout.
    
    Args:
        view_width: Width of the view widget (must be > 0).
        
    Returns:
        Number of columns that fit in the available width.
        Returns 0 if width is insufficient for at least 2 columns (avoids columns=1 provisional layout).
    """
    available_width = max(0, view_width - GRID_HORIZONTAL_MARGIN)
    
    # Calcular columnas sin fallback a 1
    # Si el ancho no es suficiente para al menos 2 columnas, retornar 0
    # Esto evita construcción con columns=1 que causa salto visual vertical→horizontal
    tile_unit_width = TILE_WIDTH + TILE_SPACING  # 82px
    min_width_for_2_columns = 2 * tile_unit_width  # 164px
    
    if available_width < min_width_for_2_columns:
        return 0  # Ancho insuficiente, evitar construcción con columns=1
    
    columns = available_width // tile_unit_width
    return columns


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

