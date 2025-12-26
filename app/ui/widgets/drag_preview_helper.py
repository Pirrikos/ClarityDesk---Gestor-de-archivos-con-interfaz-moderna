"""
DragPreviewHelper - Helper for creating drag preview images.

Generates composite preview images for multiple file drag operations.
"""

import os
from typing import Optional

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QFileIconProvider

from app.services.icon_service import IconService
from app.services.preview_file_extensions import (
    normalize_extension,
    is_previewable_image,
    validate_file_for_preview
)
from app.services.icon_renderer import render_image_preview
from app.services.preview_service import get_windows_shell_icon
from app.ui.utils.font_manager import FontManager


def create_multi_file_preview(
    file_paths: list[str],
    icon_service: IconService,
    base_size: QSize = QSize(48, 48)
) -> QPixmap:
    """
    Create composite preview image for multiple files.
    
    Args:
        file_paths: List of file paths to include in preview.
        icon_service: IconService for getting file icons.
        base_size: Base size for individual icons.
    
    Returns:
        Composite pixmap showing multiple file icons.
    """
    if not file_paths:
        return QPixmap()
    
    if len(file_paths) == 1:
        return _create_single_file_preview(file_paths[0], icon_service, base_size)
    
    return _create_composite_preview(file_paths, icon_service, base_size)


def _create_single_file_preview(
    file_path: str,
    icon_service: IconService,
    size: QSize
) -> QPixmap:
    """Create preview for single file."""
    icon = icon_service.get_file_icon(file_path, size)
    pixmap = icon.pixmap(size)
    if pixmap.isNull():
        pixmap = QPixmap(size)
        pixmap.fill(QColor(200, 200, 200))
    return pixmap


def _create_composite_preview(
    file_paths: list[str],
    icon_service: IconService,
    base_size: QSize
) -> QPixmap:
    """
    Create composite preview showing multiple file icons.
    
    Mejora: Muestra cantidad de archivos más claramente con badge siempre visible
    si hay más de 1 archivo.
    """
    max_icons = 4
    icons_to_show = file_paths[:max_icons]
    
    icon_size = QSize(32, 32)
    offset = 8
    composite_width = icon_size.width() + (offset * (len(icons_to_show) - 1))
    composite_height = icon_size.height() + 20
    
    composite = QPixmap(composite_width, composite_height)
    composite.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(composite)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    for idx, file_path in enumerate(icons_to_show):
        icon = icon_service.get_file_icon(file_path, icon_size)
        pixmap = icon.pixmap(icon_size)
        
        if pixmap.isNull():
            pixmap = QPixmap(icon_size)
            pixmap.fill(QColor(200, 200, 200))
        
        x_pos = idx * offset
        painter.drawPixmap(x_pos, 0, pixmap)
    
    # Mostrar badge siempre si hay más de 1 archivo (mejora feedback visual)
    if len(file_paths) > 1:
        _draw_count_badge(painter, len(file_paths), composite_width, composite_height)
    
    painter.end()
    return composite


def _draw_count_badge(
    painter: QPainter,
    total_count: int,
    width: int,
    height: int
) -> None:
    """
    Draw badge showing total file count.
    
    Mejora: Badge más visible con fondo semitransparente y texto más legible.
    """
    badge_size = 22
    badge_x = width - badge_size - 2
    badge_y = height - badge_size - 2
    
    # Fondo semitransparente para mejor visibilidad
    painter.setBrush(QColor(0, 120, 215, 220))
    painter.setPen(QPen(QColor(255, 255, 255, 255), 1))
    painter.drawEllipse(badge_x, badge_y, badge_size, badge_size)
    
    # Texto más legible
    painter.setPen(QColor(255, 255, 255))
    font = FontManager.create_font("Segoe UI", FontManager.SIZE_SMALL, QFont.Weight.Bold)
    painter.setFont(font)
    count_text = str(total_count) if total_count < 100 else "99+"
    painter.drawText(
        badge_x, badge_y, badge_size, badge_size,
        Qt.AlignmentFlag.AlignCenter,
        count_text
    )


