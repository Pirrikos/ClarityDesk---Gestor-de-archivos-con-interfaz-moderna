"""
Controller logic for FileTile.

Handles selection state and icon updates.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.ui.widgets.file_tile import FileTile


def set_selected(tile: 'FileTile', selected: bool) -> None:
    """Update tile selection state - sin efectos hover, solo borde visual."""
    tile._is_selected = selected
    tile.update()

