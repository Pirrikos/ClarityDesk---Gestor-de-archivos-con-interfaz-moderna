"""Coordinación de previews entre MainWindow y DesktopWindow."""
from PySide6.QtWidgets import QApplication
from typing import Type, TypeVar, Optional

T = TypeVar('T')


def close_other_window_preview(
    current_window,
    other_window_class: Type[T],
    other_window_instance: Optional[T] = None
) -> None:
    """
    Cerrar preview abierto en otra ventana para evitar conflictos.
    
    Args:
        current_window: Instancia de la ventana actual (MainWindow o DesktopWindow)
        other_window_class: Clase de la otra ventana a buscar
        other_window_instance: Instancia directa de la otra ventana (opcional, más eficiente)
    """
    target_window = other_window_instance
    if target_window is None:
        # Buscar por tipo si no se proporciona instancia directa
        for widget in QApplication.allWidgets():
            if isinstance(widget, other_window_class) and widget != current_window:
                target_window = widget
                break
    
    if target_window and target_window != current_window:
        try:
            if hasattr(target_window, '_current_preview_window') and target_window._current_preview_window:
                target_window._current_preview_window.close()
                target_window._current_preview_window = None
        except RuntimeError:
            pass

