"""
Quick Preview Navigation - Navigation logic for preview window.

Handles keyboard and mouse navigation between files and PDF pages.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent


class QuickPreviewNavigation:
    """Manages navigation logic for preview window."""
    
    def __init__(self, window, paths: list[str], current_index: int,
                 is_pdf: bool, current_page: int, total_pages: int,
                 on_prev_file, on_next_file, on_prev_page, on_next_page,
                 on_close):
        """
        Initialize navigation handler.
        
        Args:
            window: Parent window widget.
            paths: List of file paths.
            current_index: Current file index.
            is_pdf: Whether current file is PDF.
            current_page: Current PDF page (0-indexed).
            total_pages: Total PDF pages.
            on_prev_file: Callback for previous file.
            on_next_file: Callback for next file.
            on_prev_page: Callback for previous page.
            on_next_page: Callback for next page.
            on_close: Callback for closing window.
        """
        self._window = window
        self._paths = paths
        self._current_index = current_index
        self._is_pdf = is_pdf
        self._current_page = current_page
        self._total_pages = total_pages
        self._on_prev_file = on_prev_file
        self._on_next_file = on_next_file
        self._on_prev_page = on_prev_page
        self._on_next_page = on_next_page
        self._on_close = on_close
    
    def update_state(self, current_index: int, is_pdf: bool, 
                    current_page: int, total_pages: int) -> None:
        """Update navigation state."""
        self._current_index = current_index
        self._is_pdf = is_pdf
        self._current_page = current_page
        self._total_pages = total_pages
    
    def handle_key_press(self, event: QKeyEvent) -> bool:
        """
        Handle key press events.
        
        Args:
            event: Key event.
            
        Returns:
            True if event was handled, False otherwise.
        """
        key = event.key()
        
        if key == Qt.Key.Key_Escape or key == Qt.Key.Key_Space:
            event.accept()
            self._on_close()
            return True
        elif key == Qt.Key.Key_Left:
            event.accept()
            self._on_prev_file()
            return True
        elif key == Qt.Key.Key_Right:
            event.accept()
            self._on_next_file()
            return True
        elif key == Qt.Key.Key_Up:
            event.accept()
            if self._is_pdf and self._current_page > 0:
                self._on_prev_page()
            return True
        elif key == Qt.Key.Key_Down:
            event.accept()
            if self._is_pdf and self._current_page < self._total_pages - 1:
                self._on_next_page()
            return True
        
        return False
    
    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        """
        Handle mouse press events.
        
        Args:
            event: Mouse event.
            
        Returns:
            True if event was handled, False otherwise.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            width = self._window.width()
            if event.pos().x() < width / 2:
                self._on_prev_file()
            else:
                self._on_next_file()
            return True
        
        return False

