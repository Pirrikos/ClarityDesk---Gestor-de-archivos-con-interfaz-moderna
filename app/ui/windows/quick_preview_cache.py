"""
Quick Preview Cache - Preview caching for instant navigation.

Manages in-memory cache of preview pixmaps for adjacent files.
Includes mtime validation to detect file changes.
"""

import os
from typing import Optional
from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap


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
                        del self._cache[index]
                        if index in self._cache_mtime:
                            del self._cache_mtime[index]
                else:
                    # File doesn't exist, invalidate cache
                    if index in self._cache:
                        del self._cache[index]
                    if index in self._cache_mtime:
                        del self._cache_mtime[index]
            except (OSError, ValueError):
                # Can't read mtime, invalidate cache
                if index in self._cache:
                    del self._cache[index]
                if index in self._cache_mtime:
                    del self._cache_mtime[index]
        
        pixmap = self._preview_service.get_quicklook_pixmap(path, self._max_size)
        self._cache[index] = pixmap
        try:
            if os.path.exists(path):
                self._cache_mtime[index] = os.path.getmtime(path)
            else:
                self._cache_mtime[index] = 0
        except (OSError, ValueError):
            self._cache_mtime[index] = 0
        
        return pixmap
    
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

