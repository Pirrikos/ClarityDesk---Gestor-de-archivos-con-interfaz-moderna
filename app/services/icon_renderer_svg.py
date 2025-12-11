"""
IconRendererSVG - SVG icon rendering.

Handles rendering of SVG assets with category-specific colors.
"""

import re
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.services.icon_renderer_constants import SVG_COLOR_MAP


def get_svg_for_extension(ext: str) -> str:
    """Return SVG filename for a given extension."""
    from app.services.icon_renderer_constants import SVG_ICON_MAP
    return SVG_ICON_MAP.get(ext.lower(), "generic.svg")


def render_svg_icon(svg_name: str, size: QSize, ext: str = "") -> QPixmap:
    """Render an SVG asset to a pixmap of the given size with category-specific color."""
    if size.width() <= 0 or size.height() <= 0:
        size = QSize(120, 106)
    
    base_path = (
        Path(__file__).resolve()
        .parent.parent.parent
        / "assets"
        / "icons"
    )
    
    svg_path = base_path / svg_name
    pix = QPixmap(size)
    
    if not svg_path.exists():
        pix.fill(QColor(200, 200, 200))  # Gris sólido si no existe
        return pix
    
    try:
        # Leer y transformar el SVG de Heroicons para Qt
        svg_content = svg_path.read_text(encoding='utf-8')
        
        # Obtener color para este tipo de SVG
        svg_color = SVG_COLOR_MAP.get(svg_name, QColor(127, 140, 141))
        color_hex = f"#{svg_color.red():02x}{svg_color.green():02x}{svg_color.blue():02x}"
        
        # Transformar el SVG:
        # 1. Eliminar class="..." (no soportado por Qt)
        svg_transformed = re.sub(r'\s+class="[^"]*"', '', svg_content)
        # 2. Reemplazar stroke="currentColor" con color real
        svg_transformed = svg_transformed.replace('stroke="currentColor"', f'stroke="{color_hex}"')
        # 3. Cambiar fill="none" a fill="transparent" (mejor soporte en Qt)
        svg_transformed = svg_transformed.replace('fill="none"', 'fill="transparent"')
        # 4. Aumentar stroke-width para mejor visibilidad
        svg_transformed = re.sub(r'stroke-width="[^"]*"', 'stroke-width="2"', svg_transformed)
        
        # Crear renderer desde contenido transformado
        svg_bytes = QByteArray(svg_transformed.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes)
        
        if not renderer.isValid():
            pix.fill(QColor(200, 200, 200))
            return pix
        
        # Fondo TRANSPARENTE para que los iconos SVG floten igual que los de Windows
        pix.fill(Qt.GlobalColor.transparent)
        
        # Renderizar el SVG
        painter = QPainter(pix)
        if painter.isActive():
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            renderer.render(painter)
        painter.end()
        
        # NO validar vacío para SVGs de Heroicons - son mayoritariamente fondo con líneas
        # El renderer.isValid() ya garantiza que el SVG cargó correctamente
        
        return pix
    except Exception:
        pix.fill(QColor(200, 200, 200))
        return pix

