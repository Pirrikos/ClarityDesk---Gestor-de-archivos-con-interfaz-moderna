"""
Paint logic for FocusStackTile.

Handles custom painting of tile background with rounded corners.
"""

from PySide6.QtGui import QBrush, QColor, QPainter, QPen


def paint_tile_background(
    painter: QPainter,
    container_rect,
    is_active: bool,
    is_hovered: bool,
    is_dragging_over: bool
) -> None:
    """Paint tile background with rounded corners - Apple white style like DesktopStackTile."""
    if not container_rect.isValid():
        return
    
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    rect = container_rect.adjusted(2, 2, -2, -2)
    
    # Apple white style: same as DesktopStackTile and FileStackTile
    # Always white background, regardless of active state
    if is_hovered or is_dragging_over:
        bg_color = QColor(255, 255, 255, 255)
        border_color = QColor(220, 220, 220, 200)
    else:
        bg_color = QColor(255, 255, 255, 250)
        border_color = QColor(200, 200, 200, 150)
    
    painter.setBrush(QBrush(bg_color))
    painter.setPen(QPen(border_color, 1))
    painter.drawRoundedRect(rect, 14, 14)

