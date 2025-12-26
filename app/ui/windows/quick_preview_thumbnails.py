"""
Quick Preview Thumbnails - PDF page thumbnail panel.

Handles thumbnail generation, display, and interaction for PDF pages.
"""

from functools import partial
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget
from app.ui.windows.quick_preview_constants import GENERATING_THUMBNAILS, DOCUMENT_READY

from app.core.logger import get_logger
from app.services.preview_pdf_service import PreviewPdfService
from app.services.preview_file_extensions import validate_pixmap
from app.ui.windows.quick_preview_styles import get_thumbnail_scrollbar_style
from app.ui.windows.quick_preview_thumbnail_widget import QuickPreviewThumbnailWidget

logger = get_logger(__name__)


class QuickPreviewThumbnails:
    """Manages PDF page thumbnail panel."""
    
    def __init__(self, preview_service: PreviewPdfService):
        """
        Initialize thumbnail panel.
        
        Args:
            preview_service: PreviewPdfService instance.
        """
        self._preview_service = preview_service
        self._panel = None
        self._scroll = None
        self._container = None
        self._layout = None
        self._current_page = 0
        self._total_pages = 0
        self._pdf_path = None
    
    def create_panel(self) -> QWidget:
        """
        Create and configure thumbnail panel widget.
        
        Returns:
            Configured thumbnail panel widget.
        """
        self._panel = QWidget()
        self._panel.setFixedWidth(0)  # Hidden by default
        self._panel.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-right: 1px solid rgba(200, 200, 200, 150);
            }
        """)
        
        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(6, 8, 6, 8)
        panel_layout.setSpacing(4)
        
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(get_thumbnail_scrollbar_style())
        
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.addStretch()
        
        self._scroll.setWidget(self._container)
        panel_layout.addWidget(self._scroll)
        
        return self._panel
    
    def load_thumbnails_async(self, pdf_path: str, total_pages: int, current_page: int, 
                       on_click_callback, progress_cb=None, finished_cb=None) -> str:
        """
        Load all PDF page thumbnails.
        
        R1: Returns request_id for validation.
        R4: Ensures fallback visual for failed thumbnails.
        
        Args:
            pdf_path: Path to PDF file.
            total_pages: Total number of pages.
            current_page: Currently selected page (0-indexed).
            on_click_callback: Callback function(page_num) for thumbnail clicks.
            progress_cb: Optional callback(percent, text) for progress updates.
            finished_cb: Optional callback() when finished.
        
        Returns:
            request_id: Unique identifier for this request.
        """
        while self._layout.count() > 1:  # Keep stretch
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._pdf_path = pdf_path
        self._total_pages = total_pages
        self._current_page = current_page
        
        thumbnail_size = QSize(100, 120)
        
        request_id_holder = {"value": None}
        
        def on_progress(page_num: int, pixmap: QPixmap, result_request_id: str):
            if request_id_holder["value"] and result_request_id != request_id_holder["value"]:
                logger.debug(f"Ignoring stale thumbnail (current: {request_id_holder['value']}, received: {result_request_id})")
                return
            
            if validate_pixmap(pixmap):
                try:
                    thumb_container = QuickPreviewThumbnailWidget.create(
                        pixmap, page_num, current_page, on_click_callback
                    )
                    self._layout.insertWidget(page_num, thumb_container)
                except Exception as e:
                    logger.warning(f"Error creating thumbnail widget: {e}")
            
            if progress_cb:
                try:
                    pct = int(((page_num + 1) / max(1, total_pages)) * 100)
                    progress_cb(pct, GENERATING_THUMBNAILS)
                except Exception:
                    pass
        
        def on_finished(result_request_id: str):
            if request_id_holder["value"] and result_request_id != request_id_holder["value"]:
                logger.debug(f"Ignoring stale thumbnail finished (current: {request_id_holder['value']}, received: {result_request_id})")
                return
            
            logger.debug(f"Thumbnails finished loading, total widgets: {self._layout.count() - 1}")
            
            if finished_cb:
                try:
                    finished_cb()
                except Exception:
                    pass
            if progress_cb:
                try:
                    progress_cb(100, DOCUMENT_READY)
                except Exception:
                    pass
        
        def on_error(msg: str, result_request_id: str):
            if request_id_holder["value"] and result_request_id != request_id_holder["value"]:
                logger.debug("Ignoring stale thumbnail error")
                return
            
            logger.warning(f"Thumbnails error: {msg}")
            
            if finished_cb:
                try:
                    finished_cb()
                except Exception:
                    pass
        
        request_id_holder["value"] = self._preview_service.render_thumbnails_async(
            pdf_path,
            total_pages,
            thumbnail_size,
            on_progress,
            on_finished,
            on_error=on_error,
        )
        
        logger.debug(f"Started loading {total_pages} thumbnails for {pdf_path} with request_id: {request_id_holder['value']}")
        
        return request_id_holder["value"]
    
    def update_selection(self, current_page: int) -> None:
        """
        Update thumbnail selection highlight.
        
        Args:
            current_page: Currently selected page (0-indexed).
        """
        self._current_page = current_page
        for i in range(self._layout.count() - 1):  # Exclude stretch
            item = self._layout.itemAt(i)
            if item and item.widget():
                thumb_container = item.widget()
                is_selected = i == current_page
                QuickPreviewThumbnailWidget.update_style(thumb_container, is_selected)
    
    def scroll_to_thumbnail(self, page_num: int) -> None:
        """
        Scroll thumbnails panel to show selected thumbnail.
        
        Args:
            page_num: Page number to scroll to (0-indexed).
        """
        if page_num < self._layout.count() - 1:
            item = self._layout.itemAt(page_num)
            if item and item.widget():
                widget = item.widget()
                self._scroll.ensureWidgetVisible(widget, 0, 20)
    
    def show(self) -> None:
        """Show thumbnail panel."""
        if self._panel:
            self._panel.setFixedWidth(140)
    
    def hide(self) -> None:
        """Hide thumbnail panel."""
        if self._panel:
            self._panel.setFixedWidth(0)

