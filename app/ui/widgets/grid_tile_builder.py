"""
GridTileBuilder - Tile creation for FileGridView.

Handles creation of file tiles and stack tiles.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import QWidget

from app.models.file_stack import FileStack
from app.services.icon_service import IconService
from app.ui.widgets.file_stack_tile import FileStackTile
from app.ui.widgets.file_tile import FileTile
from app.ui.widgets.file_tile_anim import soft_reveal

if TYPE_CHECKING:
    from app.ui.widgets.file_grid_view import FileGridView
    from app.managers.file_state_manager import FileStateManager


def create_file_tile(
    file_path: str,
    parent_view: 'FileGridView',
    icon_service: IconService,
    state_manager: Optional['FileStateManager'],
    dock_style: bool = False
) -> QWidget:
    """
    Create a tile widget for a file.

    Args:
        file_path: Full path to the file.
        parent_view: Parent FileGridView instance.
        icon_service: IconService instance.
        state_manager: Optional FileStateManager instance.
        dock_style: If True, use dock style.

    Returns:
        QWidget representing the file tile.
    """
    state = None
    if state_manager and not dock_style:
        state = state_manager.get_file_state(file_path)

    get_label_callback = getattr(parent_view, '_get_label_callback', None)
    tile = FileTile(
        file_path, parent_view, icon_service,
        dock_style=dock_style,
        initial_state=state,
        get_label_callback=get_label_callback
    )

    # Soft reveal para tiles no-dock: crear ocultos, revelar en siguiente ciclo
    if not dock_style:
        soft_reveal(tile)

    return tile


def create_stack_tile(
    file_stack: FileStack,
    parent_view: 'FileGridView',
    icon_service: IconService
) -> QWidget:
    """
    Create a tile widget for a file stack.

    Args:
        file_stack: FileStack object.
        parent_view: Parent FileGridView instance.
        icon_service: IconService instance.

    Returns:
        QWidget representing the stack tile.
    """
    tile = FileStackTile(file_stack, parent_view, icon_service)
    return tile

