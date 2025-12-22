"""
PDF Renderer - PDF page rendering using PyMuPDF.

Handles rendering of PDF pages to QPixmap for previews and thumbnails.
"""

import sys
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap

from app.core.logger import get_logger

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
        
        page = doc[page_num]
        rect = page.rect
        
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        qpixmap = QPixmap()
        qpixmap.loadFromData(img_data, "PPM")
        return qpixmap
    
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
        """Render specific page of PDF as pixmap using PyMuPDF."""
        if not FITZ_AVAILABLE:
            logger.error("PyMuPDF (fitz) not available - module not imported")
            return QPixmap()
        
        doc = None
        try:
            logger.debug(f"render_page: Opening PDF {pdf_path}, page {page_num}")
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                logger.warning(f"render_page: PDF has 0 pages: {pdf_path}")
                return QPixmap()
            
            logger.debug(f"render_page: PDF has {len(doc)} pages, rendering page {page_num}")
            qpixmap = PdfRenderer._render_page_to_pixmap(doc, page_num, 2.5)
            
            if not qpixmap.isNull():
                logger.debug(f"render_page: Page rendered, size: {qpixmap.width()}x{qpixmap.height()}")
                result = PdfRenderer._ensure_minimum_size(qpixmap, max_size)
                logger.debug(f"render_page: After scaling, size: {result.width()}x{result.height()}")
                return result
            else:
                logger.warning(f"render_page: _render_page_to_pixmap returned null pixmap")
            
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
        """Get thumbnail of a specific PDF page."""
        if not FITZ_AVAILABLE:
            return QPixmap()
        
        doc = None
        try:
            doc = fitz.open(pdf_path)
            qpixmap = PdfRenderer._render_page_to_pixmap(doc, page_num, 0.5)
            
            if not qpixmap.isNull():
                return qpixmap.scaled(
                    thumbnail_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            
            return QPixmap()
        except Exception:
            return QPixmap()
        finally:
            if doc:
                try:
                    doc.close()
                except Exception:
                    pass

