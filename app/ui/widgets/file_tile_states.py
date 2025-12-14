"""
FileTileStates - State management for FileTile.

Handles file state badges and state updates.
"""

from typing import TYPE_CHECKING, Optional

from app.ui.widgets.file_tile_utils import is_grid_view
from app.ui.widgets.state_badge_widget import StateBadgeWidget

if TYPE_CHECKING:
    from app.ui.widgets.file_tile import FileTile


def set_file_state(tile: 'FileTile', state: Optional[str]) -> None:
    """Update file state badge."""
    tile._file_state = state
    
    if is_grid_view(tile):
        icon_label = getattr(tile, '_icon_label', None)
        if icon_label:
            icon_label.update()
    elif tile._state_badge:
        tile._state_badge.set_state(state)

