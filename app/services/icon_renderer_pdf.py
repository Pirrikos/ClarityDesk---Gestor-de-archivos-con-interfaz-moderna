"""
IconRendererPDF - PDF preview rendering.

Handles rendering of PDF first page as preview.
"""

from pdf2image import convert_from_path
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap

from app.services.icon_renderer_constants import POPPLER_PATH


def render_pdf_preview(path: str, size: QSize) -> QPixmap:
    """Render first page of PDF as preview."""
    try:
        pages = convert_from_path(
            path, dpi=180, first_page=1, last_page=1, poppler_path=str(POPPLER_PATH)
        )
        if not pages:
            return QPixmap()
        
        pixmap = QPixmap.fromImage(ImageQt(pages[0]))
        if pixmap.isNull():
            return QPixmap()
        
        if pixmap.width() != size.width() or pixmap.height() != size.height():
            pixmap = pixmap.scaled(
                size.width(), size.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
        
        return pixmap
    except Exception:
        return QPixmap()

