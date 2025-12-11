"""
IconFallbackHelper - Fallback icon helper for services.

Provides default icon fallback when main icon is unavailable.
"""

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QPixmap

from app.services.icon_renderer import get_svg_for_extension, render_svg_icon


def safe_pixmap(pixmap: QPixmap, size: int, file_extension: str = "") -> QPixmap:
    """Verify pixmap validity, return fallback only if NULL."""
    if not pixmap or pixmap.isNull():
        return get_default_icon(size, file_extension)
    return pixmap


def get_default_icon(size: int, file_extension: str = "") -> QPixmap:
    """Load SVG icon by extension or generic from assets/icons/."""
    if size <= 0:
        size = 96
    
    target_size = QSize(size, size)
    
    if file_extension:
        svg_name = get_svg_for_extension(file_extension)
        svg_pixmap = render_svg_icon(svg_name, target_size, file_extension)
        if not svg_pixmap.isNull():
            return svg_pixmap
    
    generic_pixmap = render_svg_icon("generic.svg", target_size, file_extension)
    if not generic_pixmap.isNull():
        return generic_pixmap
    
    pixmap = QPixmap(target_size)
    pixmap.fill(QColor(200, 200, 200))
    return pixmap

