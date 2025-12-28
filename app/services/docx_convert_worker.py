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
        logger.debug(f"DocxConvertWorker.run: STARTED, request_id={self.request_id}, docx_path={self.docx_path}, cancel_requested={self._cancel_requested}")
        if self._cancel_requested:
            logger.debug(f"DocxConvertWorker.run: CANCELLED before start, request_id={self.request_id}")
            return
        
        is_valid, error_msg = validate_file_for_preview(self.docx_path)
        logger.debug(f"DocxConvertWorker.run: File validation, is_valid={is_valid}, error_msg={error_msg}")
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
                logger.debug(f"DocxConvertWorker.run: CANCELLED before conversion, request_id={self.request_id}")
                return
            
            logger.debug(f"DocxConvertWorker.run: Calling converter.convert_to_pdf, request_id={self.request_id}")
            pdf_path = self._converter.convert_to_pdf(self.docx_path)
            logger.debug(f"DocxConvertWorker.run: Conversion completed, pdf_path={pdf_path}, exists={os.path.exists(pdf_path) if pdf_path else False}, request_id={self.request_id}")
            
            if self._cancel_requested:
                logger.debug(f"DocxConvertWorker.run: CANCELLED after conversion, request_id={self.request_id}")
                return
            
            try:
                current_mtime = os.path.getmtime(self.docx_path)
                if current_mtime != original_mtime:
                    logger.debug(f"DocxConvertWorker.run: File modified during conversion, ignoring result, request_id={self.request_id}")
                    return
            except (OSError, ValueError):
                pass
            
            if not pdf_path or not os.path.exists(pdf_path):
                logger.warning(f"DocxConvertWorker.run: Invalid PDF path, emitting error, request_id={self.request_id}")
                self.error.emit("Failed to convert DOCX to PDF", self.request_id)
            else:
                logger.debug(f"DocxConvertWorker.run: Emitting finished signal, pdf_path={pdf_path}, request_id={self.request_id}")
                self.finished.emit(pdf_path, self.request_id)
        except Exception as e:
            logger.error(f"Exception in DOCX convert worker: {e}", exc_info=True)
            self.error.emit("Conversion error", self.request_id)

