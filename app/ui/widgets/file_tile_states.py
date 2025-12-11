"""
FileTileStates - State management for FileTile.

Handles file state badges and state updates.
"""

from typing import Optional

from app.ui.widgets.state_badge_widget import StateBadgeWidget


def set_file_state(tile, state: Optional[str]) -> None:
    """Update file state badge."""
    if tile._state_badge:
        tile._state_badge.set_state(state)
        tile._update_badge_position()


def _set_state(tile, state) -> None:
    """Set file state via state manager."""
    if not tile._parent_view or not hasattr(tile._parent_view, '_state_manager'):
        return
    
    state_manager = tile._parent_view._state_manager
    if state_manager:
        state_manager.set_file_state(tile._file_path, state)
        set_file_state(tile, state)

