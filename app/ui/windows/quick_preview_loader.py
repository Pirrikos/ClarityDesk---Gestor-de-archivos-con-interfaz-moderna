"""
Quick Preview Loader - Preview loading and display logic.

Handles loading previews from cache or PDF handler and displaying them.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

from app.ui.windows.quick_preview_cache import QuickPreviewCache
from app.ui.windows.quick_preview_pdf_handler import QuickPreviewPdfHandler


class QuickPreviewLoader:
    """Handles preview loading and display."""
    
    def __init__(self, cache: QuickPreviewCache, pdf_handler: QuickPreviewPdfHandler):
        """Initialize loader."""
        self._cache = cache
        self._pdf_handler = pdf_handler
    
    def load_preview(self, paths: list[str], index: int, image_label: QLabel,
                    use_crossfade: bool, animations) -> tuple[Optional[QPixmap], str]:
        """Load preview for current file."""
        if not paths or index < 0 or index >= len(paths):
            return None, ""
        
        current_path = paths[index]
        
        from app.ui.windows.quick_preview_pdf_handler import QuickPreviewPdfHandler
        
        if QuickPreviewPdfHandler.is_pdf_or_docx_file(current_path):
            max_size = self._cache.get_max_size()
            if max_size:
                pixmap = self._pdf_handler.render_page(max_size)
            else:
                pixmap = QPixmap()
            
            if not pixmap.isNull():
                header_text = self._pdf_handler.get_header_text(current_path)
                return pixmap, header_text
        
        pixmap = self._cache.get_cached_pixmap(index, paths)
        header_text = Path(current_path).name
        
        if pixmap.isNull():
            image_label.setText("No preview available")
            image_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 100);
                    font-family: 'Segoe UI', sans-serif;
                    /* font-size: establecido explícitamente */
                    background-color: transparent;
                }
            """)
            return None, header_text
        
        return pixmap, header_text
    
    def preload_and_cleanup(self, index: int, paths: list[str]) -> None:
        """Preload neighbors and cleanup cache."""
        self._cache.preload_neighbors(index, paths)
        self._cache.cleanup(index, paths)

