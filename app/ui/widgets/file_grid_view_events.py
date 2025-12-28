"""
Event handlers for FileGridView.

Handles resize, stack clicks, expansion height, and tile animations.
"""

from math import ceil

from PySide6.QtCore import QTimer

from app.models.file_stack import FileStack
from app.ui.widgets.file_tile import FileTile
from app.ui.widgets.grid_layout_config import calculate_files_per_row
from app.ui.widgets.grid_tile_positions import calculate_columns_for_normal_grid


def _deferred_first_layout(view) -> None:
    """Ejecutar primera construcción del layout después de estabilizar ancho."""
    if hasattr(view, '_first_layout_pending'):
        view._first_layout_pending = False
    view._refresh_tiles()


def resize_event(view, event) -> None:
    """Handle resize coalescing: calcular columnas/filas una sola vez por ciclo."""
    view.__class__.__bases__[0].resizeEvent(view, event)
    
    # Dock no recalcula durante animaciones; ignora resize
    if view._is_desktop_window:
        if view._desktop_window and hasattr(view._desktop_window, '_height_animation_in_progress'):
            if view._desktop_window._height_animation_in_progress:
                return
        return
    
    # Ancho válido
    new_width = event.size().width()
    if new_width <= 0:
        return
    
    # Iniciar ciclo de resize: bloquear recalcular columnas dentro del ciclo
    if not getattr(view, '_layout_locked_for_resize', False):
        view._layout_locked_for_resize = True
    view._pending_resize_width = new_width
    
    # Timer único para finalizar el ciclo y calcular columnas definitivas
    if not hasattr(view, '_resize_finalize_timer'):
        view._resize_finalize_timer = QTimer()
        view._resize_finalize_timer.setSingleShot(True)
        def finalize():
            final_width = getattr(view, '_pending_resize_width', new_width)
            if final_width <= 0:
                view._layout_locked_for_resize = False
                return
            final_columns = calculate_columns_for_normal_grid(final_width)
            current_cached = getattr(view, '_cached_columns', None)
            # Actualizar cache y reconstruir solo si cambian columnas
            if final_columns and final_columns > 0:
                if current_cached is None or final_columns != current_cached:
                    view._cached_columns = final_columns
                    view._cached_width = final_width
                    if view._files or view._stacks:
                        view._refresh_tiles()
                else:
                    view._cached_width = final_width
            # Desbloquear ciclo
            view._layout_locked_for_resize = False
        view._resize_finalize_timer.timeout.connect(finalize)
    
    # Reiniciar el timer para coalescer múltiples eventos dentro de un único ciclo
    view._resize_finalize_timer.stop()
    view._resize_finalize_timer.start(180)


def on_stack_clicked(view, file_stack: FileStack) -> None:
    """Handle stack click - toggle expansion using QStackedWidget."""
    stack_type = file_stack.stack_type
    
    # Toggle expansión
    if stack_type in view._expanded_stacks:
        del view._expanded_stacks[stack_type]
    else:
        view._expanded_stacks.clear()
        view._expanded_stacks[stack_type] = file_stack.files
    
    # Calcular parámetros de layout
    total_expanded_files = sum(len(files) for files in view._expanded_stacks.values())
    
    if view._is_desktop_window and view._desktop_window:
        if total_expanded_files > 0:
            # Calcular files_per_row basado en el ancho del dock
            width = view._desktop_window.width()
            max_files_per_row = calculate_files_per_row(width)
            
            # Calcular filas discretas (1-3) basado en archivos y espacio disponible
            num_rows = ceil(total_expanded_files / max_files_per_row)
            num_rows = max(1, min(3, num_rows))
            files_per_row = ceil(total_expanded_files / num_rows)
            files_per_row = max(1, min(files_per_row, max_files_per_row))
            
            view._dock_rows_state = num_rows
            view._desktop_window._pending_expansion_state = {
                'stack_type': stack_type,
                'files': file_stack.files,
                'files_per_row': files_per_row,
                'num_rows': num_rows
            }
        else:
            view._desktop_window._pending_expansion_state = None
            view._dock_rows_state = None
    
    # Detectar si estamos REDUCIENDO filas (para ocultar durante animación)
    old_num_rows = getattr(view, '_previous_dock_rows_state', 0) or 0
    new_num_rows = getattr(view, '_dock_rows_state', 0) or 0
    is_reducing = new_num_rows < old_num_rows
    
    # Guardar estado actual para la próxima comparación
    view._previous_dock_rows_state = new_num_rows
    
    emit_expansion_height(view)
    
    # Usar ExpandedStacksWidget para cambio instantáneo
    if view._is_desktop_window and view._expanded_stacks_widget:
        if view._expanded_stacks:
            # Reutilizar files_per_row ya calculado arriba (basado en ancho del dock)
            
            if is_reducing:
                # REDUCIENDO: preparar página con altura 0, mostrar altura después de animación
                view._expanded_stacks_widget.setFixedHeight(0)
                view._expanded_stacks_widget.show_stack(
                    stack_type,
                    file_stack.files,
                    view,
                    files_per_row
                )
                view._expanded_stacks_widget.setFixedHeight(0)  # Mantener altura 0
                # Guardar datos para aplicar altura después de la animación
                view._show_expanded_after_animation = True
            else:
                # EXPANDIENDO o mismo tamaño: aplicar altura inmediatamente
                view._show_expanded_after_animation = False
                view._expanded_stacks_widget.show_stack(
                    stack_type,
                    file_stack.files,
                    view,
                    files_per_row
                )
            # NO necesitamos refresh de stacks - solo cambia el expanded widget
            view._pending_refresh_after_animation = False
            # NO estamos colapsando a base, estamos cambiando de expansión
            view._is_collapsing_to_base = False
        else:
            # Ocultar (colapsar) - solo ocultar widget, NO refresh de stacks
            view._expanded_stacks_widget.hide_stack()
            view._show_expanded_after_animation = False
            # NO marcar pending refresh cuando colapsamos - los stacks no cambian
            view._pending_refresh_after_animation = False
            # Marcar que estamos colapsando para que _force_grid_relayout no haga nada
            view._is_collapsing_to_base = True
    else:
        # Para ventanas normales
        view._refresh_tiles()


def emit_expansion_height(view) -> None:
    """Calculate and emit the height needed for expanded stacks."""
    if not view._is_desktop_window or not view._expanded_stacks:
        view.expansion_height_changed.emit(0)
        return
    
    # Usar el valor de filas clampeado si está disponible
    num_rows = getattr(view, '_dock_rows_state', None)
    
    if not num_rows:
        # Calcular si no hay valor clampeado
        total_stacks = len(view._stacks) if view._stacks else 5
        total_expanded_files = sum(len(files) for files in view._expanded_stacks.values())
        num_rows = (total_expanded_files + total_stacks - 1) // total_stacks
    
    if num_rows == 0:
        view.expansion_height_changed.emit(0)
        return
    
    # Usar cálculo consistente con ExpandedStacksWidget
    from app.ui.widgets.expanded_stacks_widget import ExpandedStacksWidget
    total_expansion_height = ExpandedStacksWidget.calculate_height_for_rows(num_rows)
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
