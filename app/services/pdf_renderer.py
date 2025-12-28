"""
PDF Renderer - PDF page rendering using PyMuPDF.

Handles rendering of PDF pages to QPixmap for previews and thumbnails.
"""

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
        """Render PDF page to QPixmap with given zoom, respecting orientation.
        
        R5: All PyMuPDF access is encapsulated in try/except.
        """
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
                logger.warning(f"R5: Failed to load pixmap from PPM data")
                return QPixmap()
            return qpixmap
        except Exception as e:
            # R5: No exception crosses renderer boundary
            logger.error(f"R5: Exception in _render_page_to_pixmap: {e}", exc_info=True)
            return QPixmap()
    
    
    @staticmethod
    def render_page(pdf_path: str, max_size: QSize, page_num: int = 0, device_pixel_ratio: float = 1.0) -> QPixmap:
        """Render specific page of PDF as pixmap using PyMuPDF.
        
        R12: Hard file size limits prevent preview of oversized files.
        R13: Early existence validation before rendering.
        R14: Pixmap validation before returning.
        
        Args:
            pdf_path: Path to PDF file.
            max_size: Maximum size for rendered pixmap (in pixels).
            page_num: Page number to render (0-indexed).
            device_pixel_ratio: Device pixel ratio for high-DPI displays (default: 1.0).
        
        Returns:
            QPixmap with rendered page, or empty QPixmap on error.
        """
        if not FITZ_AVAILABLE:
            logger.error("PyMuPDF (fitz) not available - module not imported")
            return QPixmap()
        
        # Guarda B: El renderer asume que recibe max_size válido (validado por el caller)
        # Si max_size es inválido, devolver QPixmap() vacío (error controlado)
        if max_size.width() < 50 or max_size.height() < 50:
            logger.warning(f"PdfRenderer.render_page: Invalid max_size {max_size.width()}x{max_size.height()}, returning empty pixmap")
            return QPixmap()
        
        # R13: Early existence validation
        # R12: Hard size limit check
        is_valid, error_msg = validate_file_for_preview(pdf_path)
        if not is_valid:
            logger.warning(f"R12/R13: Cannot render PDF {pdf_path}: {error_msg}")
            return QPixmap()
        
        logger.debug(f"render_page: File validated, proceeding with render for {pdf_path}")
        
        doc = None
        try:
            logger.debug(f"render_page: Opening PDF {pdf_path}, page {page_num}")
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                logger.warning(f"render_page: PDF has 0 pages: {pdf_path}")
                return QPixmap()
            
            logger.debug(f"render_page: PDF has {len(doc)} pages, rendering page {page_num}")
            
            # Obtener tamaño de página PDF (en puntos, 72 DPI)
            page = doc[page_num]
            page_rect = page.rect
            page_width_pt = page_rect.width
            page_height_pt = page_rect.height
            
            # Calcular zoom considerando DPI del dispositivo
            target_width_px = max_size.width() * device_pixel_ratio
            target_height_px = max_size.height() * device_pixel_ratio
            
            # Regla 1: Zoom base (fit)
            zoom_x = target_width_px / page_width_pt
            zoom_y = target_height_px / page_height_pt
            zoom_fit = min(zoom_x, zoom_y)  # Mantener aspect ratio (fit completo)
            
            # Regla 2: Zoom mínimo de legibilidad (fill-ish)
            ZOOM_MIN_FACTOR = 0.8
            min_width_px = max_size.width() * ZOOM_MIN_FACTOR * device_pixel_ratio
            min_height_px = max_size.height() * ZOOM_MIN_FACTOR * device_pixel_ratio
            min_zoom_x = min_width_px / page_width_pt
            min_zoom_y = min_height_px / page_height_pt
            zoom_min = max(min_zoom_x, min_zoom_y)
            
            # Regla 3: Zoom final
            zoom = max(zoom_fit, zoom_min)
            
            logger.debug(f"render_page: Calculated zoom - fit={zoom_fit:.3f}, min={zoom_min:.3f}, final={zoom:.3f}, dpr={device_pixel_ratio}")
            
            qpixmap = PdfRenderer._render_page_to_pixmap(doc, page_num, zoom)
            
            # R14: Validate pixmap before returning
            if validate_pixmap(qpixmap):
                logger.debug(f"render_page: Page rendered, size: {qpixmap.width()}x{qpixmap.height()}")
                return qpixmap
            else:
                logger.warning(f"R14: _render_page_to_pixmap returned invalid pixmap (size: {qpixmap.width()}x{qpixmap.height()}, null: {qpixmap.isNull()})")
            
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
        """
        if not FITZ_AVAILABLE:
            return QPixmap()
        
        doc = None
        try:
            # R5: Encapsulate file access
            try:
                doc = fitz.open(pdf_path)
            except Exception as e:
                logger.warning(f"R5: Cannot open PDF for thumbnail: {e}")
                return QPixmap()
            
            qpixmap = PdfRenderer._render_page_to_pixmap(doc, page_num, 0.5)
            
            if not qpixmap.isNull():
                try:
                    return qpixmap.scaled(
                        thumbnail_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                except Exception as e:
                    logger.warning(f"R5: Failed to scale thumbnail: {e}")
                    return QPixmap()
            
            return QPixmap()
        except Exception as e:
            # R5: No exception crosses renderer boundary
            logger.error(f"R5: Exception in render_thumbnail: {e}", exc_info=True)
            return QPixmap()
        finally:
            if doc:
                try:
                    doc.close()
                except Exception:
                    pass

