"""
IconRendererSVG - SVG icon rendering.

Handles rendering of SVG assets with category-specific colors.
"""

import os
import re

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.services.icon_renderer_constants import SVG_COLOR_MAP
from app.services.icon_path_utils import get_icons_dir


def get_svg_for_extension(ext: str) -> str:
    """Return SVG filename for a given extension."""
    from app.services.icon_renderer_constants import SVG_ICON_MAP
    return SVG_ICON_MAP.get(ext.lower(), "generic.svg")


def render_svg_icon(svg_name: str, size: QSize, ext: str = "") -> QPixmap:
    """Render an SVG asset to a pixmap of the given size with category-specific color."""
    if size.width() <= 0 or size.height() <= 0:
        size = QSize(120, 106)
    
    icons_dir = get_icons_dir()
    svg_path = os.path.join(icons_dir, svg_name)
    
    pix = QPixmap(size)
    
    if not os.path.exists(svg_path):
        pix.fill(QColor(200, 200, 200))  # Gris sólido si no existe
        return pix
    
    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
    except Exception:
        pix.fill(QColor(200, 200, 200))
        return pix
    
    try:
        svg_color = SVG_COLOR_MAP.get(svg_name, QColor(127, 140, 141))
        color_hex = f"#{svg_color.red():02x}{svg_color.green():02x}{svg_color.blue():02x}"
        
        svg_transformed = re.sub(r'\s+class="[^"]*"', '', svg_content)
        svg_transformed = svg_transformed.replace('stroke="currentColor"', f'stroke="{color_hex}"')
        svg_transformed = svg_transformed.replace('fill="none"', 'fill="transparent"')
        svg_transformed = re.sub(r'stroke-width="[^"]*"', 'stroke-width="2"', svg_transformed)
        
        svg_bytes = QByteArray(svg_transformed.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes)
        
        if not renderer.isValid():
            pix.fill(QColor(200, 200, 200))
            return pix
        
        # Fondo transparente para que los iconos SVG floten igual que los de Windows
        pix.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pix)
        if painter.isActive():
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            renderer.render(painter)
        painter.end()
        
        return pix
    except Exception:
        pix.fill(QColor(200, 200, 200))
        return pix

