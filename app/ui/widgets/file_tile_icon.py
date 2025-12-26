"""
FileTileIcon - Icon handling for FileTile.

Handles icon loading and sizing with asynchronous loading.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QLabel, QGraphicsDropShadowEffect, QVBoxLayout, QWidget

from app.services.icon_service import IconService
from app.ui.widgets.file_tile_utils import is_grid_view
from app.ui.widgets.grid_icon_loader import GridIconLoader
from app.ui.widgets.state_badge_widget import STATE_COLORS

if TYPE_CHECKING:
    from app.ui.widgets.file_tile import FileTile


def _create_icon_shadow(widget: QWidget) -> QGraphicsDropShadowEffect:
    """Create standard icon shadow effect."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(6)
    shadow.setColor(QColor(0, 0, 0, 25))
    shadow.setOffset(0, 2)
    return shadow


class IconWidget(QWidget):
    """Widget que pinta icono y badge de estado para GridView."""
    
    def __init__(self, tile: 'FileTile', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._tile = tile
        self._icon_pixmap: Optional[QPixmap] = None
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAutoFillBackground(False)
        self.setStyleSheet("QWidget { background-color: transparent; }")
    
    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Establecer pixmap del icono."""
        self._icon_pixmap = pixmap
        self.update()
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Pintar icono y badge de estado."""
        super().paintEvent(event)
        
        if not self._icon_pixmap or self._icon_pixmap.isNull():
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Pintar icono centrado
        icon_rect = self.rect()
        pixmap_rect = QRect(
            (icon_rect.width() - self._icon_pixmap.width()) // 2,
            (icon_rect.height() - self._icon_pixmap.height()) // 2,
            self._icon_pixmap.width(),
            self._icon_pixmap.height()
        )
        painter.drawPixmap(pixmap_rect, self._icon_pixmap)
        
        # Pintar badge si hay estado
        if self._tile._file_state:
            self._paint_state_badge(painter, icon_rect)
        
        painter.end()
    
    def _paint_state_badge(self, painter: QPainter, icon_rect: QRect) -> None:
        """Pintar punto de color en esquina inferior derecha del icono."""
        state = self._tile._file_state
        if state not in STATE_COLORS:
            return
        
        dot_color = STATE_COLORS[state]
        dot_size = 7
        dot_x = icon_rect.width() - dot_size - 2
        dot_y = icon_rect.height() - dot_size - 2
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot_color)
        painter.drawEllipse(dot_x, dot_y, dot_size, dot_size)


def _create_placeholder_pixmap(size: QSize) -> QPixmap:
    """Crear pixmap placeholder transparente mientras se carga el icono."""
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    return pixmap


def _get_icon_loader(icon_service: IconService) -> GridIconLoader:
    """
    Get or create shared GridIconLoader instance.
    
    Uses icon_service as key to ensure one loader per service instance.
    """
    if not hasattr(icon_service, '_grid_icon_loader'):
        icon_service._grid_icon_loader = GridIconLoader(max_threads=5)
    return icon_service._grid_icon_loader


def _on_icon_loaded(
    tile: 'FileTile',
    icon_label,
    tile_id: str,
    image: QImage,
    request_id: int
) -> None:
    """
    Handle icon loaded callback.
    
    Converts QImage to QPixmap in UI thread and updates tile.
    """
    # Verify request_id matches (tile might have been recreated)
    if not hasattr(tile, '_icon_request_id') or tile._icon_request_id != request_id:
        return
    
    # Verify tile still exists and path hasn't changed
    if not hasattr(tile, '_file_path') or not tile._file_path:
        return
    
    try:
        # Convert QImage to QPixmap in UI thread (required)
        pixmap = QPixmap.fromImage(image)
        
        if pixmap and not pixmap.isNull():
            tile._icon_pixmap = pixmap
            
            # Update icon label
            if hasattr(icon_label, 'set_pixmap'):
                icon_label.set_pixmap(pixmap)
            elif hasattr(icon_label, 'setPixmap'):
                icon_label.setPixmap(pixmap)
            
            
    except (RuntimeError, AttributeError):
        # Tile was destroyed, ignore
        pass


def add_icon_zone(tile: 'FileTile', layout: QVBoxLayout, icon_service: IconService) -> None:
    """
    Add icon zone with shadow - carga asíncrona real usando QThreadPool.
    
    Muestra placeholder inmediatamente y carga icono en background thread.
    """
    icon_width = 48
    icon_height = 48
    icon_size = QSize(icon_width, icon_height)
    
    # Crear placeholder mientras se carga el icono
    placeholder_pixmap = _create_placeholder_pixmap(icon_size)
    tile._icon_pixmap = placeholder_pixmap
    
    use_grid_widget = not tile._dock_style and is_grid_view(tile)
    
    if use_grid_widget:
        icon_widget = IconWidget(tile)
        icon_widget.setFixedSize(icon_width, icon_height)
        icon_widget.set_pixmap(placeholder_pixmap)
        icon_shadow = _create_icon_shadow(icon_widget)
        icon_widget.setGraphicsEffect(icon_shadow)
        tile._icon_label = icon_widget
        tile._icon_shadow = icon_shadow
        icon_label = icon_widget
    else:
        icon_label = QLabel(tile)
        icon_label.setFixedSize(icon_width, icon_height)
        icon_label.setPixmap(placeholder_pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        icon_label.setAutoFillBackground(False)
        icon_label.setStyleSheet("QLabel { background-color: transparent; }")
        icon_shadow = _create_icon_shadow(icon_label)
        icon_label.setGraphicsEffect(icon_shadow)
        tile._icon_label = icon_label
        tile._icon_shadow = icon_shadow
    
    layout.addWidget(tile._icon_label, 0, Qt.AlignmentFlag.AlignHCenter)
    
    # Request icon loading asynchronously using QThreadPool
    icon_loader = _get_icon_loader(icon_service)
    
    # Generate unique tile_id for this tile instance
    tile_id = f"tile_{id(tile)}_{tile._file_path}"
    
    # Request icon and store request_id
    request_id = icon_loader.request_icon(tile_id, tile._file_path, icon_size)
    tile._icon_request_id = request_id
    tile._icon_tile_id = tile_id
    
    # Connect signal to handle result
    icon_loader.icon_loaded.connect(
        lambda tid, img, rid: _on_icon_loaded(tile, icon_label, tid, img, rid)
    )



