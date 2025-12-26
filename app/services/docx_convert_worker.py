"""
DocxConvertWorker - QThread worker for DOCX to PDF conversion.

Handles DOCX conversion in background thread to avoid blocking UI.
R5: All external access (docx2pdf) is encapsulated in try/except.
R2: Cooperative cancellation - marks request as invalid, ignores results.
"""

import os
from PySide6.QtCore import QThread, Signal

from app.core.logger import get_logger
from app.services.docx_converter import DocxConverter
from app.services.preview_file_extensions import validate_file_for_preview

logger = get_logger(__name__)


class DocxConvertWorker(QThread):
    """Worker thread for converting DOCX to PDF."""
    
    finished = Signal(str, object)  # (PDF path, request_id)
    error = Signal(str, object)  # (error_msg, request_id)
    
    def __init__(self, docx_path: str, request_id: str = None):
        """
        Initialize DOCX convert worker.
        
        Args:
            docx_path: Path to DOCX file.
            request_id: Unique identifier for this request (R1).
        """
        super().__init__()
        self.docx_path = docx_path
        self.request_id = request_id
        self._converter = DocxConverter()
        self._cancel_requested = False
    
    def cancel(self) -> None:
        """Cooperative cancellation - mark request as invalid."""
        self._cancel_requested = True
    
    def run(self) -> None:
        """Execute DOCX conversion in background thread."""
        if self._cancel_requested:
            return
        
        is_valid, error_msg = validate_file_for_preview(self.docx_path)
        if not is_valid:
            logger.warning(f"Cannot convert {self.docx_path}: {error_msg}")
            self.error.emit(error_msg, self.request_id)
            return
        
        try:
            original_mtime = os.path.getmtime(self.docx_path)
        except (OSError, ValueError) as e:
            logger.warning(f"Cannot get mtime for {self.docx_path}: {e}")
            self.error.emit("Cannot access file", self.request_id)
            return
        
        try:
            if self._cancel_requested:
                return
            
            pdf_path = self._converter.convert_to_pdf(self.docx_path)
            
            if self._cancel_requested:
                return
            
            try:
                current_mtime = os.path.getmtime(self.docx_path)
                if current_mtime != original_mtime:
                    return
            except (OSError, ValueError):
                pass
            
            if not pdf_path or not os.path.exists(pdf_path):
                self.error.emit("Failed to convert DOCX to PDF", self.request_id)
            else:
                self.finished.emit(pdf_path, self.request_id)
        except Exception as e:
            logger.error(f"Exception in DOCX convert worker: {e}", exc_info=True)
            self.error.emit("Conversion error", self.request_id)

