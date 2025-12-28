"""
PdfThumbnailsWorker - QThread worker para generar miniaturas de todas las páginas de un PDF.

Emite progreso fluido por página para permitir actualizar una barra de progreso en UI.
R5: All external access (PyMuPDF) is encapsulated in try/except.
R2: Cooperative cancellation - marks request as invalid, ignores results.
"""

import os
from PySide6.QtCore import QSize, QThread, Signal
from PySide6.QtGui import QPixmap, QImage

from app.core.logger import get_logger
from app.services.pdf_renderer import PdfRenderer
from app.services.preview_file_extensions import validate_file_for_preview, validate_pixmap

logger = get_logger(__name__)


class PdfThumbnailsWorker(QThread):
    """Genera miniaturas de páginas PDF en segundo plano."""

    progress = Signal(int, object, object)  # (page_num, QImage, request_id) - Prioridad 1: QImage es thread-safe
    finished = Signal(object)  # request_id
    error = Signal(str, object)  # (error_msg, request_id)

    def __init__(self, pdf_path: str, total_pages: int, thumbnail_size: QSize, request_id: str = None):
        super().__init__()
        self._pdf_path = pdf_path
        self._total_pages = total_pages
        self._size = thumbnail_size
        self.request_id = request_id
        self._cancel_requested = False

    def cancel(self) -> None:
        """Cooperative cancellation - mark request as invalid."""
        self._cancel_requested = True

    def run(self) -> None:
        if self._cancel_requested:
            return
        
        try:
            if not self._pdf_path or not os.path.exists(self._pdf_path):
                logger.warning(f"Cannot generate thumbnails - file does not exist: {self._pdf_path}")
                self.error.emit("File does not exist", self.request_id)
                return
            if not os.path.isfile(self._pdf_path):
                logger.warning(f"Cannot generate thumbnails - not a regular file: {self._pdf_path}")
                self.error.emit("Not a regular file", self.request_id)
                return
        except (OSError, ValueError) as e:
            logger.warning(f"Cannot validate thumbnail file: {e}")
            self.error.emit(f"Cannot access file: {e}", self.request_id)
            return
        
        try:
            for page_num in range(self._total_pages):
                if self._cancel_requested:
                    return
                
                try:
                    pixmap = PdfRenderer.render_thumbnail(self._pdf_path, page_num, self._size)
                    if validate_pixmap(pixmap):
                        # Prioridad 1: Convertir QPixmap a QImage (thread-safe) antes de emitir
                        qimage = pixmap.toImage()
                        if not qimage.isNull():
                            self.progress.emit(page_num, qimage, self.request_id)
                except Exception as e:
                    logger.warning(f"Error rendering thumbnail page {page_num}: {e}")
            
            self.finished.emit(self.request_id)
        except Exception as e:
            logger.error(f"Exception in thumbnails worker: {e}", exc_info=True)
            self.error.emit("Thumbnails error", self.request_id)

