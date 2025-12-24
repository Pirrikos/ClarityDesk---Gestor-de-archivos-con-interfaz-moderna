"""
RoundedBackgroundPainter - Utilidad para pintar fondos redondeados estilo Finder.

Centraliza la lógica de dibujo de fondos con esquinas redondeadas y offset superior.
"""

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QPainter

from app.core.constants import ROUNDED_BG_RADIUS, ROUNDED_BG_TOP_OFFSET


def paint_rounded_background(
    painter: QPainter,
    widget_rect: QRect,
    bg_color: QColor,
    top_offset: int = ROUNDED_BG_TOP_OFFSET,
    radius: int = ROUNDED_BG_RADIUS
) -> None:
    """
    Pintar fondo redondeado con offset superior (estilo Finder).
    
    Args:
        painter: QPainter configurado con antialiasing
        widget_rect: Rectángulo del widget (ajustado para evitar artefactos)
        bg_color: Color del fondo
        top_offset: Offset superior para inset visual (default: constante)
        radius: Radio de las esquinas redondeadas (default: constante)
    """
    bg_rect = widget_rect.adjusted(0, top_offset, 0, 0)
    painter.setBrush(bg_color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(bg_rect, radius, radius)

