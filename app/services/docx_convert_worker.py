"""
DocxConvertWorker - QThread worker for DOCX to PDF conversion.

Handles DOCX conversion in background thread to avoid blocking UI.
"""

from PySide6.QtCore import QThread, Signal

from app.services.docx_converter import DocxConverter


class DocxConvertWorker(QThread):
    """Worker thread for converting DOCX to PDF."""
    
    finished = Signal(str)  # PDF path
    error = Signal(str)
    
    def __init__(self, docx_path: str):
        """
        Initialize DOCX convert worker.
        
        Args:
            docx_path: Path to DOCX file.
        """
        super().__init__()
        self.docx_path = docx_path
        self._converter = DocxConverter()
    
    def run(self) -> None:
        """Execute DOCX conversion in background thread."""
        try:
            pdf_path = self._converter.convert_to_pdf(self.docx_path)
            if not pdf_path:
                self.error.emit("Failed to convert DOCX to PDF")
            else:
                self.finished.emit(pdf_path)
        except Exception as e:
            self.error.emit(str(e))

