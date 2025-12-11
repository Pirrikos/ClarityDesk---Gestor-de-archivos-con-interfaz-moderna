"""
IconBatchWorker - QThread worker for batch icon generation.

Handles generating multiple icons in background thread to avoid blocking UI.
"""

from typing import List, Tuple

from PySide6.QtCore import QSize, QThread, Signal
from PySide6.QtGui import QPixmap

from app.services.preview_service import get_file_preview


class IconBatchWorker(QThread):
    """Worker thread for generating multiple icons."""
    
    progress = Signal(int)  # Progress percentage (0-100)
    finished = Signal(list)  # List of (path, QPixmap) tuples
    error = Signal(str)
    
    def __init__(self, file_paths: List[str], size: QSize, icon_provider):
        """
        Initialize icon batch worker.
        
        Args:
            file_paths: List of file paths to generate icons for.
            size: Size for generated icons.
            icon_provider: QFileIconProvider instance.
        """
        super().__init__()
        self.file_paths = file_paths
        self.size = size
        self.icon_provider = icon_provider
    
    def run(self) -> None:
        """Execute batch icon generation in background thread."""
        try:
            results: List[Tuple[str, QPixmap]] = []
            total = len(self.file_paths)
            
            for idx, file_path in enumerate(self.file_paths):
                try:
                    pixmap = get_file_preview(file_path, self.size, self.icon_provider)
                    results.append((file_path, pixmap))
                    
                    # Emit progress
                    progress_pct = int((idx + 1) * 100 / total) if total > 0 else 100
                    self.progress.emit(progress_pct)
                except Exception as e:
                    # Continue with other files even if one fails
                    results.append((file_path, QPixmap()))
            
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

