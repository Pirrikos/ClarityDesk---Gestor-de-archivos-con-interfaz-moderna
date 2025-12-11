"""
Paint helpers for FileTile.

Handles custom painting for dock style with premium selection effects.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QTransform


def paint_dock_style(tile, event) -> None:
    """Paint background - Dock style draws rounded rect container with premium selection."""
    if tile._dock_style and hasattr(tile, '_container_widget'):
        painter = QPainter(tile)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        container_rect = tile._container_widget.geometry()
        base_rect = QRectF(container_rect.adjusted(2, 2, -2, -2))
        
        # Check if multiple tiles are selected
        is_multi_selection = _is_multi_selection(tile)
        is_selected = tile._is_selected
        is_hovered = tile._is_hovered and not tile._disable_hover
        
        # Calculate scale factor
        scale_factor = 1.02 if is_selected else (1.01 if is_hovered else 1.0)
        
        # Draw glow effect for selection (before transform, extends beyond tile)
        if is_selected:
            _draw_selection_glow(painter, base_rect, is_multi_selection)
        
        # Draw hover shadow (before transform)
        if is_hovered and not is_selected:
            _draw_hover_shadow(painter, base_rect)
        
        # Apply scale transform if selected or hovered
        if scale_factor != 1.0:
            center = base_rect.center()
            transform = QTransform()
            transform.translate(center.x(), center.y())
            transform.scale(scale_factor, scale_factor)
            transform.translate(-center.x(), -center.y())
            painter.setTransform(transform)
        
        # Draw background (always white)
        bg_color = QColor(255, 255, 255, 250)
        border_color = QColor(200, 200, 200, 150)
        
        # Draw selection border if selected
        if is_selected:
            border_color = QColor(74, 144, 226, 255)  # #4A90E2
            border_width = 2
        else:
            border_width = 1
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, border_width))
        painter.drawRoundedRect(base_rect, 14, 14)
        
        painter.end()


def _is_multi_selection(tile) -> bool:
    """Check if multiple tiles are selected."""
    if not hasattr(tile, '_parent_view'):
        return False
    if not hasattr(tile._parent_view, '_selected_tiles'):
        return False
    selected_tiles = tile._parent_view._selected_tiles
    return len(selected_tiles) > 1


def _draw_selection_glow(painter: QPainter, rect: QRectF, is_multi: bool) -> None:
    """Draw premium glow effect for selected tiles."""
    painter.setPen(Qt.PenStyle.NoPen)
    
    if is_multi:
        # Multi-selection: softer glow
        # 0 0 0 1.5px rgba(74,144,226,0.35)
        inner_glow = QColor(74, 144, 226, 89)  # 0.35 * 255
        inner_glow_rect = rect.adjusted(-1.5, -1.5, 1.5, 1.5)
        painter.setBrush(QBrush(inner_glow))
        painter.drawRoundedRect(inner_glow_rect, 15.5, 15.5)
        
        # 0 5px 10px rgba(74,144,226,0.18)
        outer_glow = QColor(74, 144, 226, 46)  # 0.18 * 255
        outer_glow_rect = rect.adjusted(-10, -5, 10, 15)  # offset y: 5px, blur: 10px
        painter.setBrush(QBrush(outer_glow))
        painter.drawRoundedRect(outer_glow_rect, 24, 24)
    else:
        # Single selection: stronger glow
        # 0 0 0 2px rgba(74,144,226,0.55)
        inner_glow = QColor(74, 144, 226, 140)  # 0.55 * 255
        inner_glow_rect = rect.adjusted(-2, -2, 2, 2)
        painter.setBrush(QBrush(inner_glow))
        painter.drawRoundedRect(inner_glow_rect, 16, 16)
        
        # 0 6px 14px rgba(74,144,226,0.30)
        outer_glow = QColor(74, 144, 226, 77)  # 0.30 * 255
        outer_glow_rect = rect.adjusted(-14, -6, 14, 20)  # offset y: 6px, blur: 14px
        painter.setBrush(QBrush(outer_glow))
        painter.drawRoundedRect(outer_glow_rect, 28, 28)


def _draw_hover_shadow(painter: QPainter, rect: QRectF) -> None:
    """Draw subtle shadow for hover state."""
    # box-shadow: 0 6px 12px rgba(0,0,0,0.15)
    shadow_color = QColor(0, 0, 0, 38)  # 0.15 * 255 ≈ 38
    shadow_rect = rect.adjusted(-12, -6, 12, 18)  # offset y: 6px, blur: 12px
    
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(shadow_color))
    painter.drawRoundedRect(shadow_rect, 26, 26)

