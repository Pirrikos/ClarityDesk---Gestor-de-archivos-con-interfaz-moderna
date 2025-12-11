"""
Quick Preview Thumbnails - PDF page thumbnail panel.

Handles thumbnail generation, display, and interaction for PDF pages.
"""

from functools import partial
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from app.services.preview_service import PreviewService
from app.ui.windows.quick_preview_styles import get_thumbnail_scrollbar_style
from app.ui.windows.quick_preview_thumbnail_widget import QuickPreviewThumbnailWidget


class QuickPreviewThumbnails:
    """Manages PDF page thumbnail panel."""
    
    def __init__(self, preview_service: PreviewService):
        """
        Initialize thumbnail panel.
        
        Args:
            preview_service: PreviewService instance.
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
    
    def load_thumbnails(self, pdf_path: str, total_pages: int, current_page: int, 
                       on_click_callback) -> None:
        """
        Load all PDF page thumbnails.
        
        Args:
            pdf_path: Path to PDF file.
            total_pages: Total number of pages.
            current_page: Currently selected page (0-indexed).
            on_click_callback: Callback function(page_num) for thumbnail clicks.
        """
        while self._layout.count() > 1:  # Keep stretch
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._pdf_path = pdf_path
        self._total_pages = total_pages
        self._current_page = current_page
        
        thumbnail_size = QSize(100, 120)
        
        for page_num in range(total_pages):
            thumbnail = self._preview_service.get_pdf_thumbnail(
                pdf_path, page_num, thumbnail_size
            )
            
            if not thumbnail.isNull():
                thumb_container = QuickPreviewThumbnailWidget.create(
                    thumbnail, page_num, current_page, on_click_callback
                )
                self._layout.insertWidget(page_num, thumb_container)
    
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

