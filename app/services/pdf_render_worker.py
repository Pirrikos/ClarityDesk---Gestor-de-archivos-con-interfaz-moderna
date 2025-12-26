"""
PdfRenderWorker - QThread worker for PDF page rendering.

Handles PDF rendering in background thread to avoid blocking UI.
R5: All external access (PyMuPDF) is encapsulated in try/except.
R2: Cooperative cancellation - marks request as invalid, ignores results.
"""

import os
from PySide6.QtCore import QSize, QThread, Signal
from PySide6.QtGui import QPixmap

from app.core.logger import get_logger
from app.services.pdf_renderer import PdfRenderer
from app.services.preview_file_extensions import validate_file_for_preview, validate_pixmap

logger = get_logger(__name__)


class PdfRenderWorker(QThread):
    """Worker thread for rendering PDF pages."""
    
    finished = Signal(object, object)  # (QPixmap, request_id)
    error = Signal(str, object)  # (error_msg, request_id)
    
    def __init__(self, pdf_path: str, max_size: QSize, page_num: int = 0, request_id: str = None):
        """
        Initialize PDF render worker.
        
        Args:
            pdf_path: Path to PDF file.
            max_size: Maximum size for rendered pixmap.
            page_num: Page number to render (0-indexed).
            request_id: Unique identifier for this request (R1).
        """
        super().__init__()
        self.pdf_path = pdf_path
        self.max_size = max_size
        self.page_num = page_num
        self.request_id = request_id
        self._cancel_requested = False
    
    def cancel(self) -> None:
        """Cooperative cancellation - mark request as invalid."""
        self._cancel_requested = True
    
    def run(self) -> None:
        """Execute PDF rendering in background thread."""
        if self._cancel_requested:
            return
        
        is_valid, error_msg = validate_file_for_preview(self.pdf_path)
        if not is_valid:
            logger.warning(f"Cannot render {self.pdf_path}: {error_msg}")
            self.error.emit(error_msg, self.request_id)
            return
        
        try:
            original_mtime = os.path.getmtime(self.pdf_path)
        except (OSError, ValueError) as e:
            logger.warning(f"Cannot get mtime for {self.pdf_path}: {e}")
            self.error.emit("Cannot access file", self.request_id)
            return
        
        try:
            if self._cancel_requested:
                return
            
            result = PdfRenderer.render_page(self.pdf_path, self.max_size, self.page_num)
            
            if self._cancel_requested:
                return
            
            try:
                current_mtime = os.path.getmtime(self.pdf_path)
                if current_mtime != original_mtime:
                    return
            except (OSError, ValueError):
                pass
            
            if not validate_pixmap(result):
                self.error.emit("Failed to render PDF page", self.request_id)
            else:
                self.finished.emit(result, self.request_id)
        except Exception as e:
            logger.error(f"Exception in PDF render worker: {e}", exc_info=True)
            self.error.emit("Render error", self.request_id)

