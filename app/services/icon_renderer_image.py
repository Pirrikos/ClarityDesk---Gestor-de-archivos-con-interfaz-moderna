"""
IconRendererImage - Image preview rendering.

Handles rendering of image files as thumbnails.
"""

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap


def render_image_preview(path: str, size: QSize) -> QPixmap:
    """Render image file as preview (thumbnail)."""
    try:
        img = Image.open(path)
        
        if img.mode == 'RGBA':
            pass
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        img.thumbnail((size.width(), size.height()), Image.Resampling.LANCZOS)
        return QPixmap.fromImage(ImageQt(img))
    except Exception:
        return QPixmap()

