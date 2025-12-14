"""
IconRenderService - File preview rendering with visual normalization.

Handles preview generation with visual normalization, fallbacks, and view-specific
optimizations (grid vs list). Uses IconService for raw Windows icons.
"""

import os
from typing import Optional

from PySide6.QtCore import QFileInfo, QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileIconProvider

from app.services.icon_service import IconService
from app.services.icon_normalizer import apply_visual_normalization, normalize_for_list
from app.services.preview_service import get_file_preview, get_windows_shell_icon
from app.services.icon_fallback_helper import safe_pixmap


class IconRenderService:
    """
    Service for rendering file previews with visual normalization.
    
    Handles previews (PDF/DOCX), visual normalization, grid/list differences,
    and visual fallbacks. Uses IconService internally for raw Windows icons.
    """

    def __init__(self, icon_service: IconService):
        """
        Initialize IconRenderService with IconService dependency.
        
        Args:
            icon_service: IconService instance for raw Windows icons
        """
        self._icon_service = icon_service
        self._icon_provider = QFileIconProvider()

    def get_file_preview(self, path: str, size: QSize) -> QPixmap:
        """
        Get file or folder preview with visual normalization.
        
        Returns preview with 90% scale, rounded corners, and fallbacks.
        Optimized for grid view display.
        
        Args:
            path: File or folder path
            size: Target size for preview
            
        Returns:
            QPixmap with normalized visual appearance
        """
        if os.path.isdir(path):
            return self._get_folder_preview(path, size)
        else:
            raw_pixmap = get_file_preview(path, size, self._icon_provider)
            normalized = apply_visual_normalization(raw_pixmap, size)
            # Apply fallback SVG if pixmap is NULL
            _, ext = os.path.splitext(path)
            return safe_pixmap(normalized, size.width(), ext)

    def get_file_preview_list(self, path: str, size: QSize) -> QPixmap:
        """
        Get file or folder preview optimized for list view.
        
        Returns preview with 100% scale, no overlay, no rounded corners.
        Optimized for list view display.
        
        Args:
            path: File or folder path
            size: Target size for preview
            
        Returns:
            QPixmap optimized for list view
        """
        # Handle folders - use high-resolution Windows shell icons, never SVG fallback
        if os.path.isdir(path):
            raw_pixmap = get_windows_shell_icon(path, size, self._icon_provider)
            # Fallback to standard folder icon if high-res method fails
            if raw_pixmap.isNull():
                folder_icon = self._icon_service.get_folder_icon(path, size)
                raw_pixmap = folder_icon.pixmap(size)
        else:
            raw_pixmap = get_file_preview(path, size, self._icon_provider)
        
        normalized = normalize_for_list(raw_pixmap, size)
        # Apply fallback SVG if pixmap is NULL
        _, ext = os.path.splitext(path)
        return safe_pixmap(normalized, size.width(), ext)

    def _get_folder_preview(self, path: str, size: QSize) -> QPixmap:
        """Get high-resolution folder preview with fallbacks and normalization."""
        high_res_size = QSize(256, 256)
        raw_pixmap = get_windows_shell_icon(path, high_res_size, self._icon_provider, scale_to_target=False)
        raw_pixmap = self._scale_folder_icon(raw_pixmap, size)
        raw_pixmap = self._apply_folder_fallbacks(path, raw_pixmap, size)
        return apply_visual_normalization(raw_pixmap, size)

    def _scale_folder_icon(self, raw_pixmap: QPixmap, target_size: QSize) -> QPixmap:
        """Scale folder icon from high-res to target size with smooth transformation."""
        if not raw_pixmap.isNull() and (raw_pixmap.width() != target_size.width() or raw_pixmap.height() != target_size.height()):
            return raw_pixmap.scaled(
                target_size.width(), target_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        return raw_pixmap

    def _apply_folder_fallbacks(self, path: str, raw_pixmap: QPixmap, size: QSize) -> QPixmap:
        """Apply fallback methods if folder icon is null."""
        if not raw_pixmap.isNull():
            return raw_pixmap
        
        folder_icon = self._icon_service.get_folder_icon(path, None)
        raw_pixmap = self._get_best_quality_pixmap(folder_icon, size)
        
        if raw_pixmap.isNull():
            folder_icon = self._icon_service.get_folder_icon(path, size)
            raw_pixmap = folder_icon.pixmap(size)
        
        if raw_pixmap.isNull():
            generic_folder_icon = self._icon_provider.icon(QFileIconProvider.IconType.Folder)
            raw_pixmap = generic_folder_icon.pixmap(size)
        
        return raw_pixmap

    def _get_best_quality_pixmap(self, icon, target_size: QSize) -> QPixmap:
        """Get pixmap at best available quality, scaling to fill exact size."""
        available_sizes = icon.availableSizes()
        
        if available_sizes:
            best_size = max(available_sizes, key=lambda s: s.width() * s.height())
            pixmap = icon.pixmap(best_size)
            
            if pixmap.width() != target_size.width() or pixmap.height() != target_size.height():
                # Use SmoothTransformation for high quality (like PDFs)
                pixmap = pixmap.scaled(
                    target_size.width(), target_size.height(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            return pixmap
        else:
            high_dpi_size = QSize(target_size.width() * 2, target_size.height() * 2)
            pixmap_2x = icon.pixmap(high_dpi_size)
            return pixmap_2x.scaled(
                target_size.width(), target_size.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

