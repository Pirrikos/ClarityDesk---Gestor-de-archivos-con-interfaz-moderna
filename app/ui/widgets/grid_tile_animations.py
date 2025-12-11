"""
GridTileAnimations - Tile animation helpers for grid layouts.

Handles entrance and exit animations for tiles.
"""

from app.ui.widgets.file_tile import FileTile


def animate_old_tiles_exit(view, old_expanded_tiles_to_animate: dict) -> None:
    """
    Animate exit for old expanded tiles no longer needed.
    
    Args:
        view: FileGridView instance.
        old_expanded_tiles_to_animate: Dict of old expanded tiles by stack type.
    """
    for old_stack_type, old_tiles in old_expanded_tiles_to_animate.items():
        if old_stack_type not in view._expanded_stacks:
            for idx, tile in enumerate(reversed(old_tiles)):
                delay = idx * 25
                view._animate_tile_exit(tile, delay)


def animate_tiles_entrance(stack_tiles: list[FileTile]) -> None:
    """
    Animate entrance of expanded tiles with staggered delay.
    
    Args:
        stack_tiles: List of FileTile instances to animate.
    """
    for idx, tile in enumerate(stack_tiles):
        delay = idx * 35
        tile.animate_enter(delay_ms=delay, start_offset=70)

