"""
Quick Preview PDF Handler - PDF-specific preview logic.

Handles PDF file detection, page management, and PDF preview loading.
R1: Tracks request_id for validation.
R4: Ensures fallback visual always available.
"""

import os
from pathlib import Path
from typing import Optional, Callable

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap

from app.services.docx_converter import DocxConverter
from app.services.preview_pdf_service import PreviewPdfService
from app.services.preview_file_extensions import normalize_extension


class QuickPreviewPdfHandler:
    """Handles PDF-specific preview logic."""
    
    def __init__(self, preview_service: PreviewPdfService):
        """Initialize PDF handler."""
        self._preview_service = preview_service
        self._docx_converter = DocxConverter()
        self._current_page: int = 0
        self._total_pages: int = 0
        self._is_pdf: bool = False
        self._pdf_path: Optional[str] = None
        self._original_path: Optional[str] = None
    
    @staticmethod
    def is_pdf_file(path: str) -> bool:
        """Check if file is a PDF."""
        # R11: Normalize extension in single entry point
        return normalize_extension(path) == ".pdf"
    
    @staticmethod
    def is_docx_file(path: str) -> bool:
        """Check if file is a DOCX."""
        # R11: Normalize extension in single entry point
        return normalize_extension(path) == ".docx"
    
    @staticmethod
    def is_pdf_or_docx_file(path: str) -> bool:
        """Check if file is PDF or DOCX."""
        # R11: Normalize extension in single entry point
        ext = normalize_extension(path)
        return ext == ".pdf" or ext == ".docx"
    
    def load_pdf_info(self, path: str) -> bool:
        """Load PDF information for PDF or DOCX file (synchronous)."""
        is_new_file = self._original_path != path
        
        if is_new_file:
            self._current_page = 0
            self._original_path = path
            
            if self.is_docx_file(path):
                pdf_path = self._docx_converter.convert_to_pdf(path)
                if pdf_path:
                    self._pdf_path = pdf_path
                    self._is_pdf = True
                else:
                    self._is_pdf = False
                    self._pdf_path = None
                    return False
            else:
                self._pdf_path = path
                self._is_pdf = True
        
        if self._pdf_path:
            self._total_pages = self._preview_service.get_pdf_page_count(self._pdf_path)
            
            if self._current_page >= self._total_pages:
                self._current_page = 0
        
        return is_new_file
    
    def load_pdf_info_async(
        self,
        path: str,
        on_finished: Callable[[bool], None],
        on_error: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Load PDF information asynchronously (for DOCX conversion).
        
        Args:
            path: Path to PDF or DOCX file.
            on_finished: Callback called with bool (is_new_file) when loading completes.
            on_error: Optional callback called with error message on failure.
        """
        is_new_file = self._original_path != path
        
        if is_new_file:
            self._current_page = 0
            self._original_path = path
            
            if self.is_docx_file(path):
                # Use async conversion
                if hasattr(self._preview_service, 'convert_docx_to_pdf_async'):
                    def handle_conversion(pdf_path: str) -> None:
                        # R6: Validate result before using
                        if pdf_path and os.path.exists(pdf_path):
                            self._pdf_path = pdf_path
                            self._is_pdf = True
                            if self._pdf_path:
                                try:
                                    self._total_pages = self._preview_service.get_pdf_page_count(self._pdf_path)
                                    if self._current_page >= self._total_pages:
                                        self._current_page = 0
                                except Exception:
                                    # R5: Encapsulate error
                                    self._total_pages = 0
                                    self._current_page = 0
                            on_finished(True)
                        else:
                            # R4: Fallback - mark as non-PDF
                            self._is_pdf = False
                            self._pdf_path = None
                            on_finished(False)
                    
                    # R1: Request ID returned but not used here (conversion is internal)
                    self._preview_service.convert_docx_to_pdf_async(
                        path, handle_conversion, on_error
                    )
                    return
                else:
                    # Fallback to synchronous conversion
                    pdf_path = self._docx_converter.convert_to_pdf(path)
                    if pdf_path:
                        self._pdf_path = pdf_path
                        self._is_pdf = True
                    else:
                        self._is_pdf = False
                        self._pdf_path = None
                        on_finished(False)
                        return
            else:
                self._pdf_path = path
                self._is_pdf = True
        
        if self._pdf_path:
            self._total_pages = self._preview_service.get_pdf_page_count(self._pdf_path)
            
            if self._current_page >= self._total_pages:
                self._current_page = 0
        
        on_finished(is_new_file)
    
    def render_page(self, max_size: QSize) -> QPixmap:
        """Render current PDF page (synchronous)."""
        if not self._is_pdf or not self._pdf_path:
            return QPixmap()
        
        if not (0 <= self._current_page < self._total_pages):
            return QPixmap()
        
        return self._preview_service.render_pdf_page(
            self._pdf_path, max_size, self._current_page
        )
    
    def render_page_async(
        self,
        max_size: QSize,
        on_finished: Callable[[QPixmap], None],
        on_error: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        Render current PDF page asynchronously.
        
        R1: Returns request_id for validation.
        R4: Always provides fallback visual.
        
        Args:
            max_size: Maximum size for rendered pixmap.
            on_finished: Callback called with QPixmap when rendering completes.
            on_error: Optional callback called with error message on failure.
        
        Returns:
            request_id: Unique identifier for this request, or None if validation failed.
        """
        if not self._is_pdf or not self._pdf_path:
            # R4: Fallback visual
            on_finished(QPixmap())
            return None
        
        if not (0 <= self._current_page < self._total_pages):
            # R4: Fallback visual
            on_finished(QPixmap())
            return None
        
        # Use async rendering from preview service
        if hasattr(self._preview_service, 'render_pdf_page_async'):
            # R1: Get request_id from async call
            request_id = self._preview_service.render_pdf_page_async(
                self._pdf_path,
                max_size,
                self._current_page,
                on_finished,
                on_error
            )
            return request_id
        else:
            # Fallback to synchronous rendering
            pixmap = self.render_page(max_size)
            # R4: Fallback if null
            if pixmap.isNull():
                pixmap = QPixmap()
            on_finished(pixmap)
            return None
    
    def get_header_text(self, file_path: str) -> str:
        """Get header text for PDF or DOCX file."""
        if self._total_pages > 0:
            return f"{self._current_page + 1}/{self._total_pages}: {Path(file_path).name}"
        return Path(file_path).name
    
    def reset_for_new_file(self) -> None:
        """Reset PDF state for non-PDF/DOCX files."""
        self._is_pdf = False
        self._pdf_path = None
        self._original_path = None
        self._current_page = 0
        self._total_pages = 0
    
    @property
    def is_pdf(self) -> bool:
        """Whether current file is PDF."""
        return self._is_pdf
    
    @property
    def current_page(self) -> int:
        """Current PDF page (0-indexed)."""
        return self._current_page
    
    @current_page.setter
    def current_page(self, value: int) -> None:
        """Set current PDF page."""
        self._current_page = value
    
    @property
    def total_pages(self) -> int:
        """Total number of PDF pages."""
        return self._total_pages
    
    @property
    def pdf_path(self) -> Optional[str]:
        """Path to PDF file (original or converted from DOCX)."""
        return self._pdf_path
