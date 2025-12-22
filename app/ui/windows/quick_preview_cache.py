"""
Quick Preview Cache - Preview caching for instant navigation.

Manages in-memory cache of preview pixmaps for adjacent files.
Includes mtime validation to detect file changes.
"""

import os
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap

from app.core.logger import get_logger
from app.services.preview_file_extensions import (
    PREVIEW_IMAGE_EXTENSIONS,
    PREVIEW_TEXT_EXTENSIONS,
    PREVIEW_PDF_DOCX_EXTENSIONS
)
from app.services.icon_render_service import IconRenderService

logger = get_logger(__name__)


class QuickPreviewCache:
    """Manages preview cache for quick navigation."""
    
    def __init__(self, preview_service, max_size: Optional[QSize] = None):
        """Initialize cache."""
        self._preview_service = preview_service
        self._max_size = max_size
        self._cache: dict[int, QPixmap] = {}
        self._cache_mtime: dict[int, float] = {}  # Track file mtime for cache validation
    
    def set_max_size(self, max_size: QSize) -> None:
        """Set maximum size for previews."""
        self._max_size = max_size
    
    def get_max_size(self) -> Optional[QSize]:
        """Get maximum size for previews."""
        return self._max_size
    
    def get_cached_pixmap(self, index: int, paths: list[str]) -> QPixmap:
        """Get pixmap from cache or generate and cache it."""
        if index < 0 or index >= len(paths) or not self._max_size:
            return QPixmap()
        
        path = paths[index]
        
        # Check cache validity: verify file mtime hasn't changed
        if index in self._cache:
            cached_mtime = self._cache_mtime.get(index, 0)
            try:
                if os.path.exists(path):
                    current_mtime = os.path.getmtime(path)
                    if current_mtime == cached_mtime:
                        return self._cache[index]
                    else:
                        # File changed, invalidate cache entry
                        self._invalidate_cache_entry(index)
                else:
                    # File doesn't exist, invalidate cache
                    self._invalidate_cache_entry(index)
            except (OSError, ValueError):
                # Can't read mtime, invalidate cache
                self._invalidate_cache_entry(index)
        
        try:
            ext = Path(path).suffix.lower()
            is_previewable_type = (
                ext in PREVIEW_PDF_DOCX_EXTENSIONS or 
                ext in PREVIEW_IMAGE_EXTENSIONS or 
                ext in PREVIEW_TEXT_EXTENSIONS
            )
            
            # Para PDFs/DOCX/imágenes/texto, usar get_quicklook_pixmap directamente
            # NO usar fallback a iconos si falla
            if is_previewable_type:
                pixmap = self._preview_service.get_quicklook_pixmap(path, self._max_size)
                if pixmap.isNull():
                    logger.warning(f"Failed to generate preview for {ext} file: {path}")
                else:
                    logger.debug(f"Successfully generated preview for {ext} file: {path}, size: {pixmap.width()}x{pixmap.height()}")
            else:
                # Para otros tipos de archivo, intentar get_quicklook_pixmap primero
                pixmap = self._preview_service.get_quicklook_pixmap(path, self._max_size)
                if pixmap.isNull():
                    # Solo como último recurso para archivos desconocidos, usar icono
                    render_service = IconRenderService(self._preview_service.icon_service)
                    pixmap = render_service.get_file_preview(path, self._max_size)
            
            self.update_cache_entry(index, path, pixmap)
            return pixmap
        except Exception as e:
            logger.warning(f"Error generating preview for {path}: {e}", exc_info=True)
            return QPixmap()
    
    def _invalidate_cache_entry(self, index: int) -> None:
        """Invalidate cache entry for given index."""
        if index in self._cache:
            del self._cache[index]
        if index in self._cache_mtime:
            del self._cache_mtime[index]
    
    def update_cache_entry(self, index: int, path: str, pixmap: QPixmap) -> None:
        """Update cache entry with pixmap and mtime."""
        self._cache[index] = pixmap
        try:
            if os.path.exists(path):
                self._cache_mtime[index] = os.path.getmtime(path)
            else:
                self._cache_mtime[index] = 0
        except (OSError, ValueError):
            self._cache_mtime[index] = 0
    
    @property
    def preview_service(self):
        """Get preview service."""
        return self._preview_service
    
    def preload_neighbors(self, current_index: int, paths: list[str]) -> None:
        """Preload previews for adjacent files."""
        for neighbor_index in [current_index - 1, current_index + 1]:
            if (0 <= neighbor_index < len(paths) and 
                neighbor_index not in self._cache):
                self.get_cached_pixmap(neighbor_index, paths)
    
    def cleanup(self, current_index: int, paths: list[str]) -> None:
        """Keep only 10 cache entries around current index."""
        try:
            # Keep entries from index-5 to index+5 (10 entries total)
            keep_indices = set()
            for offset in range(-5, 6):  # -5 to +5 inclusive
                idx = current_index + offset
                if 0 <= idx < len(paths):
                    keep_indices.add(idx)
            
            keys_to_remove = [
                idx for idx in self._cache.keys()
                if idx not in keep_indices or idx < 0 or idx >= len(paths)
            ]
            
            for key in keys_to_remove:
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_mtime:
                    del self._cache_mtime[key]
        except Exception:
            pass
        
        # Safety limit: clear all if somehow exceeded
        if len(self._cache) > 20:
            self._cache.clear()
            self._cache_mtime.clear()

