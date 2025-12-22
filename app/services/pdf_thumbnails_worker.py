"""
PdfThumbnailsWorker - QThread worker para generar miniaturas de todas las páginas de un PDF.

Emite progreso fluido por página para permitir actualizar una barra de progreso en UI.
"""

from PySide6.QtCore import QSize, QThread, Signal
from PySide6.QtGui import QPixmap

from app.services.pdf_renderer import PdfRenderer


class PdfThumbnailsWorker(QThread):
    """Genera miniaturas de páginas PDF en segundo plano."""

    progress = Signal(int, object)  # (page_num, QPixmap)
    finished = Signal()
    error = Signal(str)

    def __init__(self, pdf_path: str, total_pages: int, thumbnail_size: QSize):
        super().__init__()
        self._pdf_path = pdf_path
        self._total_pages = total_pages
        self._size = thumbnail_size
        self._cancel_requested = False

    def cancel(self) -> None:
        self._cancel_requested = True

    def run(self) -> None:
        try:
            for page_num in range(self._total_pages):
                if self._cancel_requested:
                    self.error.emit("Cancelled")
                    return
                pixmap = PdfRenderer.render_thumbnail(self._pdf_path, page_num, self._size)
                if pixmap.isNull():
                    # Emit progreso igualmente para mantener fluidez
                    self.progress.emit(page_num, QPixmap())
                else:
                    self.progress.emit(page_num, pixmap)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

