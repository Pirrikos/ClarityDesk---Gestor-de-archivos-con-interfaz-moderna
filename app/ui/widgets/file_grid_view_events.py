"""
Event handlers for FileGridView.

Handles resize, stack clicks, expansion height, and tile animations.
"""

from PySide6.QtCore import QTimer

from app.models.file_stack import FileStack
from app.ui.widgets.file_tile import FileTile


def resize_event(view, event) -> None:
    """Handle resize to recalculate grid columns with debouncing."""
    view.__class__.__bases__[0].resizeEvent(view, event)
    
    # Debounce: solo procesar después de 150ms de quietud
    # Esto evita reconstrucciones excesivas durante resize continuo
    if not hasattr(view, '_resize_timer'):
        view._resize_timer = QTimer()
        view._resize_timer.setSingleShot(True)
        view._resize_timer.timeout.connect(lambda: view._refresh_tiles() if view._files else None)
    
    # Cancelar timer anterior y reiniciar con nuevo delay
    view._resize_timer.stop()
    view._resize_timer.start(150)


def on_stack_clicked(view, file_stack: FileStack) -> None:
    """Handle stack click - toggle expansion horizontally below stack."""
    stack_type = file_stack.stack_type
    
    if stack_type in view._expanded_stacks:
        del view._expanded_stacks[stack_type]
    else:
        view._expanded_stacks.clear()
        view._expanded_stacks[stack_type] = file_stack.files
    
    emit_expansion_height(view)
    view._refresh_tiles()


def emit_expansion_height(view) -> None:
    """Calculate and emit the height needed for expanded stacks."""
    if not view._is_desktop_window or not view._expanded_stacks:
        view.expansion_height_changed.emit(0)
        return
    
    total_stacks = len(view._stacks) if view._stacks else 5
    total_expanded_files = sum(len(files) for files in view._expanded_stacks.values())
    num_rows = (total_expanded_files + total_stacks - 1) // total_stacks
    
    if num_rows == 0:
        view.expansion_height_changed.emit(0)
        return
    
    height_per_row = 85 + 16
    total_expansion_height = (num_rows * height_per_row) + 40
    view.expansion_height_changed.emit(total_expansion_height)


def remove_tile_safely(view, tile: FileTile) -> None:
    """Safely remove a tile after exit animation completes."""
    try:
        view._grid_layout.removeWidget(tile)
        tile.setParent(None)
        tile.deleteLater()
    except RuntimeError:
        pass


def animate_tile_exit(view, tile: FileTile, delay_ms: int = 0) -> None:
    """Animate tile exit with delay, then remove it."""
    def do_animate():
        try:
            tile.animate_exit(callback=lambda: remove_tile_safely(view, tile))
        except RuntimeError:
            pass
    
    if delay_ms > 0:
        QTimer.singleShot(delay_ms, do_animate)
    else:
        do_animate()

