"""
IconRendererDOCX - DOCX preview rendering.

Handles rendering of Word document text content as preview.
"""

from docx import Document
from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap


def render_word_preview(path: str, size: QSize) -> QPixmap:
    """Render DOCX text content as preview."""
    try:
        doc = Document(path)
        lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        content = lines[:15]
        
        img = Image.new("RGB", (size.width(), size.height()), "white")
        draw = ImageDraw.Draw(img)
        
        y = 10
        for line in content:
            draw.text((10, y), line[:80], fill=(0, 0, 0))
            y += 14
            if y > size.height() - 12:
                break
        
        return QPixmap.fromImage(ImageQt(img))
    except Exception:
        return QPixmap()

