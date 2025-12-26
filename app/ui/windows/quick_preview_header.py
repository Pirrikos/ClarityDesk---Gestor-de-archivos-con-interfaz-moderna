"""
Quick Preview Header - Header with action buttons.

Provides header widget with close, open PDF, and open Word buttons.
"""

import os
import platform
import subprocess
from pathlib import Path

from app.services.preview_file_extensions import normalize_extension

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class QuickPreviewHeader:
    """Manages header with action buttons for preview window."""
    
    def __init__(self):
        """Initialize header."""
        self._header_widget = None
        self._name_label = None
        self._close_btn = None
        self._open_pdf_btn = None
        self._open_word_btn = None
        self._zoom_in_btn = None
        self._zoom_out_btn = None
        self._zoom_reset_btn = None
        self._current_path = ""
        self._on_close_callback = None
        self._on_zoom_in = None
        self._on_zoom_out = None
        self._on_zoom_reset = None
    
    def create_header(self) -> QWidget:
        """Create header widget with buttons."""
        self._header_widget = QWidget()
        header_layout = QHBoxLayout(self._header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        
        self._name_label = QLabel()
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setStyleSheet("""
            QLabel {
                color: rgba(50, 50, 50, 255);
                font-family: 'Segoe UI', sans-serif;
                /* font-size: establecido explícitamente */
                font-weight: 500;
                background-color: transparent;
            }
        """)
        
        self._close_btn = self._create_button("×", self._on_close_clicked)
        self._open_pdf_btn = self._create_button("📄", self._on_open_pdf_clicked)
        self._open_word_btn = self._create_button("📝", self._on_open_word_clicked)
        self._zoom_out_btn = self._create_button("🔍−", self._on_zoom_out_clicked)
        self._zoom_in_btn = self._create_button("🔍+", self._on_zoom_in_clicked)
        self._zoom_reset_btn = self._create_button("100%", self._on_zoom_reset_clicked)
        
        header_layout.addWidget(self._open_pdf_btn)
        header_layout.addWidget(self._open_word_btn)
        header_layout.addWidget(self._zoom_out_btn)
        header_layout.addWidget(self._zoom_in_btn)
        header_layout.addWidget(self._zoom_reset_btn)
        header_layout.addWidget(self._name_label, 1)
        header_layout.addWidget(self._close_btn)
        
        self._open_pdf_btn.setVisible(False)
        self._open_word_btn.setVisible(False)
        self._zoom_out_btn.setVisible(True)
        self._zoom_in_btn.setVisible(True)
        self._zoom_reset_btn.setVisible(True)
        
        return self._header_widget
    
    def _create_button(self, text: str, callback) -> QPushButton:
        """Create styled action button."""
        btn = QPushButton(text)
        btn.setFixedSize(32, 32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(240, 240, 240, 255);
                border: 1px solid rgba(200, 200, 200, 255);
                border-radius: 4px;
                /* font-size: establecido explícitamente */
                font-weight: 500;
                color: rgba(50, 50, 50, 255);
            }
            QPushButton:hover {
                background-color: rgba(230, 230, 230, 255);
                border: 1px solid rgba(180, 180, 180, 255);
            }
            QPushButton:pressed {
                background-color: rgba(220, 220, 220, 255);
            }
        """)
        return btn
    
    def update_file(self, file_path: str, header_text: str, on_close_callback) -> None:
        """Update header with current file info."""
        self._current_path = file_path
        self._name_label.setText(header_text)
        self._on_close_callback = on_close_callback
        
        # R11: Normalize extension in single entry point
        ext = normalize_extension(file_path) if file_path else ""
        self._open_pdf_btn.setVisible(ext == ".pdf")
        self._open_word_btn.setVisible(ext == ".docx")

    def set_zoom_callbacks(self, on_zoom_in, on_zoom_out, on_zoom_reset) -> None:
        self._on_zoom_in = on_zoom_in
        self._on_zoom_out = on_zoom_out
        self._on_zoom_reset = on_zoom_reset

    def set_zoom_percent(self, percent: int) -> None:
        """Actualizar el texto del botón de zoom con el porcentaje actual."""
        if self._zoom_reset_btn:
            self._zoom_reset_btn.setText(f"{max(1, percent)}%")
    
    def _on_close_clicked(self) -> None:
        """Handle close button click."""
        if hasattr(self, '_on_close_callback'):
            self._on_close_callback()

    def _on_zoom_in_clicked(self) -> None:
        if self._on_zoom_in:
            self._on_zoom_in()

    def _on_zoom_out_clicked(self) -> None:
        if self._on_zoom_out:
            self._on_zoom_out()

    def _on_zoom_reset_clicked(self) -> None:
        if self._on_zoom_reset:
            self._on_zoom_reset()
    
    def _on_open_pdf_clicked(self) -> None:
        """Open PDF file with default application and close preview."""
        if not self._current_path:
            return
        self._open_file_and_close(self._current_path)
    
    def _on_open_word_clicked(self) -> None:
        """Open DOCX file with Word and close preview."""
        if not self._current_path:
            return
        self._open_file_and_close(self._current_path)
    
    def _open_file_and_close(self, file_path: str) -> None:
        """Close preview and open file with default application."""
        if not file_path or not os.path.exists(file_path):
            return
        
        if self._on_close_callback:
            self._on_close_callback()
        
        QTimer.singleShot(100, lambda: self._open_file(file_path))
    
    def _open_file(self, file_path: str) -> None:
        """Open file with default system application."""
        if not file_path or not os.path.exists(file_path):
            return
        
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', file_path])
            else:
                subprocess.run(['xdg-open', file_path])
        except Exception:
            pass
