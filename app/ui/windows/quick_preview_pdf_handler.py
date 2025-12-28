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
        from app.core.logger import get_logger
        logger = get_logger(__name__)
        logger.debug(f"load_pdf_info_async: STARTED, path={path}, _original_path={self._original_path}")
        is_new_file = self._original_path != path
        logger.debug(f"load_pdf_info_async: is_new_file={is_new_file}")
        
        if is_new_file:
            self._current_page = 0
            self._original_path = path
            
            if self.is_docx_file(path):
                logger.debug(f"load_pdf_info_async: File is DOCX, checking for async conversion")
                # Use async conversion
                if hasattr(self._preview_service, 'convert_docx_to_pdf_async'):
                    logger.debug(f"load_pdf_info_async: Using async DOCX conversion")
                    def handle_conversion(pdf_path: str) -> None:
                        logger.debug(f"load_pdf_info_async.handle_conversion: STARTED, pdf_path={pdf_path}, exists={os.path.exists(pdf_path) if pdf_path else False}")
                        # R6: Validate result before using
                        if pdf_path and os.path.exists(pdf_path):
                            logger.debug(f"load_pdf_info_async.handle_conversion: PDF path valid, setting up")
                            self._pdf_path = pdf_path
                            self._is_pdf = True
                            if self._pdf_path:
                                try:
                                    logger.debug(f"load_pdf_info_async.handle_conversion: Getting page count")
                                    self._total_pages = self._preview_service.get_pdf_page_count(self._pdf_path)
                                    logger.debug(f"load_pdf_info_async.handle_conversion: total_pages={self._total_pages}")
                                    if self._current_page >= self._total_pages:
                                        self._current_page = 0
                                except Exception as e:
                                    logger.error(f"load_pdf_info_async.handle_conversion: Error getting page count: {e}", exc_info=True)
                                    # R5: Encapsulate error
                                    self._total_pages = 0
                                    self._current_page = 0
                            logger.debug(f"load_pdf_info_async.handle_conversion: Calling on_finished(True)")
                            on_finished(True)
                        else:
                            logger.warning(f"load_pdf_info_async.handle_conversion: PDF path invalid or does not exist")
                            # R4: Fallback - mark as non-PDF
                            self._is_pdf = False
                            self._pdf_path = None
                            logger.debug(f"load_pdf_info_async.handle_conversion: Calling on_finished(False)")
                            on_finished(False)
                    
                    # R1: Request ID returned but not used here (conversion is internal)
                    logger.debug(f"load_pdf_info_async: Calling convert_docx_to_pdf_async")
                    self._preview_service.convert_docx_to_pdf_async(
                        path, handle_conversion, on_error
                    )
                    logger.debug(f"load_pdf_info_async: convert_docx_to_pdf_async called, returning")
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
                logger.debug(f"load_pdf_info_async: File is PDF, setting path")
                self._pdf_path = path
                self._is_pdf = True
        
        if self._pdf_path:
            logger.debug(f"load_pdf_info_async: Getting page count for PDF")
            self._total_pages = self._preview_service.get_pdf_page_count(self._pdf_path)
            logger.debug(f"load_pdf_info_async: total_pages={self._total_pages}")
            
            if self._current_page >= self._total_pages:
                self._current_page = 0
        
        logger.debug(f"load_pdf_info_async: Calling on_finished(is_new_file={is_new_file})")
        on_finished(is_new_file)
        logger.debug(f"load_pdf_info_async: COMPLETED")
    
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
        from app.core.logger import get_logger
        logger = get_logger(__name__)
        logger.debug(f"render_page_async: STARTED, _is_pdf={self._is_pdf}, _pdf_path={self._pdf_path}, _current_page={self._current_page}, _total_pages={self._total_pages}, max_size={max_size.width()}x{max_size.height()}")
        
        if not self._is_pdf or not self._pdf_path:
            logger.warning(f"render_page_async: Validation failed - _is_pdf={self._is_pdf}, _pdf_path={self._pdf_path}")
            # R4: Fallback visual
            on_finished(QPixmap())
            return None
        
        if not (0 <= self._current_page < self._total_pages):
            logger.warning(f"render_page_async: Page out of range - _current_page={self._current_page}, _total_pages={self._total_pages}")
            # R4: Fallback visual
            on_finished(QPixmap())
            return None
        
        # Use async rendering from preview service
        logger.debug(f"render_page_async: Checking if preview_service has render_pdf_page_async method")
        if hasattr(self._preview_service, 'render_pdf_page_async'):
            # R1: Get request_id from async call
            logger.debug(f"render_page_async: Calling preview_service.render_pdf_page_async, pdf_path={self._pdf_path}, page={self._current_page}, max_size={max_size.width()}x{max_size.height()}")
            try:
                request_id = self._preview_service.render_pdf_page_async(
                    self._pdf_path,
                    max_size,
                    self._current_page,
                    on_finished,
                    on_error
                )
                logger.debug(f"render_page_async: preview_service returned request_id={request_id}")
                return request_id
            except Exception as e:
                logger.error(f"render_page_async: Exception calling preview_service.render_pdf_page_async: {e}", exc_info=True)
                if on_error:
                    on_error(f"Error starting render: {e}")
                return None
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
