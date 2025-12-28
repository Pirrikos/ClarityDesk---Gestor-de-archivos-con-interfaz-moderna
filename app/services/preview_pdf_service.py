"""
PreviewPdfService - PDF and DOCX preview rendering.

Handles PDF page rendering and DOCX to PDF conversion for quick preview.
Supports both synchronous and asynchronous (QThread) rendering.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Callable

from PySide6.QtCore import QSize, Qt, QThread
from PySide6.QtGui import QPixmap, QImage

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
    is_previewable_text,
    normalize_extension,
    validate_file_for_preview,
    validate_pixmap
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
    """Service for generating PDF and DOCX preview images.
    
    R1: Each request has unique request_id.
    R2: Cooperative cancellation - workers mark requests as invalid.
    R6: Validates results before publishing to UI.
    """
    
    def __init__(self, icon_service) -> None:
        """Initialize PreviewPdfService with icon service."""
        self._icon_service = icon_service
        self._pdf_renderer = PdfRenderer()
        self._docx_converter = DocxConverter()
        self._active_pdf_worker: Optional[PdfRenderWorker] = None
        self._active_docx_worker: Optional[DocxConvertWorker] = None
        self._active_thumbs_worker: Optional[PdfThumbnailsWorker] = None
        self._current_request_id: Optional[str] = None  # R1: Track current request

    def _cancel_worker(self, worker: Optional[QThread], timeout_ms: int = 2000) -> None:
        """Cancel worker cooperatively (R2) and wait for completion."""
        if not worker:
            return
        try:
            if hasattr(worker, 'cancel'):
                worker.cancel()
        except Exception:
            pass
        try:
            worker.quit()
            if not worker.wait(timeout_ms):
                # Force termination if still running after timeout
                worker.terminate()
                worker.wait(500)
        except Exception:
            pass
    
    def get_pdf_page_count(self, pdf_path: str) -> int:
        """Get total number of pages in PDF."""
        return self._pdf_renderer.get_page_count(pdf_path)

    def render_pdf_page(self, pdf_path: str, max_size: QSize, page_num: int = 0) -> QPixmap:
        """Render specific page of PDF as pixmap using PyMuPDF (synchronous)."""
        pixmap = self._pdf_renderer.render_page(pdf_path, max_size, page_num)
        if pixmap.isNull():
            logger.warning(f"Failed to render PDF page {page_num} from {pdf_path}")
        return pixmap
    
    def render_pdf_page_async(
        self,
        pdf_path: str,
        max_size: QSize,
        page_num: int,
        on_finished: Callable[[QPixmap], None],
        on_error: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Render PDF page asynchronously using QThread worker.
        
        R1: Returns request_id for validation.
        R2: Cancels previous worker cooperatively.
        R6: Validates result before calling callback.
        
        Args:
            pdf_path: Path to PDF file.
            max_size: Maximum size for rendered pixmap.
            page_num: Page number to render (0-indexed).
            on_finished: Callback called with QPixmap when rendering completes.
            on_error: Optional callback called with error message on failure.
        
        Returns:
            request_id: Unique identifier for this request.
        """
        # Prioridad 0: Asegurar que solo hay un render activo
        if self._active_pdf_worker and self._active_pdf_worker.isRunning():
            # Invalidar request_id anterior antes de cancelar
            old_request_id = self._current_request_id
            self._current_request_id = None
            self._cancel_worker(self._active_pdf_worker)
            # Esperar a que termine completamente antes de continuar
            if self._active_pdf_worker.isRunning():
                return None  # Worker anterior aún activo, rechazar nuevo request
        
        # R1: Generate unique request_id
        request_id = str(uuid.uuid4())
        self._current_request_id = request_id
        
        worker = PdfRenderWorker(pdf_path, max_size, page_num, request_id)
        self._active_pdf_worker = worker
        
        def handle_finished(qimage: QImage, result_request_id: str) -> None:
            try:
                if result_request_id != self._current_request_id:
                    return
                
                # Prioridad 1: Convertir QImage a QPixmap en el hilo GUI
                if qimage.isNull():
                    if on_error:
                        try:
                            on_error("Failed to render PDF page")
                        except Exception as e:
                            logger.warning(f"Error in on_error callback: {e}", exc_info=True)
                    else:
                        try:
                            on_finished(QPixmap())
                        except Exception as e:
                            logger.warning(f"Error in on_finished callback: {e}", exc_info=True)
                    return
                
                pixmap = QPixmap.fromImage(qimage)
                if not validate_pixmap(pixmap):
                    if on_error:
                        try:
                            on_error("Failed to render PDF page")
                        except Exception as e:
                            logger.warning(f"Error in on_error callback: {e}", exc_info=True)
                    else:
                        try:
                            on_finished(QPixmap())
                        except Exception as e:
                            logger.warning(f"Error in on_finished callback: {e}", exc_info=True)
                    return
                
                self._active_pdf_worker = None
                try:
                    on_finished(pixmap)
                except Exception as e:
                    logger.warning(f"Error in on_finished callback: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Exception in handle_finished: {e}", exc_info=True)
                self._active_pdf_worker = None
        
        def handle_error(error_msg: str, result_request_id: str) -> None:
            try:
                if result_request_id != self._current_request_id:
                    return
                
                self._active_pdf_worker = None
                if on_error:
                    try:
                        on_error(error_msg)
                    except Exception as e:
                        logger.warning(f"Error in on_error callback: {e}", exc_info=True)
                else:
                    try:
                        on_finished(QPixmap())
                    except Exception as e:
                        logger.warning(f"Error in on_finished callback: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Exception in handle_error: {e}", exc_info=True)
                self._active_pdf_worker = None
        
        worker.finished.connect(handle_finished)
        worker.error.connect(handle_error)
        worker.start()
        
        return request_id
    
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
    ) -> str:
        """Render thumbnails in background and emit progress.

        R1: Returns request_id for validation.
        R2: Cancels previous worker cooperatively.
        R6: Validates results before calling callbacks.

        on_progress(page_num: int, pixmap: QPixmap, request_id: str)
        on_finished(request_id: str)
        on_error(msg: str, request_id: str)
        
        Returns:
            request_id: Unique identifier for this request.
        """
        # Prioridad 0: Asegurar que solo hay un render activo
        if self._active_thumbs_worker and self._active_thumbs_worker.isRunning():
            # Invalidar request_id anterior antes de cancelar (thumbnails no usa _current_request_id del servicio)
            self._cancel_worker(self._active_thumbs_worker)
            # Esperar a que termine completamente antes de continuar
            if self._active_thumbs_worker.isRunning():
                return None  # Worker anterior aún activo, rechazar nuevo request
        
        self._active_thumbs_worker = None

        # R1: Generate unique request_id
        request_id = str(uuid.uuid4())

        worker = PdfThumbnailsWorker(pdf_path, total_pages, thumbnail_size, request_id)
        self._active_thumbs_worker = worker

        def _on_progress(page_num: int, qimage: QImage, result_request_id: str):
            try:
                if result_request_id != request_id:
                    return
                # Prioridad 1: Convertir QImage a QPixmap en el hilo GUI
                if qimage.isNull():
                    return
                pixmap = QPixmap.fromImage(qimage)
                if validate_pixmap(pixmap):
                    try:
                        on_progress(page_num, pixmap, result_request_id)
                    except Exception as e:
                        logger.warning(f"Error in on_progress callback: {e}", exc_info=True)
            except Exception as e:
                logger.warning(f"Error in thumbnail progress callback: {e}", exc_info=True)

        def _on_finished(result_request_id: str):
            try:
                if result_request_id != request_id:
                    return
                self._active_thumbs_worker = None
                try:
                    # Pasar result_request_id al callback si lo acepta
                    import inspect
                    sig = inspect.signature(on_finished)
                    if len(sig.parameters) > 0:
                        on_finished(result_request_id)
                    else:
                        on_finished()
                except Exception as e:
                    logger.warning(f"Error in on_finished callback: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Exception in _on_finished: {e}", exc_info=True)
                self._active_thumbs_worker = None

        def _on_error(msg: str, result_request_id: str):
            try:
                if result_request_id != request_id:
                    return
                self._active_thumbs_worker = None
                if on_error:
                    try:
                        on_error(msg)
                    except Exception as e:
                        logger.warning(f"Error in on_error callback: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Exception in _on_error: {e}", exc_info=True)
                self._active_thumbs_worker = None

        worker.progress.connect(_on_progress)
        worker.finished.connect(_on_finished)
        worker.error.connect(_on_error)
        worker.start()
        
        return request_id
    
    def _convert_docx_to_pdf(self, docx_path: str) -> str:
        """Convert DOCX to PDF using docx2pdf (synchronous)."""
        return self._docx_converter.convert_to_pdf(docx_path)
    
    def convert_docx_to_pdf_async(
        self,
        docx_path: str,
        on_finished: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Convert DOCX to PDF asynchronously using QThread worker.
        
        R1: Returns request_id for validation.
        R2: Cancels previous worker cooperatively.
        R6: Validates result before calling callback.
        
        Args:
            docx_path: Path to DOCX file.
            on_finished: Callback called with PDF path when conversion completes.
            on_error: Optional callback called with error message on failure.
        
        Returns:
            request_id: Unique identifier for this request.
        """
        # Prioridad 0: Asegurar que solo hay un render activo
        if self._active_docx_worker and self._active_docx_worker.isRunning():
            self._cancel_worker(self._active_docx_worker)
            if self._active_docx_worker.isRunning():
                logger.warning(f"Previous worker still running, rejecting request")
                return None
        
        request_id = str(uuid.uuid4())
        worker = DocxConvertWorker(docx_path, request_id)
        self._active_docx_worker = worker
        
        def handle_finished(pdf_path: str, result_request_id: str) -> None:
            try:
                if not pdf_path or not os.path.exists(pdf_path):
                    if on_error:
                        try:
                            on_error("Failed to convert DOCX to PDF")
                        except Exception as e:
                            logger.warning(f"Error in on_error callback: {e}", exc_info=True)
                    else:
                        try:
                            on_finished("")
                        except Exception as e:
                            logger.warning(f"Error in on_finished callback: {e}", exc_info=True)
                    return
                
                self._active_docx_worker = None
                try:
                    on_finished(pdf_path)
                except Exception as e:
                    logger.warning(f"Error in on_finished callback: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Exception in handle_finished: {e}", exc_info=True)
                self._active_docx_worker = None
        
        def handle_error(error_msg: str, result_request_id: str) -> None:
            try:
                self._active_docx_worker = None
                if on_error:
                    try:
                        on_error(error_msg)
                    except Exception as e:
                        logger.warning(f"Error in on_error callback: {e}", exc_info=True)
                else:
                    try:
                        on_finished("")
                    except Exception as e:
                        logger.warning(f"Error in on_finished callback: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Exception in handle_error: {e}", exc_info=True)
                self._active_docx_worker = None
        
        worker.finished.connect(handle_finished)
        worker.error.connect(handle_error)
        worker.start()
        
        return request_id

    def get_quicklook_pixmap(self, path: str, max_size: QSize) -> QPixmap:
        """Get pixmap for quick preview with real rendering for PDFs, DOCX, images, and text files.
        
        R5: All external access is encapsulated in try/except.
        R4: Always returns valid pixmap (may be empty for fallback).
        R12: Hard file size limits prevent preview of oversized files.
        R13: Early existence validation before any rendering.
        R14: Pixmap validation before returning.
        """
        is_valid, error_msg = validate_file_for_preview(path)
        if not is_valid:
            logger.warning(f"Cannot preview {path}: {error_msg}")
            return QPixmap()

        ext = normalize_extension(path)
        
        if ext == ".pdf":
            try:
                pdf_pixmap = self.render_pdf_page(path, max_size)
                if validate_pixmap(pdf_pixmap):
                    return pdf_pixmap
            except Exception as e:
                logger.error(f"Exception rendering PDF: {e}", exc_info=True)

        elif ext == ".docx":
            try:
                pdf_path = self._convert_docx_to_pdf(path)
                if pdf_path:
                    pdf_pixmap = self.render_pdf_page(pdf_path, max_size)
                    if validate_pixmap(pdf_pixmap):
                        return pdf_pixmap
            except Exception as e:
                logger.error(f"Exception converting DOCX: {e}", exc_info=True)

        if is_previewable_image(ext):
            try:
                pixmap = render_image_preview(path, max_size)
                if validate_pixmap(pixmap):
                    return pixmap
            except Exception as e:
                logger.error(f"Exception rendering image: {e}", exc_info=True)

        if is_previewable_text(ext):
            try:
                pixmap = self._render_text_preview(path, max_size)
                if validate_pixmap(pixmap):
                    return pixmap
            except Exception as e:
                logger.error(f"Exception rendering text: {e}", exc_info=True)

        try:
            from app.services.icon_render_service import IconRenderService
            render_service = IconRenderService(self._icon_service)
            base = render_service.get_file_preview(path, max_size)
            if base.isNull():
                return QPixmap()

            scaled = base.scaled(
                max_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            if not validate_pixmap(scaled):
                return QPixmap()
            return scaled
        except Exception as e:
            logger.error(f"Exception getting icon fallback: {e}", exc_info=True)
            return QPixmap()
    
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
        """Stop all workers and disconnect signals (Prioridad 2: cierre robusto)."""
        if self._active_pdf_worker:
            try:
                # Prioridad 2: Desconectar señales antes de cancelar
                self._active_pdf_worker.finished.disconnect()
                self._active_pdf_worker.error.disconnect()
            except (TypeError, RuntimeError):
                pass  # Señales ya desconectadas o worker destruido
            try:
                self._active_pdf_worker.cancel()
            except Exception:
                pass
            self._active_pdf_worker.quit()
            self._active_pdf_worker.wait()
            self._active_pdf_worker = None
        if self._active_docx_worker:
            try:
                # Prioridad 2: Desconectar señales antes de cancelar
                self._active_docx_worker.finished.disconnect()
                self._active_docx_worker.error.disconnect()
            except (TypeError, RuntimeError):
                pass  # Señales ya desconectadas o worker destruido
            try:
                self._active_docx_worker.cancel()
            except Exception:
                pass
            self._active_docx_worker.quit()
            self._active_docx_worker.wait()
            self._active_docx_worker = None
        if self._active_thumbs_worker:
            try:
                # Prioridad 2: Desconectar señales antes de cancelar
                self._active_thumbs_worker.progress.disconnect()
                self._active_thumbs_worker.finished.disconnect()
                self._active_thumbs_worker.error.disconnect()
            except (TypeError, RuntimeError):
                pass  # Señales ya desconectadas o worker destruido
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

