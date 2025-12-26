"""
PDF Renderer - PDF page rendering using PyMuPDF.

Handles rendering of PDF pages to QPixmap for previews and thumbnails.
"""

import os
import sys
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap

from app.core.logger import get_logger
from app.services.preview_file_extensions import validate_file_for_preview, validate_pixmap

logger = get_logger(__name__)

# Try to import PyMuPDF at module level
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError as e:
    FITZ_AVAILABLE = False
    fitz = None
    logger.error(f"Failed to import PyMuPDF (fitz): {e}")
    logger.error(f"Python executable: {sys.executable}")
    # Try alternative import
    try:
        import pymupdf as fitz
        FITZ_AVAILABLE = True
    except ImportError as e2:
        logger.error(f"Failed to import PyMuPDF as pymupdf: {e2}")


class PdfRenderer:
    """Renders PDF pages to QPixmap using PyMuPDF."""
    
    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """Get total number of pages in PDF."""
        if not FITZ_AVAILABLE:
            return 0
        
        doc = None
        try:
            doc = fitz.open(pdf_path)
            return len(doc)
        except Exception:
            return 0
        finally:
            if doc:
                try:
                    doc.close()
                except Exception:
                    pass
    
    @staticmethod
    def _render_page_to_pixmap(doc, page_num: int, zoom: float) -> QPixmap:
        """Render PDF page to QPixmap with given zoom, respecting orientation."""
        if not FITZ_AVAILABLE:
            return QPixmap()
        
        if page_num < 0 or page_num >= len(doc):
            return QPixmap()
        
        try:
            page = doc[page_num]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            qpixmap = QPixmap()
            if not qpixmap.loadFromData(img_data, "PPM"):
                logger.warning("Failed to load pixmap from PPM data")
                return QPixmap()
            return qpixmap
        except Exception as e:
            logger.error(f"Exception in _render_page_to_pixmap: {e}", exc_info=True)
            return QPixmap()
    
    @staticmethod
    def _ensure_minimum_size(pixmap: QPixmap, max_size: QSize) -> QPixmap:
        """Ensure pixmap fits within max_size, respecting orientation."""
        if pixmap.isNull():
            return pixmap
        
        is_landscape = pixmap.width() > pixmap.height()
        
        if is_landscape:
            scale_factor = min(max_size.width() / pixmap.width(), max_size.height() / pixmap.height())
            scaled_width = int(pixmap.width() * scale_factor)
            scaled_height = int(pixmap.height() * scale_factor)
            
            if scaled_height > max_size.height() * 0.95:
                scale_factor = max_size.height() / pixmap.height()
                scaled_width = int(pixmap.width() * scale_factor)
                scaled_height = int(pixmap.height() * scale_factor)
        else:
            scale_factor = min(max_size.width() / pixmap.width(), max_size.height() / pixmap.height())
            scaled_width = int(pixmap.width() * scale_factor)
            scaled_height = int(pixmap.height() * scale_factor)
            
            min_width = int(max_size.width() * 0.8)
            min_height = int(max_size.height() * 0.8)
            if scaled_width < min_width or scaled_height < min_height:
                scale_factor = max(min_width / pixmap.width(), min_height / pixmap.height())
                scaled_width = int(pixmap.width() * scale_factor)
                scaled_height = int(pixmap.height() * scale_factor)
        
        return pixmap.scaled(
            scaled_width, scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    @staticmethod
    def render_page(pdf_path: str, max_size: QSize, page_num: int = 0) -> QPixmap:
        """Render specific page of PDF as pixmap using PyMuPDF.
        
        R12: Hard file size limits prevent preview of oversized files.
        R13: Early existence validation before rendering.
        R14: Pixmap validation before returning.
        """
        if not FITZ_AVAILABLE:
            logger.error("PyMuPDF (fitz) not available - module not imported")
            return QPixmap()
        
        is_valid, error_msg = validate_file_for_preview(pdf_path)
        if not is_valid:
            logger.warning(f"Cannot render PDF {pdf_path}: {error_msg}")
            return QPixmap()
        
        doc = None
        try:
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                logger.warning(f"PDF has 0 pages: {pdf_path}")
                return QPixmap()
            
            qpixmap = PdfRenderer._render_page_to_pixmap(doc, page_num, 2.5)
            
            if validate_pixmap(qpixmap):
                result = PdfRenderer._ensure_minimum_size(qpixmap, max_size)
                if validate_pixmap(result):
                    return result
            
            return QPixmap()
        except Exception as e:
            logger.error(f"Error rendering PDF page {page_num} from {pdf_path}: {e}", exc_info=True)
            return QPixmap()
        finally:
            if doc:
                try:
                    doc.close()
                except Exception:
                    pass
    
    @staticmethod
    def render_thumbnail(pdf_path: str, page_num: int, thumbnail_size: QSize) -> QPixmap:
        """Get thumbnail of a specific PDF page.
        
        R5: All PyMuPDF access is encapsulated in try/except.
        R12: Hard file size limits prevent preview of oversized files.
        R13: Early existence validation before rendering.
        R14: Pixmap validation before returning.
        """
        if not FITZ_AVAILABLE:
            return QPixmap()
        
        try:
            if not pdf_path or not os.path.exists(pdf_path):
                return QPixmap()
            if not os.path.isfile(pdf_path):
                return QPixmap()
        except (OSError, ValueError):
            return QPixmap()
        
        doc = None
        try:
            try:
                doc = fitz.open(pdf_path)
            except Exception as e:
                logger.warning(f"Cannot open PDF for thumbnail: {e}")
                return QPixmap()
            
            qpixmap = PdfRenderer._render_page_to_pixmap(doc, page_num, 0.5)
            
            if validate_pixmap(qpixmap):
                try:
                    scaled = qpixmap.scaled(
                        thumbnail_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    if validate_pixmap(scaled):
                        return scaled
                except Exception as e:
                    logger.warning(f"Failed to scale thumbnail: {e}")
            
            return QPixmap()
        except Exception as e:
            logger.error(f"Exception in render_thumbnail: {e}", exc_info=True)
            return QPixmap()
        finally:
            if doc:
                try:
                    doc.close()
                except Exception:
                    pass

