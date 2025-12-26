"""
IconRendererImage - Image preview rendering.

Handles rendering of image files as thumbnails.

R12: Hard file size limits prevent preview of oversized files.
R13: Early existence validation before rendering.
R14: Pixmap validation before returning.
"""

from PIL import Image, ImageOps
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap

from app.services.preview_file_extensions import validate_file_for_preview, validate_pixmap


def _normalize_exif_orientation(img: Image.Image) -> Image.Image:
    """
    Normaliza la orientación EXIF de la imagen aplicando la rotación/espejo real.
    
    Lee el metadato EXIF de orientación, aplica la transformación al bitmap
    y devuelve una imagen ya normalizada sin metadatos de orientación.
    """
    try:
        return ImageOps.exif_transpose(img)
    except (AttributeError, TypeError, ValueError):
        return img


def render_image_preview(path: str, size: QSize) -> QPixmap:
    """
    Render image file as preview (thumbnail).
    
    R12: Hard file size limits prevent preview of oversized files.
    R13: Early existence validation before rendering.
    R14: Pixmap validation before returning.
    """
    # R13: Early existence and type validation
    # R12: Hard size limit check
    is_valid, error_msg = validate_file_for_preview(path)
    if not is_valid:
        return QPixmap()  # R4: Fallback
    
    try:
        img = Image.open(path)
        
        img = _normalize_exif_orientation(img)
        
        if img.mode == 'RGBA':
            pass
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        img.thumbnail((size.width(), size.height()), Image.Resampling.LANCZOS)
        pixmap = QPixmap.fromImage(ImageQt(img))
        
        # R14: Validate pixmap before returning
        if not validate_pixmap(pixmap):
            return QPixmap()  # R4: Fallback
        
        return pixmap
    except Exception:
        return QPixmap()  # R4: Fallback

