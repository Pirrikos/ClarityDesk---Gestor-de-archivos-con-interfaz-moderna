"""
PixelAnalyzer - Pixel analysis utilities for icon processing.

Extracted from icon_processor to reduce method size.
"""

from PySide6.QtGui import QPixmap


def find_content_bounds(image):
    """Find content bounds (non-transparent, non-white pixels)."""
    width = image.width()
    height = image.height()
    min_x = width
    min_y = height
    max_x = 0
    max_y = 0
    
    for y in range(height):
        for x in range(width):
            pixel = image.pixel(x, y)
            alpha = (pixel >> 24) & 0xFF
            red = (pixel >> 16) & 0xFF
            green = (pixel >> 8) & 0xFF
            blue = pixel & 0xFF
            
            if alpha > 5 and not (red > 245 and green > 245 and blue > 245):
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    
    return min_x, min_y, max_x, max_y


def count_content_pixels(image):
    """Count content pixels (non-transparent, non-white)."""
    width = image.width()
    height = image.height()
    content_pixels = 0
    
    for y in range(height):
        for x in range(width):
            pixel = image.pixel(x, y)
            alpha = (pixel >> 24) & 0xFF
            red = (pixel >> 16) & 0xFF
            green = (pixel >> 8) & 0xFF
            blue = pixel & 0xFF
            
            if alpha > 5 and not (red > 245 and green > 245 and blue > 245):
                content_pixels += 1
    
    return content_pixels

