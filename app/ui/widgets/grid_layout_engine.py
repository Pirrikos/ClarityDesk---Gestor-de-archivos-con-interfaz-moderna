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


def _connect_settings_tile_signals(settings_tile: SettingsStackTile, view) -> None:
    """Connect settings tile click to open SettingsWindow."""
    from app.ui.windows.settings_window import get_settings_window
    settings_tile.clicked.connect(lambda: get_settings_window().show())


def build_dock_layout(
    view,
    items_to_render: list,
    old_expanded_tiles_to_animate: dict,
    grid_layout: QGridLayout
) -> None:
    """
    Build Dock-style layout with stacks only.
    
    Los archivos expandidos son manejados por ExpandedStacksWidget (QStackedWidget),
    no se crean en este grid. Esto permite cambios instantáneos sin recrear widgets.
    """
    setup_dock_layout_config(grid_layout)
    
    # Obtener contenedor de stacks (puede ser _content_widget o _stacks_container)
    stacks_container = getattr(view, '_stacks_container', view._content_widget)
    
    updates_enabled = stacks_container.updatesEnabled()
    try:
        stacks_container.setUpdatesEnabled(False)
        
        # Construir solo los stack tiles (fila 0)
        _build_stack_tiles(view, items_to_render, grid_layout)
        
        # Forzar cálculo del layout
        grid_layout.activate()
        stacks_container.updateGeometry()
    finally:
        stacks_container.setUpdatesEnabled(updates_enabled)


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
    
    setup_normal_grid_config(grid_layout)
    
    col_offset = get_col_offset_for_desktop_window(view._is_desktop_window)
    
    # Política: durante un ciclo de resize, NO recalcular columnas aquí.
    # Se calcularán al finalizar el ciclo en resizeEvent (coalescido).
    if not getattr(view, '_layout_locked_for_resize', False):
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
        
        # REGLA CRÍTICA: Eliminar headers existentes SIEMPRE antes de procesar cambios
        # Esto asegura que:
        # 1. Categorías vacías no dejen headers huérfanos
        # 2. Transiciones de categorizado a no categorizado limpien headers
        # 3. Cambios de categorías eliminen headers antiguos antes de añadir nuevos
        _remove_existing_headers(grid_layout)
        
        # Añadir headers nuevos solo si hay categorización Y categorías con archivos
        if is_categorized and header_rows:
            _add_category_headers_at_rows(view, items_to_render, grid_layout, header_rows, columns, col_offset)
        
        # Apply changes incrementally
        # 1. Detach removed and moved tiles
        for tile_id in diff.removed + list(diff.moved.keys()):
            tile = tile_manager.get_tile(tile_id)
            if tile:
                tile_manager.detach(tile)
        
        # 2. Destroy removed (ya están ocultos)
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
    
    IMPORTANTE: _remove_existing_headers() debe llamarse ANTES de esta función.
    Esta función solo añade headers nuevos, no elimina los antiguos.
    
    Args:
        view: FileGridView instance
        items_to_render: List of (category_label, files) tuples
        grid_layout: Grid layout
        header_rows: List of row numbers where headers should be placed
        columns: Number of columns
        col_offset: Column offset
    """
    from app.ui.widgets.category_section_header import CategorySectionHeader
    
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
    
    # Reutilizar tiles de sistema existentes (Desktop, Settings, Separator)
    if view._is_desktop_window:
        # Buscar tiles existentes en el layout antes de crear nuevos
        desktop_tile = None
        settings_tile = None
        separator = None
        
        # Buscar tiles existentes en sus posiciones conocidas
        desktop_item = grid_layout.itemAtPosition(stack_row, 0)
        if desktop_item and desktop_item.widget():
            widget = desktop_item.widget()
            if isinstance(widget, DesktopStackTile):
                desktop_tile = widget
        
        settings_item = grid_layout.itemAtPosition(stack_row, 1)
        if settings_item and settings_item.widget():
            widget = settings_item.widget()
            if isinstance(widget, SettingsStackTile):
                settings_tile = widget
        
        separator_item = grid_layout.itemAtPosition(stack_row, 2)
        if separator_item and separator_item.widget():
            widget = separator_item.widget()
            if isinstance(widget, DockSeparator):
                separator = widget
        
        # Crear solo si no existen
        if not desktop_tile:
            desktop_tile = DesktopStackTile(view)
            _connect_desktop_tile_signals(desktop_tile, view)
            grid_layout.addWidget(desktop_tile, stack_row, 0)
        
        if not settings_tile:
            settings_tile = SettingsStackTile(view)
            _connect_settings_tile_signals(settings_tile, view)
            grid_layout.addWidget(settings_tile, stack_row, 1)
        
        if not separator:
            separator = DockSeparator(view)
            grid_layout.addWidget(separator, stack_row, 2)
        
        col_offset = 3
    
    # Eliminar tiles de stacks que ya no existen
    from app.ui.widgets.file_stack_tile import FileStackTile
    
    # Calcular cuántos stacks nuevos hay
    new_stacks_count = len(items_to_render) if view._stacks else 0
    
    # Encontrar y eliminar tiles de stacks en columnas que ya no tienen stacks
    col_to_check = col_offset
    while True:
        existing_item = grid_layout.itemAtPosition(stack_row, col_to_check)
        if not existing_item:
            break
        widget = existing_item.widget()
        if widget and isinstance(widget, FileStackTile):
            # Si esta columna está más allá del número de stacks nuevos, eliminar
            if col_to_check >= col_offset + new_stacks_count:
                grid_layout.removeWidget(widget)
                # Limpiar badge antes de eliminar (está en parent diferente)
                if hasattr(widget, '_cleanup_badge'):
                    widget._cleanup_badge()
                widget.deleteLater()
        col_to_check += 1
    
    # Reutilizar stack tiles existentes en lugar de recrearlos
    for idx, item in enumerate(items_to_render):
        col = idx + col_offset
        if view._stacks:
            stack = item
            stack_type = stack.stack_type
            
            # Buscar tile existente en esta posición
            existing_item = grid_layout.itemAtPosition(stack_row, col)
            existing_tile = None
            widget_to_remove = None
            
            if existing_item and existing_item.widget():
                widget = existing_item.widget()
                # Verificar si es un FileStackTile y corresponde al mismo stack_type
                if isinstance(widget, FileStackTile):
                    if hasattr(widget, '_file_stack') and widget._file_stack.stack_type == stack_type:
                        existing_tile = widget
                    else:
                        # Tile de tipo diferente - marcar para eliminar
                        widget_to_remove = widget
            
            # Eliminar tile antiguo de tipo diferente si existe
            if widget_to_remove:
                grid_layout.removeWidget(widget_to_remove)
                # Limpiar badge antes de eliminar (está en parent diferente)
                if hasattr(widget_to_remove, '_cleanup_badge'):
                    widget_to_remove._cleanup_badge()
                widget_to_remove.deleteLater()
            
            if existing_tile:
                # Reutilizar tile existente
                tile = existing_tile
                # Actualizar el stack interno con los nuevos archivos
                tile._file_stack = stack
                # Forzar actualización del badge (resetear _last_count para forzar update)
                tile._last_count = -1
                QTimer.singleShot(0, tile.update_badge_count)
            else:
                # Crear nuevo tile solo si no existe
                tile = create_stack_tile(stack, view, view._icon_service)
                tile.stack_clicked.connect(view._on_stack_clicked)
                tile.open_file.connect(view.open_file.emit)
                grid_layout.addWidget(tile, stack_row, col)
                QTimer.singleShot(0, tile.update_badge_count)
            
            stack_col_map[stack_type] = col
        else:
            tile = create_file_tile(
                item, view, view._icon_service, view._state_manager,
                dock_style=view._is_desktop_window
            )
            grid_layout.addWidget(tile, stack_row, col)
    
    return stack_col_map



# NOTA: Los archivos expandidos ahora son manejados por ExpandedStacksWidget (QStackedWidget)
# Las funciones _build_expanded_files y _create_expanded_file_tiles han sido eliminadas.
