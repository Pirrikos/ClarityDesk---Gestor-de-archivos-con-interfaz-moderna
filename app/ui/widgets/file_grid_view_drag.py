"""
Drag and drop handlers for FileGridView.

Handles drag enter, move, and drop events.
"""

from app.ui.widgets.container_drag_handler import handle_drag_enter, handle_drag_move, handle_drop


def drag_enter_event(view, event) -> None:
    """Handle drag enter for file drop on main widget."""
    handle_drag_enter(event, view._tab_manager)


def drag_move_event(view, event) -> None:
    """Handle drag move to maintain drop acceptance."""
    handle_drag_move(event, view._tab_manager)


def drop_event(view, event) -> None:
    """Handle file drop on main widget."""
    handle_drop(event, view._tab_manager, view.file_dropped)