def get_drag_preview_pixmap(
    file_paths: list[str],
    icon_service: IconService,
    fallback_icon_pixmap: Optional[QPixmap] = None
) -> QPixmap:
    """
    Get unified drag preview pixmap for any file type.
    
    Unifies behavior for all file types:
    - Images: large preview (96-128px maintaining proportion)
    - Other files: icon scaled to consistent visual size (96-112px)
    - Multiple files: composite of icons
    
    Args:
        file_paths: List of file paths to drag.
        icon_service: IconService for getting file icons.
        fallback_icon_pixmap: Optional fallback pixmap (used by tile view).
    
    Returns:
        Preview pixmap for drag operation.
    """
    if len(file_paths) > 1:
        if icon_service:
            return create_multi_file_preview(file_paths, icon_service, QSize(48, 48))
        if fallback_icon_pixmap and not fallback_icon_pixmap.isNull():
            return fallback_icon_pixmap
        return QPixmap()
    
    if len(file_paths) == 1:
        file_path = file_paths[0]
        ext = normalize_extension(file_path)
        
        if is_previewable_image(ext):
            is_valid, _ = validate_file_for_preview(file_path)
            if is_valid:
                try:
                    max_size = QSize(128, 128)
                    image_preview = render_image_preview(file_path, max_size)
                    
                    if not image_preview.isNull():
                        min_size = 96
                        if image_preview.width() < min_size and image_preview.height() < min_size:
                            scale_factor = min_size / max(image_preview.width(), image_preview.height())
                            new_width = int(image_preview.width() * scale_factor)
                            new_height = int(image_preview.height() * scale_factor)
                            image_preview = image_preview.scaled(
                                new_width, new_height,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
                        return image_preview
                except Exception:
                    pass
        
        if icon_service:
            try:
                high_res_size = QSize(256, 256)
                target_size = QSize(112, 112)
                icon_provider = QFileIconProvider()
                
                if os.path.isdir(file_path):
                    folder_pixmap = get_windows_shell_icon(file_path, high_res_size, icon_provider, scale_to_target=False)
                    
                    if not folder_pixmap.isNull():
                        file_icon_pixmap = folder_pixmap.scaled(
                            target_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    else:
                        icon = icon_service.get_folder_icon(file_path, target_size)
                        file_icon_pixmap = icon.pixmap(target_size)
                else:
                    file_pixmap = get_windows_shell_icon(file_path, high_res_size, icon_provider, scale_to_target=False)
                    
                    if not file_pixmap.isNull():
                        file_icon_pixmap = file_pixmap.scaled(
                            target_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    else:
                        icon = icon_service.get_file_icon(file_path, target_size)
                        file_icon_pixmap = icon.pixmap(target_size)
                
                if not file_icon_pixmap.isNull():
                    min_size = 96
                    if file_icon_pixmap.width() < min_size or file_icon_pixmap.height() < min_size:
                        scale_factor = min_size / max(file_icon_pixmap.width(), file_icon_pixmap.height())
                        new_width = int(file_icon_pixmap.width() * scale_factor)
                        new_height = int(file_icon_pixmap.height() * scale_factor)
                        file_icon_pixmap = file_icon_pixmap.scaled(
                            new_width, new_height,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    return file_icon_pixmap
            except Exception:
                pass
        
        if fallback_icon_pixmap and not fallback_icon_pixmap.isNull():
            min_size = 96
            if fallback_icon_pixmap.width() < min_size or fallback_icon_pixmap.height() < min_size:
                scale_factor = min_size / max(fallback_icon_pixmap.width(), fallback_icon_pixmap.height())
                new_width = int(fallback_icon_pixmap.width() * scale_factor)
                new_height = int(fallback_icon_pixmap.height() * scale_factor)
                return fallback_icon_pixmap.scaled(
                    new_width, new_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            return fallback_icon_pixmap
        
        if icon_service:
            return create_multi_file_preview(file_paths, icon_service, QSize(48, 48))
    
    return QPixmap()


def calculate_drag_hotspot(preview_pixmap: QPixmap) -> QPoint:
    """Calculate optimal hotspot for drag preview."""
    if preview_pixmap.width() > 64:
        return QPoint(preview_pixmap.width() // 2, preview_pixmap.height() // 3)
    return QPoint(preview_pixmap.width() // 2, preview_pixmap.height() // 2)

