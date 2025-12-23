"""
GridTilePositions - Tile position calculation for grid layouts.

Handles column calculation, row/col positioning, and layout offsets.
"""

from typing import List, Tuple, Union

from PySide6.QtWidgets import QGridLayout

from app.ui.widgets.category_section_header import CategorySectionHeader
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
    items_to_render: Union[list, List[Tuple[str, List[str]]]],
    grid_layout: QGridLayout,
    columns: int,
    col_offset: int
) -> None:
    """
    Add tiles to normal grid layout.
    
    Args:
        view: FileGridView instance.
        items_to_render: List of items (files or stacks) OR list of (category_label, files) tuples.
        grid_layout: Grid layout to add tiles to.
        columns: Number of columns in grid.
        col_offset: Column offset for positioning.
    """
    current_row = 0
    
    # Si items_to_render es una lista de tuplas (categorías), renderizar con secciones
    if items_to_render and isinstance(items_to_render[0], tuple):
        for category_label, files in items_to_render:
            # Agregar header de sección
            header = CategorySectionHeader(category_label, view._content_widget)
            grid_layout.addWidget(header, current_row, col_offset, 1, columns)
            current_row += 1
            
            # Agregar tiles de archivos de esta categoría
            for idx, file_path in enumerate(files):
                # Reutilizar tile del cache si existe, sino crear nuevo
                if file_path in view._tile_cache:
                    tile = view._tile_cache[file_path]
                    # Resetear estado visual (selección, animaciones)
                    tile.set_selected(False)
                    tile.setParent(view._content_widget)
                else:
                    tile = create_file_tile(
                        file_path, view, view._icon_service, view._state_manager,
                        dock_style=view._is_desktop_window
                    )
                    view._tile_cache[file_path] = tile
                file_row = idx // columns
                file_col = (idx % columns) + col_offset
                grid_layout.addWidget(tile, current_row + file_row, file_col)
            
            # Avanzar a la siguiente fila después de esta categoría
            files_rows = (len(files) + columns - 1) // columns  # Ceiling division
            current_row += files_rows
    else:
        # Renderizado normal sin categorías
        for idx, item in enumerate(items_to_render):
            if view._stacks:
                tile = create_stack_tile(item, view, view._icon_service)
                tile.stack_clicked.connect(view._on_stack_clicked)
                tile.open_file.connect(view.open_file.emit)
            else:
                # Reutilizar tile del cache si existe, sino crear nuevo
                if item in view._tile_cache:
                    tile = view._tile_cache[item]
                    # Resetear estado visual (selección, animaciones)
                    tile.set_selected(False)
                    tile.setParent(view._content_widget)
                else:
                    tile = create_file_tile(
                        item, view, view._icon_service, view._state_manager,
                        dock_style=view._is_desktop_window
                    )
                    view._tile_cache[item] = tile
            row = idx // columns
            col = (idx % columns) + col_offset
            grid_layout.addWidget(tile, row, col)

