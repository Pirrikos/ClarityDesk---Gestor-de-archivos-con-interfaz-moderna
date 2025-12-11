"""
IconProcessor - Icon processing utilities.

Handles icon cropping, whitespace detection, and scaling operations.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap

from app.services.pixel_analyzer import find_content_bounds


def crop_and_scale_icon(pixmap: QPixmap, target_size: QSize) -> QPixmap:
    """Crop whitespace from icon and scale to fill target size."""
    if pixmap.isNull():
        return QPixmap()
    
    image = pixmap.toImage()
    width = image.width()
    height = image.height()
    
    min_x, min_y, max_x, max_y = find_content_bounds(image)
    
    if min_x >= max_x or min_y >= max_y:
        return _scale_pixmap(pixmap, target_size)
    
    crop_x, crop_y, crop_width, crop_height = _calculate_crop_bounds(
        min_x, min_y, max_x, max_y, width, height
    )
    
    cropped_image = image.copy(crop_x, crop_y, crop_width, crop_height)
    cropped_pixmap = QPixmap.fromImage(cropped_image)
    return _scale_pixmap(cropped_pixmap, target_size)


def _scale_pixmap(pixmap: QPixmap, target_size: QSize) -> QPixmap:
    """Scale pixmap to target size."""
    return pixmap.scaled(
        target_size.width(), target_size.height(),
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.FastTransformation
    )


def _calculate_crop_bounds(min_x, min_y, max_x, max_y, width, height):
    """Calculate crop bounds with padding and minimum size constraints."""
    content_width = max_x - min_x + 1
    content_height = max_y - min_y + 1
    
    padding_x = max(int(content_width * 0.20), int(width * 0.10))
    padding_y = max(int(content_height * 0.20), int(height * 0.10))
    
    crop_x = max(0, min_x - padding_x)
    crop_y = max(0, min_y - padding_y)
    crop_width = min(width - crop_x, max_x - min_x + 2 * padding_x)
    crop_height = min(height - crop_y, max_y - min_y + 2 * padding_y)
    
    min_crop_width = int(width * 0.60)
    min_crop_height = int(height * 0.60)
    if crop_width < min_crop_width:
        crop_x = max(0, (width - min_crop_width) // 2)
        crop_width = min_crop_width
    if crop_height < min_crop_height:
        crop_y = max(0, (height - min_crop_height) // 2)
        crop_height = min_crop_height
    
    return crop_x, crop_y, crop_width, crop_height


def has_excessive_whitespace(pixmap: QPixmap, threshold: float = 0.4) -> bool:
    """Detect if pixmap has excessive whitespace (transparent/white pixels)."""
    if pixmap.isNull():
        return False
    
    image = pixmap.toImage()
    width = image.width()
    height = image.height()
    total_pixels = width * height
    
    if total_pixels == 0:
        return False
    
    from app.services.pixel_analyzer import count_content_pixels, find_content_bounds
    
    min_x, min_y, max_x, max_y = find_content_bounds(image)
    content_pixels = count_content_pixels(image)
    
    if min_x >= max_x or min_y >= max_y:
        return True
    
    content_area = (max_x - min_x + 1) * (max_y - min_y + 1)
    content_ratio = content_area / total_pixels
    pixel_ratio = content_pixels / total_pixels
    
    return content_ratio < threshold or pixel_ratio < threshold

