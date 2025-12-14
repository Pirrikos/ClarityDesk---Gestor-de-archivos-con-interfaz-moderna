"""
ListIconDelegate - Delegate for rendering icons in list view.
"""

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import QStyle, QStyledItemDelegate


class ListIconDelegate(QStyledItemDelegate):
    """Delegate for rendering icons in list view."""
    
    def paint(self, painter: QPainter, option, index) -> None:
        """Paint item with icon and text."""
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
        # Mantener fondo transparente para coherencia con Grid; usar overlays sutiles
        if is_selected:
            painter.fillRect(option.rect, QColor(255, 255, 255, 18))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(255, 255, 255, 10))
        else:
            # Transparente: no dibujar bloque blanco
            pass
    
    def _draw_icon_with_shadow(self, painter: QPainter, option, icon: QIcon, is_selected: bool) -> None:
        """Draw icon without background."""
        icon_size = QSize(30, 30) if is_selected else QSize(28, 28)
        pixmap = icon.pixmap(icon_size)
        if pixmap.isNull():
            return
        
        icon_x = option.rect.left() + 10
        icon_y = option.rect.top() + (option.rect.height() - icon_size.height()) // 2
        
        icon_rect = QRect(icon_x, icon_y, icon_size.width(), icon_size.height())
        painter.drawPixmap(icon_rect, pixmap)
    
    def _draw_text(self, painter: QPainter, option, text: str, is_selected: bool) -> None:
        """Draw text next to icon."""
        text_x = option.rect.left() + (30 if is_selected else 28) + 32
        text_rect = QRect(
            text_x,
            option.rect.top(),
            option.rect.width() - text_x,
            option.rect.height()
        )
        # Texto en claro para fondo oscuro
        painter.setPen(QColor(230, 231, 234))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

