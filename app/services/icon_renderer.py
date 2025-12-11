"""
IconRenderer - Icon rendering for different file types.

Handles rendering of PDF, Word, image, and SVG previews.

This module re-exports all public APIs for backward compatibility.
Actual implementations are in separate modules:
- icon_renderer_pdf.py: PDF preview rendering
- icon_renderer_docx.py: DOCX preview rendering
- icon_renderer_image.py: Image preview rendering
- icon_renderer_svg.py: SVG icon rendering
- icon_renderer_constants.py: Constants and mappings
"""

# Re-export public APIs for backward compatibility
from app.services.icon_renderer_constants import POPPLER_PATH, SVG_COLOR_MAP, SVG_ICON_MAP
from app.services.icon_renderer_docx import render_word_preview
from app.services.icon_renderer_image import render_image_preview
from app.services.icon_renderer_pdf import render_pdf_preview
from app.services.icon_renderer_svg import get_svg_for_extension, render_svg_icon

__all__ = [
    'POPPLER_PATH',
    'SVG_ICON_MAP',
    'SVG_COLOR_MAP',
    'render_pdf_preview',
    'render_word_preview',
    'render_image_preview',
    'get_svg_for_extension',
    'render_svg_icon',
]
