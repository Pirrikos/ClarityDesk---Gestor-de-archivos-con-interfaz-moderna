"""
EventFilterUtils - Utilidades para instalación recursiva de eventFilters.

Centraliza la lógica de instalación de eventFilters para evitar duplicación.
"""

from PySide6.QtWidgets import QWidget


def install_event_filter_recursive(widget: QWidget, filter_object) -> None:
    """Instala eventFilter en un widget y todos sus hijos recursivamente."""
    if widget is None:
        return
    widget.installEventFilter(filter_object)
    for child in widget.findChildren(QWidget):
        child.installEventFilter(filter_object)

