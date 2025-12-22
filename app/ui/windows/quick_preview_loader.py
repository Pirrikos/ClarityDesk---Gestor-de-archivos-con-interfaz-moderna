"""
Quick Preview Loader - Preview loading and display logic.

Handles loading previews from cache or PDF handler and displaying them.
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

from app.ui.windows.quick_preview_cache import QuickPreviewCache
from app.ui.windows.quick_preview_pdf_handler import QuickPreviewPdfHandler
from app.ui.windows.quick_preview_styles import get_error_label_style

if TYPE_CHECKING:
    from app.ui.windows.quick_preview_animations import QuickPreviewAnimations


class QuickPreviewLoader:
    """Handles preview loading and display."""
    
    def __init__(self, cache: QuickPreviewCache, pdf_handler: QuickPreviewPdfHandler):
        """Initialize loader."""
        self._cache = cache
        self._pdf_handler = pdf_handler
    
    def load_preview(
        self, 
        paths: list[str], 
        index: int, 
        image_label: QLabel,
        use_crossfade: bool, 
        animations: 'QuickPreviewAnimations'
    ) -> tuple[QPixmap, str]:
        """Load preview for current file."""
        if not paths or index < 0 or index >= len(paths):
            return QPixmap(), ""
        
        current_path = paths[index]
        
        # Para PDFs/DOCX, usar el pdf_handler para renderizar la página específica
        if QuickPreviewPdfHandler.is_pdf_or_docx_file(current_path):
            max_size = self._cache.get_max_size()
            if max_size:
                # Usar el pdf_handler para renderizar la página actual (no siempre la primera)
                pixmap = self._pdf_handler.render_page(max_size)
                if not pixmap.isNull():
                    header_text = self._pdf_handler.get_header_text(current_path)
                    # Actualizar el cache con el pixmap renderizado usando método público
                    self._cache.update_cache_entry(index, current_path, pixmap)
                    return pixmap, header_text
        
        # Para otros archivos, usar el cache normalmente
        pixmap = self._cache.get_cached_pixmap(index, paths)
        header_text = Path(current_path).name
        
        if pixmap.isNull():
            image_label.setText("No preview available")
            image_label.setStyleSheet(get_error_label_style())
            return QPixmap(), header_text
        
        return pixmap, header_text
    
    def preload_and_cleanup(self, index: int, paths: list[str]) -> None:
        """Preload neighbors and cleanup cache."""
        self._cache.preload_neighbors(index, paths)
        self._cache.cleanup(index, paths)

