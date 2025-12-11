"""
IconNormalizer - Visual normalization utilities for icons.

Handles scaling, centering, and rounded corners.
"""

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap


def apply_visual_normalization(raw_pixmap: QPixmap, target_size: QSize) -> QPixmap:
    """Normalize visual appearance: 90% scale, rounded corners, NO overlay."""
    if raw_pixmap.isNull():
        return raw_pixmap
    
    canvas = QPixmap(target_size)
    canvas.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    scaled_pixmap, x_offset, y_offset = scale_and_center_pixmap(raw_pixmap, target_size)
    
    apply_rounded_clip(painter, target_size)
    painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
    # NO aplicar overlay - causaba que iconos se vieran blanqueados
    
    painter.end()
    return canvas


def normalize_for_list(raw_pixmap: QPixmap, target_size: QSize) -> QPixmap:
    """Normalize for list view: 100% scale, no overlay, no rounded corners."""
    if raw_pixmap.isNull():
        return raw_pixmap
    
    if raw_pixmap.width() != target_size.width() or raw_pixmap.height() != target_size.height():
        scaled_pixmap = raw_pixmap.scaled(
            target_size.width(), target_size.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    else:
        scaled_pixmap = raw_pixmap
    
    canvas = QPixmap(target_size)
    canvas.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    x_offset = (target_size.width() - scaled_pixmap.width()) // 2
    y_offset = (target_size.height() - scaled_pixmap.height()) // 2
    painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
    
    painter.end()
    return canvas


def scale_and_center_pixmap(raw_pixmap: QPixmap, target_size: QSize) -> tuple[QPixmap, int, int]:
    """Scale pixmap to 90% max and calculate centered position."""
    max_scale = 0.9
    scaled_width = int(target_size.width() * max_scale)
    scaled_height = int(target_size.height() * max_scale)
    
    scaled_pixmap = raw_pixmap.scaled(
        scaled_width, scaled_height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )
    
    x_offset = (target_size.width() - scaled_pixmap.width()) // 2
    y_offset = (target_size.height() - scaled_pixmap.height()) // 2
    
    return scaled_pixmap, x_offset, y_offset


def apply_rounded_clip(painter: QPainter, target_size: QSize) -> None:
    """Apply rounded rectangle clip path with radius 8."""
    clip_path = QPainterPath()
    clip_path.addRoundedRect(
        QRect(0, 0, target_size.width(), target_size.height()),
        8, 8, Qt.SizeMode.AbsoluteSize
    )
    painter.setClipPath(clip_path)
