"""
ViewIconUtils - Utilities for loading view toggle icons.

Provides icon loading for grid/list view toggle buttons.
"""

import os

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.core.logger import get_logger
from app.services.icon_path_utils import get_icons_dir

logger = get_logger(__name__)

_icon_cache: dict[tuple[str, int, int, bool], QIcon] = {}


def load_view_icon(svg_name: str, size: QSize, checked: bool) -> QIcon:
    """
    Load SVG icon for view toggle buttons, adapting colors for theme.
    
    Args:
        svg_name: Name of SVG file (e.g., "grid.svg", "lista.svg")
        size: Icon size
        checked: True if button is checked (selected)
        
    Returns:
        QIcon with adapted colors, or empty QIcon if loading fails
    """
    cache_key = (svg_name, size.width(), size.height(), checked)
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]
    
    icons_dir = get_icons_dir()
    svg_path = os.path.join(icons_dir, svg_name)
    
    if not os.path.exists(svg_path):
        return QIcon()
    
    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
    except Exception:
        return QIcon()
    
    try:
        if checked:
            svg_content = svg_content.replace('fill="rgb(245,245,245)"', 'fill="transparent"')  # Fondo transparente
            svg_content = svg_content.replace('fill="rgb(255,255,255)"', 'fill="rgb(220, 220, 220)"')  # Gris claro sólido (no transparente)
            svg_content = svg_content.replace('stroke="rgb(255,255,255)"', 'stroke="rgb(220, 220, 220)"')  # Gris claro sólido (no transparente)
        else:
            # Evitar rgba() porque QSvgRenderer (SVG 1.1) no lo soporta correctamente.
            # Usamos rgb() + fill-opacity/stroke-opacity para semitransparencia.
            svg_content = svg_content.replace('fill="rgb(245,245,245)"', 'fill="transparent"')
            # Variantes de blanco en fill
            for white_fill in ('fill="rgb(255,255,255)"', 'fill="#FFFFFF"', 'fill="#ffffff"', 'fill="#fff"', 'fill="white"'):
                if white_fill in svg_content:
                    svg_content = svg_content.replace(white_fill, 'fill="rgb(255,255,255)" fill-opacity="0.7"')
            # Variantes de blanco en stroke
            for white_stroke in ('stroke="rgb(255,255,255)"', 'stroke="#FFFFFF"', 'stroke="#ffffff"', 'stroke="#fff"', 'stroke="white"'):
                if white_stroke in svg_content:
                    svg_content = svg_content.replace(white_stroke, 'stroke="rgb(255,255,255)" stroke-opacity="0.7"')
        
        svg_bytes = QByteArray(svg_content.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes)
        
        if not renderer.isValid():
            return QIcon()
        
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        
        icon = QIcon(pixmap)
        _icon_cache[cache_key] = icon
        return icon
    except Exception as e:
        logger.warning(f"No se pudo cargar icono {svg_name}: {e}")
        return QIcon()
