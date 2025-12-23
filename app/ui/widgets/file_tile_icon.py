"""
FileTileIcon - Icon handling for FileTile.

Handles icon loading and sizing.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QLabel, QGraphicsDropShadowEffect, QVBoxLayout, QWidget

from app.services.icon_render_service import IconRenderService
from app.services.icon_service import IconService
from app.ui.widgets.file_tile_utils import is_grid_view
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


def _load_icon_async(tile: 'FileTile', icon_service: IconService, icon_label) -> None:
    """Cargar icono de forma diferida para no bloquear la construcción del tile."""
    # Verificar que el tile aún existe
    if not hasattr(tile, '_file_path') or not tile._file_path:
        return
    
    file_path = tile._file_path
    
    # Cargar icono de forma diferida usando QTimer
    # Esto permite que la UI se construya primero y luego se carguen los iconos progresivamente
    def load_icon():
        # Verificar que el tile aún existe y la ruta no cambió
        if not hasattr(tile, '_file_path') or tile._file_path != file_path:
            return
        
        try:
            render_service = IconRenderService(icon_service)
            pixmap = render_service.get_file_preview(file_path, QSize(48, 48))
            
            # Verificar nuevamente antes de actualizar
            if not hasattr(tile, '_file_path') or tile._file_path != file_path:
                return
            
            if pixmap and not pixmap.isNull():
                tile._icon_pixmap = pixmap
                if hasattr(icon_label, 'set_pixmap'):
                    icon_label.set_pixmap(pixmap)
                elif hasattr(icon_label, 'setPixmap'):
                    icon_label.setPixmap(pixmap)
        except (RuntimeError, AttributeError):
            # Tile fue destruido, ignorar
            pass
    
    # Cargar con pequeño delay para no bloquear construcción inicial
    QTimer.singleShot(10, load_icon)


def add_icon_zone(tile: 'FileTile', layout: QVBoxLayout, icon_service: IconService) -> None:
    """Add icon zone with shadow - carga asíncrona de iconos para mejor rendimiento."""
    icon_width = 48
    icon_height = 48
    
    # Crear placeholder mientras se carga el icono
    placeholder_pixmap = _create_placeholder_pixmap(QSize(icon_width, icon_height))
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
        # Cargar icono real de forma asíncrona
        QTimer.singleShot(0, lambda: _load_icon_async(tile, icon_service, icon_widget))
    else:
        icon_label = QLabel()
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
        # Cargar icono real de forma asíncrona
        QTimer.singleShot(0, lambda: _load_icon_async(tile, icon_service, icon_label))
    
    layout.addWidget(tile._icon_label, 0, Qt.AlignmentFlag.AlignHCenter)



