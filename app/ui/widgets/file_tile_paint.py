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
    is_hovered = getattr(tile, '_is_hovered', False)
    
    # Fondo gris claro para todos los tiles
    bg_color = QColor(190, 190, 190)  # #BEBEBE
    border_color = QColor(160, 160, 160)  # Borde gris más oscuro
    border_width = 1
    
    if is_selected:
        # Cuando está seleccionado, azul suave y sutil
        border_color = QColor(100, 150, 255)  # Azul más suave y claro
        border_width = 2
        bg_color = QColor(100, 150, 255, 15)  # Azul suave semitransparente
    
    # Pintar fondo del contenedor
    painter.setBrush(QBrush(bg_color))
    painter.setPen(QPen(border_color, border_width))
    painter.drawRoundedRect(base_rect, 14, 14)
    
    painter.end()


def _paint_hover_overlay(tile: 'FileTile', event: QPaintEvent) -> None:
    """Pintar overlay de hover encima de todo (llamado después de super().paintEvent)."""
    is_selected = tile._is_selected
    is_hovered = getattr(tile, '_is_hovered', False)
    
    if not is_hovered or is_selected:
        return
    
    container_widget = getattr(tile, '_container_widget', None)
    if not container_widget:
        return
    
    container_rect = container_widget.geometry()
    base_rect = QRectF(container_rect.adjusted(2, 2, -2, -2))
    
    # Pintar hover encima de TODO (incluyendo widgets hijos)
    hover_painter = QPainter(tile)
    hover_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Usar opacidad animada si está disponible (tanto dock como grid), sino usar opacidad fija
    hover_opacity = getattr(tile, '_hover_opacity', 1.0 if is_hovered else 0.0)
    hover_alpha = int(34 * hover_opacity)  # 34 es la opacidad máxima del hover
    
    hover_color = QColor(0, 0, 0, hover_alpha)  # Negro semitransparente - visible sobre fondo gris claro
    hover_painter.setBrush(QBrush(hover_color))
    hover_painter.setPen(Qt.PenStyle.NoPen)
    hover_painter.drawRoundedRect(base_rect, 14, 14)
    hover_painter.end()



