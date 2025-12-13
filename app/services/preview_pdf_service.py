"""
PreviewPdfService - PDF and DOCX preview rendering.

Handles PDF page rendering and DOCX to PDF conversion for quick preview.
Supports both synchronous and asynchronous (QThread) rendering.
"""

import os
from pathlib import Path
from typing import Optional, Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap

from app.services.docx_converter import DocxConverter
from app.services.pdf_renderer import PdfRenderer
from app.services.pdf_render_worker import PdfRenderWorker
from app.services.docx_convert_worker import DocxConvertWorker


class PreviewPdfService:
    """Service for generating PDF and DOCX preview images."""
    
    def __init__(self, icon_service) -> None:
        """Initialize PreviewPdfService with icon service."""
        self._icon_service = icon_service
        self._pdf_renderer = PdfRenderer()
        self._docx_converter = DocxConverter()
        self._active_pdf_worker: Optional[PdfRenderWorker] = None
        self._active_docx_worker: Optional[DocxConvertWorker] = None

    @staticmethod
    def _is_pdf(path: str) -> bool:
        """Check if file is a PDF."""
        return Path(path).suffix.lower() == ".pdf"

    @staticmethod
    def _is_docx(path: str) -> bool:
        """Check if file is a DOCX."""
        return Path(path).suffix.lower() == ".docx"

    def get_pdf_page_count(self, pdf_path: str) -> int:
        """Get total number of pages in PDF."""
        return self._pdf_renderer.get_page_count(pdf_path)

    def _render_pdf_page(self, pdf_path: str, max_size: QSize, page_num: int = 0) -> QPixmap:
        """Render specific page of PDF as pixmap using PyMuPDF (synchronous)."""
        return self._pdf_renderer.render_page(pdf_path, max_size, page_num)
    
    def render_pdf_page_async(
        self,
        pdf_path: str,
        max_size: QSize,
        page_num: int,
        on_finished: Callable[[QPixmap], None],
        on_error: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Render PDF page asynchronously using QThread worker.
        
        Args:
            pdf_path: Path to PDF file.
            max_size: Maximum size for rendered pixmap.
            page_num: Page number to render (0-indexed).
            on_finished: Callback called with QPixmap when rendering completes.
            on_error: Optional callback called with error message on failure.
        """
        if self._active_pdf_worker:
            try:
                self._active_pdf_worker.cancel()
            except Exception:
                pass
            self._active_pdf_worker.quit()
            self._active_pdf_worker.wait()
        
        worker = PdfRenderWorker(pdf_path, max_size, page_num)
        self._active_pdf_worker = worker
        
        def handle_finished(pixmap: QPixmap) -> None:
            self._active_pdf_worker = None
            on_finished(pixmap)
        
        def handle_error(error_msg: str) -> None:
            self._active_pdf_worker = None
            if on_error:
                on_error(error_msg)
            else:
                on_finished(QPixmap())  # Return empty pixmap on error
        
        worker.finished.connect(handle_finished)
        worker.error.connect(handle_error)
        worker.start()

    def get_pdf_thumbnail(self, pdf_path: str, page_num: int, thumbnail_size: QSize) -> QPixmap:
        """Get thumbnail of a specific PDF page."""
        return self._pdf_renderer.render_thumbnail(pdf_path, page_num, thumbnail_size)
    
    def _convert_docx_to_pdf(self, docx_path: str) -> str:
        """Convert DOCX to PDF using docx2pdf (synchronous)."""
        return self._docx_converter.convert_to_pdf(docx_path)
    
    def convert_docx_to_pdf_async(
        self,
        docx_path: str,
        on_finished: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Convert DOCX to PDF asynchronously using QThread worker.
        
        Args:
            docx_path: Path to DOCX file.
            on_finished: Callback called with PDF path when conversion completes.
            on_error: Optional callback called with error message on failure.
        """
        if self._active_docx_worker:
            try:
                self._active_docx_worker.cancel()
            except Exception:
                pass
            self._active_docx_worker.quit()
            self._active_docx_worker.wait()
        
        worker = DocxConvertWorker(docx_path)
        self._active_docx_worker = worker
        
        def handle_finished(pdf_path: str) -> None:
            self._active_docx_worker = None
            on_finished(pdf_path)
        
        def handle_error(error_msg: str) -> None:
            self._active_docx_worker = None
            if on_error:
                on_error(error_msg)
            else:
                on_finished("")  # Return empty string on error
        
        worker.finished.connect(handle_finished)
        worker.error.connect(handle_error)
        worker.start()

    def get_quicklook_pixmap(self, path: str, max_size: QSize) -> QPixmap:
        """Get pixmap for quick preview with real rendering for PDFs and DOCX."""
        if not path or not os.path.exists(path):
            return QPixmap()

        ext = Path(path).suffix.lower()
        
        if ext == ".pdf":
            pdf_pixmap = self._render_pdf_page(path, max_size)
            if not pdf_pixmap.isNull():
                return pdf_pixmap

        elif ext == ".docx":
            pdf_path = self._convert_docx_to_pdf(path)
            if pdf_path:
                pdf_pixmap = self._render_pdf_page(pdf_path, max_size)
                if not pdf_pixmap.isNull():
                    return pdf_pixmap

        # Otros tipos → usar lógica existente (IconService)
        base = self._icon_service.get_file_preview(path, max_size)
        if base.isNull():
            return QPixmap()

        return base.scaled(
            max_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    def clear_cache(self) -> None:
        """Clear temporary PDF cache directory."""
        self._docx_converter.clear_cache()
    
    def stop_workers(self) -> None:
        if self._active_pdf_worker:
            try:
                self._active_pdf_worker.cancel()
            except Exception:
                pass
            self._active_pdf_worker.quit()
            self._active_pdf_worker.wait()
            self._active_pdf_worker = None
        if self._active_docx_worker:
            try:
                self._active_docx_worker.cancel()
            except Exception:
                pass
            self._active_docx_worker.quit()
            self._active_docx_worker.wait()
            self._active_docx_worker = None

