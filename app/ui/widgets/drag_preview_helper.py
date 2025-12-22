"""
DragPreviewHelper - Helper for creating drag preview images.

Generates composite preview images for multiple file drag operations.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap

from app.services.icon_service import IconService
from app.ui.utils.font_manager import FontManager


def create_multi_file_preview(
    file_paths: list[str],
    icon_service: IconService,
    base_size: QSize = QSize(48, 48)
) -> QPixmap:
    """
    Create composite preview image for multiple files.
    
    Args:
        file_paths: List of file paths to include in preview.
        icon_service: IconService for getting file icons.
        base_size: Base size for individual icons.
    
    Returns:
        Composite pixmap showing multiple file icons.
    """
    if not file_paths:
        return QPixmap()
    
    if len(file_paths) == 1:
        return _create_single_file_preview(file_paths[0], icon_service, base_size)
    
    return _create_composite_preview(file_paths, icon_service, base_size)


def _create_single_file_preview(
    file_path: str,
    icon_service: IconService,
    size: QSize
) -> QPixmap:
    """Create preview for single file."""
    icon = icon_service.get_file_icon(file_path, size)
    pixmap = icon.pixmap(size)
    if pixmap.isNull():
        pixmap = QPixmap(size)
        pixmap.fill(QColor(200, 200, 200))
    return pixmap


def _create_composite_preview(
    file_paths: list[str],
    icon_service: IconService,
    base_size: QSize
) -> QPixmap:
    """
    Create composite preview showing multiple file icons.
    
    Mejora: Muestra cantidad de archivos más claramente con badge siempre visible
    si hay más de 1 archivo.
    """
    max_icons = 4
    icons_to_show = file_paths[:max_icons]
    
    icon_size = QSize(32, 32)
    offset = 8
    composite_width = icon_size.width() + (offset * (len(icons_to_show) - 1))
    composite_height = icon_size.height() + 20
    
    composite = QPixmap(composite_width, composite_height)
    composite.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(composite)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    for idx, file_path in enumerate(icons_to_show):
        icon = icon_service.get_file_icon(file_path, icon_size)
        pixmap = icon.pixmap(icon_size)
        
        if pixmap.isNull():
            pixmap = QPixmap(icon_size)
            pixmap.fill(QColor(200, 200, 200))
        
        x_pos = idx * offset
        painter.drawPixmap(x_pos, 0, pixmap)
    
    # Mostrar badge siempre si hay más de 1 archivo (mejora feedback visual)
    if len(file_paths) > 1:
        _draw_count_badge(painter, len(file_paths), composite_width, composite_height)
    
    painter.end()
    return composite


def _draw_count_badge(
    painter: QPainter,
    total_count: int,
    width: int,
    height: int
) -> None:
    """
    Draw badge showing total file count.
    
    Mejora: Badge más visible con fondo semitransparente y texto más legible.
    """
    badge_size = 22
    badge_x = width - badge_size - 2
    badge_y = height - badge_size - 2
    
    # Fondo semitransparente para mejor visibilidad
    painter.setBrush(QColor(0, 120, 215, 220))
    painter.setPen(QPen(QColor(255, 255, 255, 255), 1))
    painter.drawEllipse(badge_x, badge_y, badge_size, badge_size)
    
    # Texto más legible
    painter.setPen(QColor(255, 255, 255))
    font = FontManager.create_font("Segoe UI", FontManager.SIZE_SMALL, QFont.Weight.Bold)
    painter.setFont(font)
    count_text = str(total_count) if total_count < 100 else "99+"
    painter.drawText(
        badge_x, badge_y, badge_size, badge_size,
        Qt.AlignmentFlag.AlignCenter,
        count_text
    )



