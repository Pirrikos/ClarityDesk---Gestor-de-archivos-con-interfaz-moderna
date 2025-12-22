"""FolderTreeIconUtils - Utilidades compartidas para iconos del sidebar."""

from pathlib import Path as PathLib
from PySide6.QtCore import QByteArray, QRect, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

FOLDER_ICON_SIZE = QSize(32, 32)


def get_assets_icons_path() -> PathLib:
    return PathLib(__file__).resolve().parents[3] / 'assets' / 'icons'


def load_folder_icon_svg(svg_path: PathLib, size: QSize = QSize(32, 32)) -> QIcon:
    if not svg_path.exists():
        return QIcon()
    
    try:
        with open(str(svg_path), 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
        if not renderer.isValid():
            return QIcon()
        
        # Renderizar a 4x para bordes delgados y detalles finos
        scale_factor = 4
        render_size = QSize(size.width() * scale_factor, size.height() * scale_factor)
        pixmap = QPixmap(render_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        if painter.isActive():
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering, True)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
            painter.setViewport(0, 0, render_size.width(), render_size.height())
            painter.setWindow(0, 0, render_size.width(), render_size.height())
            renderer.render(painter, QRect(0, 0, render_size.width(), render_size.height()))
        painter.end()
        
        final_pixmap = pixmap.scaled(
            size, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        icon = QIcon(final_pixmap)
        icon.addPixmap(pixmap, QIcon.Mode.Normal, QIcon.State.Off)
        return icon
    except Exception:
        return QIcon()


def load_folder_icon_with_fallback(size: QSize = QSize(32, 32)) -> QIcon:
    icons_path = get_assets_icons_path()
    svg_path = icons_path / 'folder icon.svg'
    
    if not svg_path.exists():
        svg_path = icons_path / 'folder_sidebar.svg'
    
    return load_folder_icon_svg(svg_path, size)

