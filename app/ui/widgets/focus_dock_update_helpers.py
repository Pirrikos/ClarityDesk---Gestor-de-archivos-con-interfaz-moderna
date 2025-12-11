"""
Update helpers for FocusDockWidget.

Handles tile creation, removal, and container size updates.
"""

from app.ui.widgets.focus_stack_tile import FocusStackTile


def remove_old_tiles(tiles: dict, current_paths: set) -> None:
    """Remove tiles for paths that no longer exist."""
    paths_to_remove = [path for path in tiles.keys() if path not in current_paths]
    for path in paths_to_remove:
        tile = tiles.pop(path)
        tile.deleteLater()


def create_new_tile(
    folder_path: str,
    is_active: bool,
    tiles_container: 'QWidget',
    icon_service: 'IconService'
) -> FocusStackTile:
    """Create a new FocusStackTile."""
    tile = FocusStackTile(
        folder_path,
        is_active,
        tiles_container,
        icon_service
    )
    return tile


def update_container_size(tiles_container: 'QWidget', tabs_count: int) -> None:
    """Update container minimum height based on number of tiles."""
    total_height = tabs_count * 93 + 16  # 85px per tile + 8px spacing + margins
    tiles_container.setMinimumHeight(max(100, total_height))


def force_widget_update(widget: 'QWidget') -> None:
    """Force widget and container updates for visibility."""
    widget.update()
    widget.repaint()
    widget.show()
    widget.raise_()

