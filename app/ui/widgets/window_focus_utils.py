"""Utilidades para manejo de foco de ventanas."""
from PySide6.QtWidgets import QWidget


def activate_parent_window(widget: QWidget) -> None:
    """Activar ventana padre y darle foco para que funcionen los shortcuts."""
    top_level = widget.window()
    if top_level:
        top_level.activateWindow()
        top_level.setFocus()

