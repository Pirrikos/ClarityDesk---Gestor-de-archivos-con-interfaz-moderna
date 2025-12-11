"""
ListIconDelegate - Delegate for rendering icons with blue shadow in list view.

Shows blue shadow effect when row is selected, similar to grid mode.
"""

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import QStyle, QStyledItemDelegate


class ListIconDelegate(QStyledItemDelegate):
    """Delegate for rendering icons with blue shadow when selected (like grid mode)."""
    
    def paint(self, painter: QPainter, option, index) -> None:
        """Paint item with icon shadow effect when selected."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        is_selected = option.state & QStyle.StateFlag.State_Selected
        
        self._draw_background(painter, option, is_selected)
        
        if icon and isinstance(icon, QIcon) and not icon.isNull():
            self._draw_icon_with_shadow(painter, option, icon, is_selected)
        
        if text:
            self._draw_text(painter, option, text, is_selected)
    
    def _draw_background(self, painter: QPainter, option, is_selected: bool) -> None:
        """Draw background for item."""
        if is_selected:
            painter.fillRect(option.rect, QColor(255, 255, 255, 0))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(245, 248, 255))
        else:
            painter.fillRect(option.rect, QColor(255, 255, 255))
    
    def _draw_icon_with_shadow(self, painter: QPainter, option, icon: QIcon, is_selected: bool) -> None:
        """Draw icon with blue shadow if selected."""
        icon_size = QSize(30, 30) if is_selected else QSize(28, 28)
        pixmap = icon.pixmap(icon_size)
        if pixmap.isNull():
            return
        
        icon_x = option.rect.left() + 10
        icon_y = option.rect.top() + (option.rect.height() - icon_size.height()) // 2
        
        if is_selected:
            self._draw_blue_shadow(painter, icon_x, icon_y, icon_size)
        
        icon_rect = QRect(icon_x, icon_y, icon_size.width(), icon_size.height())
        painter.drawPixmap(icon_rect, pixmap)
    
    def _draw_blue_shadow(self, painter: QPainter, icon_x: int, icon_y: int, icon_size: QSize) -> None:
        """Draw blue shadow layers for selected icon."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        shadow_offset = 3
        shadow_blur = 15
        
        for i in range(shadow_blur):
            alpha = int(100 * (1 - i / shadow_blur) * 0.2)
            if alpha <= 0:
                break
            shadow_color = QColor(0, 120, 255, alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(shadow_color)
            offset = shadow_offset - (i * 0.12)
            shadow_rect = QRect(
                int(icon_x + offset),
                int(icon_y + offset),
                icon_size.width(),
                icon_size.height()
            )
            painter.drawRoundedRect(shadow_rect, 8, 8)
    
    def _draw_text(self, painter: QPainter, option, text: str, is_selected: bool) -> None:
        """Draw text next to icon."""
        text_x = option.rect.left() + (30 if is_selected else 28) + 32
        text_rect = QRect(
            text_x,
            option.rect.top(),
            option.rect.width() - text_x,
            option.rect.height()
        )
        painter.setPen(QColor(43, 43, 43))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

