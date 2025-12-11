"""
GridTileBuilder - Tile creation for FileGridView.

Handles creation of file tiles and stack tiles.
"""

from PySide6.QtWidgets import QWidget

from app.models.file_stack import FileStack
from app.services.icon_service import IconService
from app.ui.widgets.file_stack_tile import FileStackTile
from app.ui.widgets.file_tile import FileTile


def create_file_tile(
    file_path: str,
    parent_view,
    icon_service: IconService,
    state_manager,
    disable_hover: bool = False,
    dock_style: bool = False
) -> QWidget:
    """
    Create a tile widget for a file.

    Args:
        file_path: Full path to the file.
        parent_view: Parent FileGridView instance.
        icon_service: IconService instance.
        state_manager: Optional FileStateManager instance.
        disable_hover: If True, disable hover animation.
        dock_style: If True, use dock style.

    Returns:
        QWidget representing the file tile.
    """
    tile = FileTile(
        file_path, parent_view, icon_service,
        disable_hover=disable_hover,
        dock_style=dock_style
    )
    
    # Set file state badge if manager is available (only if not dock style)
    if state_manager and not dock_style:
        state = state_manager.get_file_state(file_path)
        tile.set_file_state(state)
    
    return tile


def create_stack_tile(
    file_stack: FileStack,
    parent_view,
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

