"""
FileTileAnim - Animation handling for FileTile.

Handles enter and exit animations for dock-style tiles.
"""

from PySide6.QtCore import QPoint, QPropertyAnimation, QEasingCurve, QTimer, QParallelAnimationGroup


def animate_enter(tile, delay_ms: int = 0, start_offset: int = 80) -> None:
    """
    Animate tile entrance Apple-style: emerge from below with fade.
    
    Args:
        tile: FileTile instance.
        delay_ms: Delay in milliseconds before starting animation.
        start_offset: Vertical offset to start from (pixels below final position).
    """
    if not tile._dock_style:
        return
    
    # Start invisible
    tile.setWindowOpacity(0)
    tile.show()
    
    # Minimum delay to allow Qt layout to calculate correct positions
    actual_delay = max(delay_ms, 20)
    
    # Schedule the animation
    QTimer.singleShot(actual_delay, lambda: _run_enter_animation(tile, start_offset))


def _run_enter_animation(tile, start_offset: int) -> None:
    """Execute the enter animation with position and opacity."""
    try:
        final_pos = tile.pos()
        start_pos = QPoint(final_pos.x(), final_pos.y() + start_offset)
        
        tile.move(start_pos)
        tile.setWindowOpacity(1)
        
        tile._enter_anim_group = QParallelAnimationGroup(tile)
        
        pos_anim = QPropertyAnimation(tile, b"pos", tile)
        pos_anim.setDuration(280)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(final_pos)
        pos_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        
        tile._enter_anim_group.addAnimation(pos_anim)
        tile._enter_anim_group.start()
    except RuntimeError:
        pass


def animate_exit(tile, callback=None, end_offset: int = 60) -> None:
    """
    Animate tile exit Apple-style: sink down with fade.
    
    Args:
        tile: FileTile instance.
        callback: Optional callback to call when animation finishes.
        end_offset: Vertical offset to end at (pixels below current position).
    """
    if not tile._dock_style:
        _call_exit_callback(tile, callback)
        return
    
    try:
        start_pos = tile.pos()
        end_pos = QPoint(start_pos.x(), start_pos.y() + end_offset)
        _setup_exit_animation(tile, start_pos, end_pos, callback)
    except RuntimeError:
        _call_exit_callback(tile, callback)


def _setup_exit_animation(tile, start_pos: QPoint, end_pos: QPoint, callback) -> None:
    """Setup and start exit animation."""
    tile._exit_anim_group = QParallelAnimationGroup(tile)
    pos_anim = QPropertyAnimation(tile, b"pos", tile)
    pos_anim.setDuration(200)
    pos_anim.setStartValue(start_pos)
    pos_anim.setEndValue(end_pos)
    pos_anim.setEasingCurve(QEasingCurve.Type.InBack)
    
    tile._exit_anim_group.addAnimation(pos_anim)
    tile._exit_anim_group.finished.connect(lambda: _on_exit_animation_finished(tile, callback))
    tile._exit_anim_group.start()


def _on_exit_animation_finished(tile, callback) -> None:
    """Handle exit animation completion."""
    try:
        tile.hide()
        _call_exit_callback(tile, callback)
    except RuntimeError:
        pass


def _call_exit_callback(tile, callback) -> None:
    """Safely call exit callback."""
    if callback:
        try:
            callback()
        except RuntimeError:
            pass

