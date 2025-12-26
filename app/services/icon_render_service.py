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

    def _is_valid_pixmap(self, pixmap: QPixmap) -> bool:
        """Validar pixmap según R16: no nulo, no 0x0, válido visualmente."""
        if not pixmap or pixmap.isNull():
            return False
        if pixmap.width() <= 0 or pixmap.height() <= 0:
            return False
        return True

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
            # R16: Validar y aplicar fallback inmediato si inválido
            if not self._is_valid_pixmap(raw_pixmap):
                folder_icon = self._icon_service.get_folder_icon(path, size)
                fallback_pixmap = folder_icon.pixmap(size) if folder_icon and not folder_icon.isNull() else QPixmap()
                if self._is_valid_pixmap(fallback_pixmap):
                    raw_pixmap = fallback_pixmap
                else:
                    # Fallback a icono genérico del sistema
                    generic_icon = self._icon_provider.icon(QFileIconProvider.IconType.Folder)
                    raw_pixmap = generic_icon.pixmap(size) if generic_icon and not generic_icon.isNull() else QPixmap()
        else:
            raw_pixmap = get_file_preview(path, size, self._icon_provider)
        
        # R16: Validar antes de normalizar
        if not self._is_valid_pixmap(raw_pixmap):
            _, ext = os.path.splitext(path)
            return safe_pixmap(QPixmap(), size.width(), ext)
        
        normalized = normalize_for_list(raw_pixmap, size)
        # R16: Validar después de normalizar
        if not self._is_valid_pixmap(normalized):
            _, ext = os.path.splitext(path)
            return safe_pixmap(QPixmap(), size.width(), ext)
        
        # Apply fallback SVG if pixmap is NULL
        _, ext = os.path.splitext(path)
        return safe_pixmap(normalized, size.width(), ext)

    def _get_folder_preview(self, path: str, size: QSize) -> QPixmap:
        """Get high-resolution folder preview with fallbacks and normalization (R16 validated)."""
        high_res_size = QSize(256, 256)
        raw_pixmap = get_windows_shell_icon(path, high_res_size, self._icon_provider, scale_to_target=False)
        raw_pixmap = self._scale_folder_icon(raw_pixmap, size)
        raw_pixmap = self._apply_folder_fallbacks(path, raw_pixmap, size)
        
        # R16: Validar antes de normalizar
        if not self._is_valid_pixmap(raw_pixmap):
            return QPixmap()
        
        normalized = apply_visual_normalization(raw_pixmap, size)
        
        # R16: Validar después de normalizar
        if not self._is_valid_pixmap(normalized):
            return QPixmap()
        
        return normalized

    def _scale_folder_icon(self, raw_pixmap: QPixmap, target_size: QSize) -> QPixmap:
        """Scale folder icon from high-res to target size with smooth transformation (R16 validated)."""
        # R16: Validar pixmap antes de escalar
        if not self._is_valid_pixmap(raw_pixmap):
            return QPixmap()
        
        if raw_pixmap.width() != target_size.width() or raw_pixmap.height() != target_size.height():
            scaled = raw_pixmap.scaled(
                target_size.width(), target_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            # R16: Validar después de escalar
            if not self._is_valid_pixmap(scaled):
                return QPixmap()
            return scaled
        return raw_pixmap

    def _apply_folder_fallbacks(self, path: str, raw_pixmap: QPixmap, size: QSize) -> QPixmap:
        """Apply fallback methods if folder icon is invalid (R16)."""
        # R16: Validar pixmap antes de continuar
        if self._is_valid_pixmap(raw_pixmap):
            return raw_pixmap
        
        # Fallback 1: IconService sin tamaño específico
        folder_icon = self._icon_service.get_folder_icon(path, None)
        if folder_icon and not folder_icon.isNull():
            raw_pixmap = self._get_best_quality_pixmap(folder_icon, size)
            if self._is_valid_pixmap(raw_pixmap):
                return raw_pixmap
        
        # Fallback 2: IconService con tamaño específico
        folder_icon = self._icon_service.get_folder_icon(path, size)
        if folder_icon and not folder_icon.isNull():
            raw_pixmap = folder_icon.pixmap(size)
            if self._is_valid_pixmap(raw_pixmap):
                return raw_pixmap
        
        # Fallback 3: Icono genérico del sistema
        generic_folder_icon = self._icon_provider.icon(QFileIconProvider.IconType.Folder)
        if generic_folder_icon and not generic_folder_icon.isNull():
            raw_pixmap = generic_folder_icon.pixmap(size)
            if self._is_valid_pixmap(raw_pixmap):
                return raw_pixmap
        
        # Último recurso: retornar pixmap vacío (será manejado por safe_pixmap)
        return QPixmap()

    def _get_best_quality_pixmap(self, icon, target_size: QSize) -> QPixmap:
        """Get pixmap at best available quality, scaling to fill exact size (R16 validated)."""
        if not icon or icon.isNull():
            return QPixmap()
        
        available_sizes = icon.availableSizes()
        
        if available_sizes:
            best_size = max(available_sizes, key=lambda s: s.width() * s.height())
            pixmap = icon.pixmap(best_size)
            
            # R16: Validar pixmap antes de escalar
            if not self._is_valid_pixmap(pixmap):
                return QPixmap()
            
            if pixmap.width() != target_size.width() or pixmap.height() != target_size.height():
                # Use SmoothTransformation for high quality (like PDFs)
                pixmap = pixmap.scaled(
                    target_size.width(), target_size.height(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                # R16: Validar después de escalar
                if not self._is_valid_pixmap(pixmap):
                    return QPixmap()
            return pixmap
        else:
            high_dpi_size = QSize(target_size.width() * 2, target_size.height() * 2)
            pixmap_2x = icon.pixmap(high_dpi_size)
            
            # R16: Validar antes de escalar
            if not self._is_valid_pixmap(pixmap_2x):
                return QPixmap()
            
            scaled = pixmap_2x.scaled(
                target_size.width(), target_size.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            # R16: Validar después de escalar
            if not self._is_valid_pixmap(scaled):
                return QPixmap()
            return scaled

