"""
Preview Scaling - Pixmap scaling utilities.

Handles smart scaling of pixmaps for previews.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap


def _calculate_size_diff(pixmap: QPixmap, target: QSize) -> tuple[int, int]:
    """Calculate width and height differences."""
    return (
        abs(pixmap.width() - target.width()),
        abs(pixmap.height() - target.height())
    )


def _scale_to_exact_size(pixmap: QPixmap, size: QSize) -> QPixmap:
    """Scale pixmap to exact target size ignoring aspect ratio."""
    return pixmap.scaled(
        size.width(), size.height(),
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )


def _scale_keeping_aspect(pixmap: QPixmap, width: int, height: int) -> QPixmap:
    """Scale pixmap keeping aspect ratio."""
    return pixmap.scaled(
        width, height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )


def scale_if_needed(pixmap: QPixmap, target_size: QSize) -> QPixmap:
    """Scale pixmap if size difference is significant."""
    width_diff, height_diff = _calculate_size_diff(pixmap, target_size)
    
    if width_diff > 5 or height_diff > 5:
        return _scale_to_exact_size(pixmap, target_size)
    return pixmap


def _is_too_large(pixmap: QPixmap, size: QSize) -> bool:
    """Check if pixmap is significantly larger than target."""
    return (pixmap.width() > size.width() * 1.1 or 
            pixmap.height() > size.height() * 1.1)


def _is_within_tolerance(pixmap: QPixmap, size: QSize) -> bool:
    """Check if pixmap size is within acceptable tolerance."""
    width_diff, height_diff = _calculate_size_diff(pixmap, size)
    return width_diff <= 5 and height_diff <= 5


def _is_too_small(pixmap: QPixmap, size: QSize) -> bool:
    """Check if pixmap is smaller than target."""
    return (pixmap.width() < size.width() or 
            pixmap.height() < size.height())


def scale_pixmap_to_size(pixmap: QPixmap, size: QSize) -> QPixmap:
    """Scale pixmap to target size with smart scaling logic."""
    if pixmap.isNull():
        return pixmap
    
    if _is_too_large(pixmap, size):
        return _scale_keeping_aspect(pixmap, size.width(), size.height())
    
    if _is_within_tolerance(pixmap, size):
        return pixmap
    
    if _is_too_small(pixmap, size):
        return scale_small_pixmap(pixmap, size)
    
    return pixmap


def _calculate_scale_factor_for_min_size(pixmap: QPixmap, min_size: float) -> float:
    """Calculate scale factor to reach minimum size."""
    return max(min_size / pixmap.width(), min_size / pixmap.height())


def _calculate_scale_factor_to_fit(pixmap: QPixmap, size: QSize) -> float:
    """Calculate scale factor to fit within target size."""
    return min(size.width() / pixmap.width(), size.height() / pixmap.height())


def _calculate_scaled_dimensions(pixmap: QPixmap, scale_factor: float) -> tuple[int, int]:
    """Calculate scaled width and height."""
    return (
        int(pixmap.width() * scale_factor),
        int(pixmap.height() * scale_factor)
    )


def scale_small_pixmap(pixmap: QPixmap, size: QSize) -> QPixmap:
    """Scale small pixmap up to minimum size, then down if needed."""
    min_size = max(size.width(), size.height()) * 0.5
    
    if pixmap.width() < min_size or pixmap.height() < min_size:
        scale_factor = _calculate_scale_factor_for_min_size(pixmap, min_size)
        scaled_width, scaled_height = _calculate_scaled_dimensions(pixmap, scale_factor)
        
        if scaled_width > size.width() or scaled_height > size.height():
            scale_factor = _calculate_scale_factor_to_fit(pixmap, size)
            scaled_width, scaled_height = _calculate_scaled_dimensions(pixmap, scale_factor)
        
        return _scale_keeping_aspect(pixmap, scaled_width, scaled_height)
    
    return pixmap
