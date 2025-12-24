"""
GridIconLoader - Asynchronous icon loading for grid tiles.

Uses QThreadPool to load icons in background threads, preventing UI blocking.
"""

from typing import Dict, Optional
from PySide6.QtCore import QObject, QThreadPool, Signal, QRunnable, QSize, Qt
from PySide6.QtGui import QImage

from app.core.logger import get_logger

logger = get_logger(__name__)


class IconLoadWorker(QRunnable):
    """
    Worker that loads icon in background thread.
    
    Never creates QPixmap - only works with QImage/bytes.
    """
    
    def __init__(
        self,
        tile_id: str,
        file_path: str,
        size: QSize,
        request_id: int,
        icon_provider,
        callback
    ):
        """
        Initialize worker.
        
        Args:
            tile_id: Unique identifier for the tile
            file_path: Path to file/folder
            size: Target icon size
            request_id: Request ID to match with result
            icon_provider: QFileIconProvider instance
            callback: Function to call with result (tile_id, image, request_id)
        """
        super().__init__()
        self._tile_id = tile_id
        self._file_path = file_path
        self._size = size
        self._request_id = request_id
        self._icon_provider = icon_provider
        self._callback = callback
    
    def run(self) -> None:
        """Load icon in background thread."""
        try:
            from app.services.preview_service import get_file_preview
            
            # Load preview - returns QPixmap, convert to QImage for thread safety
            pixmap = get_file_preview(self._file_path, self._size, self._icon_provider)
            
            if pixmap and not pixmap.isNull():
                # Convert QPixmap to QImage (thread-safe, can be done in worker thread)
                # QImage is thread-safe, QPixmap is not
                image = pixmap.toImage()
                
                # Ensure image has correct size
                if image.width() != self._size.width() or image.height() != self._size.height():
                    image = image.scaled(
                        self._size.width(), 
                        self._size.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
            else:
                # Create empty transparent image as fallback
                image = QImage(self._size, QImage.Format.Format_ARGB32)
                image.fill(0)  # Transparent
            
            # Call callback with result (pass file_path and size for caching)
            self._callback(self._tile_id, self._file_path, self._size, image, self._request_id)
            
        except Exception as e:
            logger.error(f"Error loading icon for {self._file_path}: {e}")
            # Return empty transparent image on error
            image = QImage(self._size, QImage.Format.Format_ARGB32)
            image.fill(0)
            self._callback(self._tile_id, self._file_path, self._size, image, self._request_id)


class GridIconLoader(QObject):
    """
    Asynchronous icon loader using QThreadPool.
    
    Loads icons in background threads and emits signals with results.
    """
    
    icon_loaded = Signal(str, QImage, int)  # tile_id, image, request_id
    
    def __init__(self, max_threads: int = 5):
        """
        Initialize icon loader.
        
        Args:
            max_threads: Maximum number of concurrent worker threads
        """
        super().__init__()
        self._thread_pool = QThreadPool()
        self._thread_pool.setMaxThreadCount(max_threads)
        self._request_counter = 0
        self._cache: Dict[tuple, QImage] = {}  # (file_path, width, height) -> QImage
        self._icon_provider = None  # Lazy initialization
    
    def _get_icon_provider(self):
        """Get or create QFileIconProvider instance."""
        if self._icon_provider is None:
            from PySide6.QtWidgets import QFileIconProvider
            self._icon_provider = QFileIconProvider()
        return self._icon_provider
    
    def request_icon(
        self,
        tile_id: str,
        file_path: str,
        size: QSize
    ) -> int:
        """
        Request icon loading for a tile.
        
        Args:
            tile_id: Unique identifier for the tile
            file_path: Path to file/folder
            size: Target icon size
            
        Returns:
            Request ID for matching with result
        """
        # Check cache first
        cache_key = (file_path, size.width(), size.height())
        if cache_key in self._cache:
            cached_image = self._cache[cache_key]
            request_id = self._request_counter
            self._request_counter += 1
            # Emit cached result immediately (in next event loop iteration)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.icon_loaded.emit(tile_id, cached_image, request_id))
            return request_id
        
        # Generate request ID
        request_id = self._request_counter
        self._request_counter += 1
        
        # Create and start worker
        worker = IconLoadWorker(
            tile_id,
            file_path,
            size,
            request_id,
            self._get_icon_provider(),
            self._on_icon_loaded
        )
        
        self._thread_pool.start(worker)
        
        return request_id
    
    def _on_icon_loaded(self, tile_id: str, file_path: str, size: QSize, image: QImage, request_id: int) -> None:
        """
        Handle icon loaded callback from worker.
        
        Caches result and emits signal.
        """
        # Cache the result
        cache_key = (file_path, size.width(), size.height())
        self._cache[cache_key] = image
        
        # Emit signal (will be handled in UI thread)
        self.icon_loaded.emit(tile_id, image, request_id)

