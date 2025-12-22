"""
Paint helpers for FileTile.

Handles custom painting for dock and grid styles with shared visual language.
Both modes use the same translucent rounded rectangle background.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPaintEvent

if TYPE_CHECKING:
    from app.ui.widgets.file_tile import FileTile


def paint_dock_style(tile: 'FileTile', event: QPaintEvent) -> None:
    container_widget = getattr(tile, '_container_widget', None)
    if not container_widget:
        return
    
    container_rect = container_widget.geometry()
    base_rect = QRectF(container_rect.adjusted(2, 2, -2, -2))
    
    painter = QPainter(tile)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    is_selected = tile._is_selected
    
    # Fondo gris claro para todos los tiles
    bg_color = QColor(190, 190, 190)  # #BEBEBE
    border_color = QColor(160, 160, 160)  # Borde gris más oscuro
    border_width = 1
    
    if is_selected:
        # Cuando está seleccionado, mantener el estilo azul pero sobre el fondo gris
        border_color = QColor(0, 122, 255)
        border_width = 2
        bg_color = QColor(0, 122, 255, 10)
    
    painter.setBrush(QBrush(bg_color))
    painter.setPen(QPen(border_color, border_width))
    painter.drawRoundedRect(base_rect, 14, 14)
    
    painter.end()



