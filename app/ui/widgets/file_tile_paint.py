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
    """Paint background - Dock y Grid comparten el mismo fondo visual translúcido."""
    container_widget = getattr(tile, '_container_widget', None)
    if not container_widget:
        return
    
    container_rect = container_widget.geometry()
    base_rect = QRectF(container_rect.adjusted(2, 2, -2, -2))
    
    painter = QPainter(tile)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    is_selected = tile._is_selected
    
    bg_color = QColor(255, 255, 255, 15)
    border_color = QColor(255, 255, 255, 20)
    
    if is_selected:
        border_color = QColor(74, 144, 226, 255)
        border_width = 2
    else:
        border_width = 1
    
    painter.setBrush(QBrush(bg_color))
    painter.setPen(QPen(border_color, border_width))
    painter.drawRoundedRect(base_rect, 14, 14)
    
    painter.end()



