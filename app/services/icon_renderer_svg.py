"""
IconRendererSVG - SVG icon rendering.

Handles rendering of SVG assets with category-specific colors.
"""

import re
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.core.logger import get_logger
from app.services.icon_renderer_constants import SVG_COLOR_MAP

logger = get_logger(__name__)


def get_svg_for_extension(ext: str) -> str:
    """Return SVG filename for a given extension."""
    from app.services.icon_renderer_constants import SVG_ICON_MAP
    return SVG_ICON_MAP.get(ext.lower(), "generic.svg")


def render_svg_icon(svg_name: str, size: QSize, ext: str = "") -> QPixmap:
    """Render an SVG asset to a pixmap of the given size with category-specific color."""
    # Validar y corregir tamaño inválido
    if size.width() <= 0 or size.height() <= 0:
        logger.warning(f"Invalid size {size} for {svg_name}, using default (120x106)")
        size = QSize(120, 106)

    # Validar tamaño máximo para evitar problemas de memoria
    max_size = 4096
    if size.width() > max_size or size.height() > max_size:
        logger.warning(f"Size {size} exceeds maximum {max_size} for {svg_name}, clamping")
        size = QSize(min(size.width(), max_size), min(size.height(), max_size))

    base_path = (
        Path(__file__).resolve()
        .parent.parent.parent
        / "assets"
        / "icons"
    )

    svg_path = base_path / svg_name
    pix = QPixmap(size)

    # Verificar existencia del archivo
    if not svg_path.exists():
        logger.error(f"SVG file not found: {svg_path}")
        pix.fill(QColor(200, 200, 200))
        return pix

    try:
        # Leer contenido del archivo SVG
        svg_content = svg_path.read_text(encoding='utf-8')

        # Validar que el contenido no esté vacío
        if not svg_content.strip():
            logger.error(f"SVG file is empty: {svg_path}")
            pix.fill(QColor(200, 200, 200))
            return pix

        # Obtener color para este tipo de SVG
        svg_color = SVG_COLOR_MAP.get(svg_name, QColor(127, 140, 141))
        color_hex = f"#{svg_color.red():02x}{svg_color.green():02x}{svg_color.blue():02x}"

        # Transformar el SVG de Heroicons para Qt
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

        # Validar que el renderer sea válido
        if not renderer.isValid():
            logger.error(f"SVG renderer invalid for: {svg_name}")
            logger.debug(f"Transformed SVG content (first 500 chars):\n{svg_transformed[:500]}...")
            pix.fill(QColor(200, 200, 200))
            return pix

        # Fondo TRANSPARENTE para que los iconos SVG floten igual que los de Windows
        pix.fill(Qt.GlobalColor.transparent)

        # Renderizar el SVG
        painter = QPainter(pix)

        if not painter.isActive():
            logger.error(f"QPainter not active for: {svg_name}")
            painter.end()
            pix.fill(QColor(200, 200, 200))
            return pix

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        renderer.render(painter)
        painter.end()

        logger.debug(f"Successfully rendered SVG: {svg_name} at size {size}")

        # NO validar vacío para SVGs de Heroicons - son mayoritariamente fondo con líneas
        # El renderer.isValid() ya garantiza que el SVG cargó correctamente

        return pix

    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error reading {svg_name}: {e}")
        pix.fill(QColor(200, 200, 200))
        return pix
    except OSError as e:
        logger.error(f"OS error reading {svg_name}: {e}")
        pix.fill(QColor(200, 200, 200))
        return pix
    except Exception as e:
        logger.error(f"Unexpected error rendering {svg_name}: {e}", exc_info=True)
        pix.fill(QColor(200, 200, 200))
        return pix

