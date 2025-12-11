"""
IconService - Windows native icon provider for files.

Provides native Windows icons for file paths with caching per extension.
Supports real PDF previews using Poppler.
Supports batch icon generation using QThread workers.
"""

import os
from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import QFileInfo, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFileIconProvider

from app.services.icon_normalizer import apply_visual_normalization, normalize_for_list
from app.services.preview_service import get_file_preview, get_windows_shell_icon
from app.services.windows_icon_converter import hicon_to_qpixmap_at_size
from app.services.icon_fallback_helper import safe_pixmap
from app.services.icon_batch_worker import IconBatchWorker


class IconService:
    """Service for providing native Windows file icons."""

    def __init__(self):
        """Initialize IconService with icon provider and cache."""
        self._icon_provider = QFileIconProvider()
        self._icon_cache: dict[str, QIcon] = {}
        self._icon_cache_mtime: dict[str, float] = {}  # Track file mtime for cache validation
        self._active_batch_worker: Optional[IconBatchWorker] = None

    def get_file_icon(self, file_path: str, size: QSize = None) -> QIcon:
        """Get native Windows icon for a file."""
        if not file_path or not os.path.isfile(file_path):
            return self._get_default_icon()

        _, ext = os.path.splitext(file_path)
        ext = ext.lower() if ext else ""

        cache_key = f"{ext}_{size.width() if size else 'default'}"
        
        # Check cache validity: verify file mtime hasn't changed
        if cache_key in self._icon_cache:
            cached_mtime = self._icon_cache_mtime.get(cache_key, 0)
            try:
                current_mtime = os.path.getmtime(file_path)
                if current_mtime == cached_mtime:
                    return self._icon_cache[cache_key]
                else:
                    # File changed, invalidate cache entry
                    del self._icon_cache[cache_key]
                    del self._icon_cache_mtime[cache_key]
            except (OSError, ValueError):
                # File doesn't exist or can't read mtime, invalidate cache
                if cache_key in self._icon_cache:
                    del self._icon_cache[cache_key]
                if cache_key in self._icon_cache_mtime:
                    del self._icon_cache_mtime[cache_key]

        qfile_info = QFileInfo(file_path)
        icon = self._icon_provider.icon(qfile_info)
        
        if size:
            pixmap = self._get_best_quality_pixmap(icon, size)
            icon = QIcon(pixmap)

        if ext:
            self._icon_cache[cache_key] = icon
            try:
                self._icon_cache_mtime[cache_key] = os.path.getmtime(file_path)
            except (OSError, ValueError):
                self._icon_cache_mtime[cache_key] = 0

        return icon

    def get_folder_icon(self, folder_path: str = None, size: QSize = None) -> QIcon:
        """Get native Windows icon for a folder."""
        if folder_path and os.path.isdir(folder_path):
            qfile_info = QFileInfo(folder_path)
            icon = self._icon_provider.icon(qfile_info)
        else:
            icon = self._icon_provider.icon(QFileIconProvider.IconType.Folder)

        if size:
            return QIcon(icon.pixmap(size))
        return icon

    def get_file_icon_pixmap(
        self, 
        file_path: str, 
        size: QSize, 
        device_pixel_ratio: float = 1.0
    ) -> QPixmap:
        """Get pixmap directly for maximum sharpness (avoids double scaling)."""
        if not file_path or not os.path.isfile(file_path):
            default_icon = self._get_default_icon()
            high_dpi_size = QSize(
                int(size.width() * device_pixel_ratio), 
                int(size.height() * device_pixel_ratio)
            )
            pixmap = default_icon.pixmap(high_dpi_size)
            pixmap.setDevicePixelRatio(device_pixel_ratio)
            return pixmap
        
        qfile_info = QFileInfo(file_path)
        icon = self._icon_provider.icon(qfile_info)
        
        high_dpi_size = QSize(
            int(size.width() * device_pixel_ratio), 
            int(size.height() * device_pixel_ratio)
        )
        
        pixmap = self._get_best_quality_pixmap(icon, high_dpi_size)
        pixmap.setDevicePixelRatio(device_pixel_ratio)
        return pixmap

    def get_file_preview(self, path: str, size: QSize) -> QPixmap:
        """Get file or folder preview (real PDF/DOCX preview or Windows shell icon)."""
        if os.path.isdir(path):
            return self._get_folder_preview(path, size)
        else:
            raw_pixmap = get_file_preview(path, size, self._icon_provider)
            normalized = apply_visual_normalization(raw_pixmap, size)
            # Aplicar fallback SVG si el pixmap es NULL
            _, ext = os.path.splitext(path)
            return safe_pixmap(normalized, size.width(), ext)
    
    def _get_folder_preview(self, path: str, size: QSize) -> QPixmap:
        """Get high-resolution folder preview with fallbacks."""
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
        
        folder_icon = self.get_folder_icon(path, None)
        raw_pixmap = self._get_best_quality_pixmap(folder_icon, size)
        
        if raw_pixmap.isNull():
            folder_icon = self.get_folder_icon(path, size)
            raw_pixmap = folder_icon.pixmap(size)
        
        if raw_pixmap.isNull():
            generic_folder_icon = self._icon_provider.icon(QFileIconProvider.IconType.Folder)
            raw_pixmap = generic_folder_icon.pixmap(size)
        
        return raw_pixmap
    
    def get_file_preview_list(self, path: str, size: QSize) -> QPixmap:
        """Get file or folder preview optimized for list view (no overlay, 100% scale)."""
        # Handle folders - use high-resolution Windows shell icons, never SVG fallback
        if os.path.isdir(path):
            raw_pixmap = get_windows_shell_icon(path, size, self._icon_provider)
            # Fallback to standard folder icon if high-res method fails
            if raw_pixmap.isNull():
                folder_icon = self.get_folder_icon(path, size)
                raw_pixmap = folder_icon.pixmap(size)
        else:
            raw_pixmap = get_file_preview(path, size, self._icon_provider)
        
        normalized = normalize_for_list(raw_pixmap, size)
        # Aplicar fallback SVG si el pixmap es NULL
        _, ext = os.path.splitext(path)
        return safe_pixmap(normalized, size.width(), ext)

    def _get_best_quality_pixmap(self, icon: QIcon, target_size: QSize) -> QPixmap:
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

    def _get_default_icon(self) -> QIcon:
        """Get default document icon when file icon unavailable."""
        return self._icon_provider.icon(QFileIconProvider.IconType.File)

    def generate_icons_batch_async(
        self,
        file_paths: List[str],
        size: QSize,
        on_finished: Callable[[List[Tuple[str, QPixmap]]], None],
        on_progress: Optional[Callable[[int], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Generate multiple icons asynchronously using QThread worker.
        
        Args:
            file_paths: List of file paths to generate icons for.
            size: Size for generated icons.
            on_finished: Callback called with list of (path, QPixmap) tuples when complete.
            on_progress: Optional callback called with progress percentage (0-100).
            on_error: Optional callback called with error message on failure.
        """
        # Cancel any existing worker
        if self._active_batch_worker:
            self._active_batch_worker.terminate()
            self._active_batch_worker.wait()
        
        worker = IconBatchWorker(file_paths, size, self._icon_provider)
        self._active_batch_worker = worker
        
        def handle_finished(results: List[Tuple[str, QPixmap]]) -> None:
            self._active_batch_worker = None
            on_finished(results)
        
        def handle_progress(progress_pct: int) -> None:
            if on_progress:
                on_progress(progress_pct)
        
        def handle_error(error_msg: str) -> None:
            self._active_batch_worker = None
            if on_error:
                on_error(error_msg)
            else:
                on_finished([])  # Return empty list on error
        
        worker.finished.connect(handle_finished)
        worker.progress.connect(handle_progress)
        worker.error.connect(handle_error)
        worker.start()

    def clear_cache(self) -> None:
        """Clear icon cache to free memory."""
        self._icon_cache.clear()
        self._icon_cache_mtime.clear()
