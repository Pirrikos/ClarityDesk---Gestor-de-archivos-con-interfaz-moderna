"""
PdfRenderWorker - QThread worker for PDF page rendering.

Handles PDF rendering in background thread to avoid blocking UI.
"""

from PySide6.QtCore import QSize, QThread, Signal
from PySide6.QtGui import QPixmap

from app.services.pdf_renderer import PdfRenderer


class PdfRenderWorker(QThread):
    """Worker thread for rendering PDF pages."""
    
    finished = Signal(object)  # QPixmap
    error = Signal(str)
    
    def __init__(self, pdf_path: str, max_size: QSize, page_num: int = 0):
        """
        Initialize PDF render worker.
        
        Args:
            pdf_path: Path to PDF file.
            max_size: Maximum size for rendered pixmap.
            page_num: Page number to render (0-indexed).
        """
        super().__init__()
        self.pdf_path = pdf_path
        self.max_size = max_size
        self.page_num = page_num
        self._cancel_requested = False
    
    def cancel(self) -> None:
        self._cancel_requested = True
    
    def run(self) -> None:
        """Execute PDF rendering in background thread."""
        try:
            if self._cancel_requested:
                self.error.emit("Cancelled")
                return
            result = PdfRenderer.render_page(self.pdf_path, self.max_size, self.page_num)
            if result.isNull():
                self.error.emit("Failed to render PDF page")
            else:
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

