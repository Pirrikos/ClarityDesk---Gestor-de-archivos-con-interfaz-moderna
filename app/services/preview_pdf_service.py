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

from app.core.logger import get_logger
from app.services.docx_converter import DocxConverter
from app.services.pdf_renderer import PdfRenderer
from app.services.pdf_render_worker import PdfRenderWorker
from app.services.docx_convert_worker import DocxConvertWorker
from app.services.pdf_thumbnails_worker import PdfThumbnailsWorker
from app.services.preview_file_extensions import (
    PREVIEW_IMAGE_EXTENSIONS,
    PREVIEW_TEXT_EXTENSIONS,
    is_previewable_image,
    is_previewable_text
)
from app.services.icon_renderer import render_image_preview

try:
    from PIL import Image, ImageDraw, ImageFont
    from PIL.ImageQt import ImageQt
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageQt = None

logger = get_logger(__name__)


class PreviewPdfService:
    """Service for generating PDF and DOCX preview images."""
    
    def __init__(self, icon_service) -> None:
        """Initialize PreviewPdfService with icon service."""
        self._icon_service = icon_service
        self._pdf_renderer = PdfRenderer()
        self._docx_converter = DocxConverter()
        self._active_pdf_worker: Optional[PdfRenderWorker] = None
        self._active_docx_worker: Optional[DocxConvertWorker] = None
        self._active_thumbs_worker: Optional[PdfThumbnailsWorker] = None

    def get_pdf_page_count(self, pdf_path: str) -> int:
        """Get total number of pages in PDF."""
        return self._pdf_renderer.get_page_count(pdf_path)

    def _render_pdf_page(self, pdf_path: str, max_size: QSize, page_num: int = 0) -> QPixmap:
        """Render specific page of PDF as pixmap using PyMuPDF (synchronous)."""
        pixmap = self._pdf_renderer.render_page(pdf_path, max_size, page_num)
        if pixmap.isNull():
            logger.warning(f"Failed to render PDF page {page_num} from {pdf_path}")
        return pixmap
    
    def render_pdf_page(self, pdf_path: str, max_size: QSize, page_num: int = 0) -> QPixmap:
        return self._render_pdf_page(pdf_path, max_size, page_num)
    
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

    def render_thumbnails_async(
        self,
        pdf_path: str,
        total_pages: int,
        thumbnail_size: QSize,
        on_progress,
        on_finished,
        on_error=None,
    ) -> None:
        """Render thumbnails in background and emit progress.

        on_progress(page_num: int, pixmap: QPixmap)
        on_finished()
        on_error(msg: str)
        """
        if self._active_thumbs_worker:
            try:
                self._active_thumbs_worker.cancel()
            except Exception:
                pass
            self._active_thumbs_worker.quit()
            self._active_thumbs_worker.wait()
            self._active_thumbs_worker = None

        worker = PdfThumbnailsWorker(pdf_path, total_pages, thumbnail_size)
        self._active_thumbs_worker = worker

        def _on_progress(page_num: int, pixmap: QPixmap):
            try:
                on_progress(page_num, pixmap)
            except Exception:
                pass

        def _on_finished():
            self._active_thumbs_worker = None
            try:
                on_finished()
            except Exception:
                pass

        def _on_error(msg: str):
            self._active_thumbs_worker = None
            if on_error:
                try:
                    on_error(msg)
                except Exception:
                    pass

        worker.progress.connect(_on_progress)
        worker.finished.connect(_on_finished)
        worker.error.connect(_on_error)
        worker.start()
    
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
        """Get pixmap for quick preview with real rendering for PDFs, DOCX, images, and text files."""
        if not path or not os.path.exists(path):
            logger.warning(f"get_quicklook_pixmap: Path does not exist: {path}")
            return QPixmap()

        ext = Path(path).suffix.lower()
        
        # PDFs: renderizar página real
        if ext == ".pdf":
            logger.debug(f"get_quicklook_pixmap: Rendering PDF {path} with max_size {max_size.width()}x{max_size.height()}")
            pdf_pixmap = self._render_pdf_page(path, max_size)
            if not pdf_pixmap.isNull():
                logger.debug(f"get_quicklook_pixmap: PDF rendered successfully, size: {pdf_pixmap.width()}x{pdf_pixmap.height()}")
                return pdf_pixmap
            else:
                logger.warning(f"get_quicklook_pixmap: PDF render returned null pixmap for {path}")

        # DOCX: convertir a PDF y renderizar
        elif ext == ".docx":
            pdf_path = self._convert_docx_to_pdf(path)
            if pdf_path:
                pdf_pixmap = self._render_pdf_page(pdf_path, max_size)
                if not pdf_pixmap.isNull():
                    return pdf_pixmap

        # Imágenes: usar render_image_preview directamente con tamaño grande
        if is_previewable_image(ext):
            pixmap = render_image_preview(path, max_size)
            if not pixmap.isNull():
                return pixmap

        # Archivos de texto: renderizar contenido como imagen
        if is_previewable_text(ext):
            pixmap = self._render_text_preview(path, max_size)
            if not pixmap.isNull():
                return pixmap

        # Otros tipos: usar icono grande como fallback
        # Import aquí para evitar importación circular
        from app.services.icon_render_service import IconRenderService
        render_service = IconRenderService(self._icon_service)
        base = render_service.get_file_preview(path, max_size)
        if base.isNull():
            return QPixmap()

        # Escalar manteniendo calidad para preview grande
        return base.scaled(
            max_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    def _render_text_preview(self, path: str, max_size: QSize) -> QPixmap:
        """Render text file content as preview image."""
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow not available, cannot render text preview")
            return QPixmap()
        
        try:
            # Leer contenido del archivo
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                # Intentar con latin-1 si utf-8 falla
                with open(path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            
            # Limitar número de líneas y caracteres por línea
            max_lines = min(50, len(lines))
            lines = lines[:max_lines]
            
            # Crear imagen
            img = Image.new("RGB", (max_size.width(), max_size.height()), "white")
            draw = ImageDraw.Draw(img)
            
            # Intentar usar fuente monospace, fallback a default
            try:
                font_size = max(12, min(16, max_size.height() // 40))
                font = ImageFont.truetype("consola.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("cour.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Calcular espaciado
            line_height = font_size + 4
            padding = 20
            max_chars_per_line = (max_size.width() - 2 * padding) // (font_size // 2)
            
            y = padding
            for line in lines:
                if y + line_height > max_size.height() - padding:
                    break
                
                # Limitar longitud de línea y eliminar caracteres de control
                text = line.rstrip('\n\r\t')[:max_chars_per_line]
                if text.strip():  # Solo dibujar líneas no vacías
                    draw.text((padding, y), text, fill=(0, 0, 0), font=font)
                    y += line_height
            
            return QPixmap.fromImage(ImageQt(img))
        except Exception as e:
            logger.warning(f"Failed to render text preview for {path}: {e}")
            return QPixmap()
    
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
        if self._active_thumbs_worker:
            try:
                self._active_thumbs_worker.cancel()
            except Exception:
                pass
            self._active_thumbs_worker.quit()
            self._active_thumbs_worker.wait()
            self._active_thumbs_worker = None
    
    @property
    def icon_service(self):
        """Get icon service."""
        return self._icon_service

