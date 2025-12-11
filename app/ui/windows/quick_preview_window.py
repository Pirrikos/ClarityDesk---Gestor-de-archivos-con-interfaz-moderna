"""
QuickPreviewWindow - Immersive fullscreen overlay for file preview.

Shows a large preview image with QuickLook-style interface.
Supports navigation, PDF multi-page viewing, and animations.
"""

from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.services.preview_service import PreviewService
from app.ui.windows.quick_preview_cache import QuickPreviewCache
from app.ui.windows.quick_preview_animations import QuickPreviewAnimations
from app.ui.windows.quick_preview_thumbnails import QuickPreviewThumbnails
from app.ui.windows.quick_preview_navigation import QuickPreviewNavigation
from app.ui.windows.quick_preview_ui_setup import QuickPreviewUISetup
from app.ui.windows.quick_preview_pdf_handler import QuickPreviewPdfHandler
from app.ui.windows.quick_preview_loader import QuickPreviewLoader
from app.ui.windows.quick_preview_header import QuickPreviewHeader


class QuickPreviewWindow(QWidget):
    """Immersive fullscreen overlay for quick preview."""
    
    def __init__(
        self,
        preview_service: PreviewService,
        file_path: str = None,
        file_paths: list[str] = None,
        start_index: int = 0,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize QuickPreviewWindow."""
        super().__init__(parent)
        self._preview_service = preview_service
        
        if file_paths is None:
            if file_path is None:
                raise ValueError("Either file_path or file_paths must be provided")
            self._paths = [file_path]
            self._index = 0
        else:
            self._paths = file_paths
            self._index = max(0, min(start_index, len(file_paths) - 1))
        
        self._cache = QuickPreviewCache(preview_service)
        self._thumbnails = QuickPreviewThumbnails(preview_service)
        self._animations = QuickPreviewAnimations()
        self._pdf_handler = QuickPreviewPdfHandler(preview_service)
        self._header = QuickPreviewHeader()
        self._loader = None  # Will be initialized after UI setup
        self._navigation = None  # Will be initialized after UI setup
        
        self._setup_ui()
        self._loader = QuickPreviewLoader(self._cache, self._pdf_handler)
        self._setup_navigation()
        self._load_preview()
        self._animations.animate_entrance(self)
    
    def _setup_ui(self) -> None:
        """Build the UI layout."""
        max_size = QuickPreviewUISetup.setup_window(self)
        self._cache.set_max_size(max_size)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        header_widget = self._header.create_header()
        main_layout.addWidget(header_widget)
        
        thumbnails_panel = self._thumbnails.create_panel()
        self._image_label = QLabel()
        content_layout = QuickPreviewUISetup.create_content_area(
            thumbnails_panel, self._image_label
        )
        main_layout.addLayout(content_layout)
    
    def _setup_navigation(self) -> None:
        """Setup navigation handler."""
        self._navigation = QuickPreviewNavigation(
            self, self._paths, self._index, self._pdf_handler.is_pdf,
            self._pdf_handler.current_page, self._pdf_handler.total_pages,
            self._prev, self._next, self._prev_page, self._next_page,
            self.close
        )
    
    def _load_pdf_info(self, path: str) -> None:
        """Load PDF/DOCX information and setup thumbnails."""
        is_new_file = self._pdf_handler.load_pdf_info(path)
        
        if self._pdf_handler.total_pages > 1:
            self._thumbnails.show()
            if is_new_file:
                pdf_path = self._pdf_handler.pdf_path or path
                self._thumbnails.load_thumbnails(
                    pdf_path, self._pdf_handler.total_pages, 
                    self._pdf_handler.current_page,
                    self._on_thumbnail_clicked
                )
            else:
                self._thumbnails.update_selection(self._pdf_handler.current_page)
        else:
            self._thumbnails.hide()
    
    def _on_thumbnail_clicked(self, page_num: int) -> None:
        """Handle thumbnail click to change page."""
        if 0 <= page_num < self._pdf_handler.total_pages:
            self._pdf_handler.current_page = page_num
            self._load_preview(use_crossfade=True)
            self._thumbnails.update_selection(self._pdf_handler.current_page)
            QTimer.singleShot(50, lambda: self._thumbnails.scroll_to_thumbnail(page_num))
    
    def _load_preview(self, use_crossfade: bool = True) -> None:
        """Load and display the file preview."""
        current_path = self._paths[self._index] if self._paths else ""
        
        if QuickPreviewPdfHandler.is_pdf_or_docx_file(current_path):
            self._load_pdf_info(current_path)
        
        result = self._loader.load_preview(
            self._paths, self._index, self._image_label,
            use_crossfade, self._animations
        )
        
        pixmap, header_text = result
        
        if not QuickPreviewPdfHandler.is_pdf_or_docx_file(current_path):
            self._pdf_handler.reset_for_new_file()
            self._thumbnails.hide()
        
        self._header.update_file(current_path, header_text, self.close)
        
        if pixmap:
            if use_crossfade:
                self._animations.apply_crossfade(self._image_label, pixmap)
            else:
                self._image_label.setPixmap(pixmap)
        
        self._loader.preload_and_cleanup(self._index, self._paths)
        self._update_navigation_state()
    
    def _update_navigation_state(self) -> None:
        """Update navigation handler state."""
        if self._navigation:
            self._navigation.update_state(
                self._index, self._pdf_handler.is_pdf,
                self._pdf_handler.current_page, self._pdf_handler.total_pages
            )
    
    def _prev(self) -> None:
        """Navigate to previous file."""
        if self._index > 0:
            self._index -= 1
            self._pdf_handler.current_page = 0
            self._load_preview(use_crossfade=True)
    
    def _next(self) -> None:
        """Navigate to next file."""
        if self._index < len(self._paths) - 1:
            self._index += 1
            self._pdf_handler.current_page = 0
            self._load_preview(use_crossfade=True)
    
    def _prev_page(self) -> None:
        """Navigate to previous PDF page."""
        if self._pdf_handler.current_page > 0:
            self._pdf_handler.current_page -= 1
            self._load_preview(use_crossfade=True)
            self._thumbnails.update_selection(self._pdf_handler.current_page)
            self._thumbnails.scroll_to_thumbnail(self._pdf_handler.current_page)
    
    def _next_page(self) -> None:
        """Navigate to next PDF page."""
        if self._pdf_handler.current_page < self._pdf_handler.total_pages - 1:
            self._pdf_handler.current_page += 1
            self._load_preview(use_crossfade=True)
            self._thumbnails.update_selection(self._pdf_handler.current_page)
            self._thumbnails.scroll_to_thumbnail(self._pdf_handler.current_page)
    
    def keyPressEvent(self, event) -> None:
        """Handle key press events."""
        if self._navigation and self._navigation.handle_key_press(event):
            return
        super().keyPressEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        if self._navigation and self._navigation.handle_mouse_press(event):
            return
        super().mousePressEvent(event)
