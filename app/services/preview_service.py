"""
PreviewService - File preview generation utilities.

Provides utility functions for file preview generation including scaling and SVG fallback logic.
For PDF/DOCX preview rendering, use PreviewPdfService directly.
"""

import os
from pathlib import Path

from PySide6.QtCore import QFileInfo, QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileIconProvider

from app.services.icon_processor import has_excessive_whitespace
from app.services.icon_renderer import (
    get_svg_for_extension,
    render_image_preview,
    render_svg_icon,
)
from app.services.windows_icon_converter import hicon_to_qpixmap_at_size
from app.services.icon_extraction_fallbacks import (
    get_icon_via_extracticon,
    get_icon_via_qicon,
)
from app.services.windows_icon_extractor import get_icon_via_imagelist
from app.services.preview_scaling import scale_pixmap_to_size, scale_if_needed
from app.services.preview_file_extensions import normalize_extension, validate_file_for_preview, validate_pixmap



def get_file_preview(
    path: str, 
    size: QSize, 
    icon_provider
) -> QPixmap:
    """Get file preview (real PDF/DOCX preview or Windows shell icon)."""
    return _get_file_preview_impl(path, size, icon_provider)


def _get_file_preview_impl(path: str, size: QSize, icon_provider) -> QPixmap:
    """Internal implementation of get_file_preview."""
    # R13: Early existence validation
    is_valid, error_msg = validate_file_for_preview(path)
    if not is_valid:
        return QPixmap()  # R4: Fallback
    
    if os.path.isdir(path):
        return _get_folder_preview_impl(path, size, icon_provider)
    
    # Para accesos directos (.lnk), verificar si apuntan a una carpeta
    # R11: Normalize extension in single entry point
    ext = normalize_extension(path)
    if ext == '.lnk':
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(path)
            target_path = shortcut.Targetpath
            if target_path and os.path.exists(target_path) and os.path.isdir(target_path):
                # Si el acceso directo apunta a una carpeta, usar el icono de carpeta
                return _get_folder_preview_impl(target_path, size, icon_provider)
        except Exception:
            pass  # Si falla la resolución, continuar con la lógica normal
    
    return _get_file_preview_impl_helper(path, size, icon_provider)


def _get_folder_preview_impl(path: str, size: QSize, icon_provider) -> QPixmap:
    """Get folder preview with high-resolution Windows icons, never SVG."""
    high_res_size = QSize(256, 256)
    pixmap = get_windows_shell_icon(path, high_res_size, icon_provider, scale_to_target=False)
    
    if not pixmap.isNull() and (pixmap.width() != size.width() or pixmap.height() != size.height()):
        pixmap = pixmap.scaled(
            size.width(), size.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    if pixmap.isNull():
        qfile_info = QFileInfo(path)
        folder_icon = icon_provider.icon(qfile_info)
        pixmap = folder_icon.pixmap(size)
    
    if pixmap.isNull():
        generic_folder_icon = icon_provider.icon(QFileIconProvider.IconType.Folder)
        pixmap = generic_folder_icon.pixmap(size)
    
    return pixmap


def _get_file_preview_impl_helper(path: str, size: QSize, icon_provider) -> QPixmap:
    """Get file preview with SVG fallback logic."""
    # R11: Normalize extension in single entry point
    ext = normalize_extension(path)
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.ico'}
    
    if ext in image_extensions:
        return render_image_preview(path, size)
    
    # Ejecutables: siempre usar SVG exe.svg en lugar del icono de Windows
    # Nota: .lnk NO está incluido aquí - los accesos directos usan iconos nativos de Windows
    executable_extensions = {'.exe', '.msi', '.bat', '.cmd', '.ps1', '.sh'}
    if ext in executable_extensions:
        svg_name = get_svg_for_extension(ext)
        svg_pixmap = render_svg_icon(svg_name, size, ext)
        if validate_pixmap(svg_pixmap):
            return svg_pixmap
    
    pixmap = get_windows_shell_icon(path, size, icon_provider)
    
    # No usar fallback SVG para imágenes, documentos Word/PDF y accesos directos (.lnk)
    # (usar iconos nativos de Windows)
    document_extensions = {'.doc', '.docx', '.pdf'}
    skip_svg_fallback = ext in image_extensions or ext in document_extensions or ext == '.lnk'
    
    if os.path.isdir(path):
        qfile_info = QFileInfo(path)
        folder_icon = icon_provider.icon(qfile_info)
        return folder_icon.pixmap(size)
    
    if not skip_svg_fallback and not pixmap.isNull() and has_excessive_whitespace(pixmap, threshold=0.4):
        svg_name = get_svg_for_extension(ext)
        svg_pixmap = render_svg_icon(svg_name, size, ext)
        # R14: Validate pixmap before using
        if validate_pixmap(svg_pixmap):
            return svg_pixmap
    
    # R14: Validate pixmap before scaling
    if not validate_pixmap(pixmap):
        return QPixmap()  # R4: Fallback
    
    scaled = scale_pixmap_to_size(pixmap, size)
    # R14: Validate scaled result
    if not validate_pixmap(scaled):
        return QPixmap()  # R4: Fallback
    
    return scaled


def get_windows_shell_icon(path: str, size: QSize, icon_provider, scale_to_target: bool = True) -> QPixmap:
    """Get native Windows shell icon at maximum resolution."""
    try:
        icon_size = max(size.width(), size.height())
        
        pixmap = get_icon_via_imagelist(path, icon_size, hicon_to_qpixmap_at_size)
        if not pixmap.isNull():
            if _has_visible_content(pixmap):
                if scale_to_target and (pixmap.width() != size.width() or pixmap.height() != size.height()):
                    return scale_if_needed(pixmap, size)
                return pixmap
        
        pixmap = get_icon_via_extracticon(path, size, hicon_to_qpixmap_at_size)
        if not pixmap.isNull() and _has_visible_content(pixmap):
            return pixmap
        
        pixmap = get_icon_via_qicon(path, size, icon_provider)
        if not pixmap.isNull() and _has_visible_content(pixmap):
            return pixmap
        
        return QPixmap()
    except Exception:
        return QPixmap()


def _has_visible_content(pixmap: QPixmap) -> bool:
    """Verificar si el pixmap tiene contenido visible (no completamente transparente)."""
    if pixmap.isNull():
        return False
    
    image = pixmap.toImage()
    if image.isNull():
        return False
    
    width = image.width()
    height = image.height()
    
    if width == 0 or height == 0:
        return False
    
    check_points = [
        (width // 2, height // 2),
        (width // 4, height // 4),
        (3 * width // 4, 3 * height // 4),
    ]
    
    visible_count = 0
    for x, y in check_points:
        if 0 <= x < width and 0 <= y < height:
            color = image.pixelColor(x, y)
            if color.alpha() > 50:
                visible_count += 1
    
    return visible_count > 0
