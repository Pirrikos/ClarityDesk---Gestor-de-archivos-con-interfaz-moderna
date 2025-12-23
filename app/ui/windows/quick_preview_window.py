"""
QuickPreviewWindow - Immersive fullscreen overlay for file preview.

Shows a large preview image with QuickLook-style interface.
Supports navigation, PDF multi-page viewing, and animations.
"""

from typing import Optional

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QStackedLayout, QProgressBar, QApplication

from app.services.preview_pdf_service import PreviewPdfService
from app.ui.windows.quick_preview_cache import QuickPreviewCache
from app.ui.windows.quick_preview_animations import QuickPreviewAnimations
from app.ui.windows.quick_preview_thumbnails import QuickPreviewThumbnails
from app.ui.windows.quick_preview_navigation import QuickPreviewNavigation
from app.ui.windows.quick_preview_ui_setup import QuickPreviewUISetup
from app.ui.windows.quick_preview_pdf_handler import QuickPreviewPdfHandler
from app.ui.windows.quick_preview_loader import QuickPreviewLoader
from app.ui.windows.quick_preview_header import QuickPreviewHeader
from app.ui.windows.quick_preview_styles import get_loading_label_style, get_error_label_style
from pathlib import Path
from app.ui.windows.quick_preview_constants import (
    LOADING_PREVIEW,
    LOADING_DOCUMENT,
    GENERATING_THUMBNAILS,
    DOCUMENT_READY,
    NO_PREVIEW,
    BORDER_COLOR_DARK,
    OUTER_BORDER_WIDTH,
)


class QuickPreviewWindow(QWidget):
    """Immersive fullscreen overlay for quick preview."""
    
    # Border styling constants
    OUTER_BORDER_WIDTH = OUTER_BORDER_WIDTH
    BORDER_COLOR = BORDER_COLOR_DARK
    DEFAULT_PREVIEW_SIZE = QSize(800, 600)
    
    def __init__(
        self,
        preview_service: PreviewPdfService,
        file_path: str = None,
        file_paths: list[str] = None,
        start_index: int = 0,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize QuickPreviewWindow."""
        super().__init__(parent)
        self.setObjectName("QuickPreviewWindow")
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        except (AttributeError, RuntimeError):
            # Attribute may not be available in all Qt versions
            pass
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
        self._zoom = 1.0
        self._thumbs_loading = False
        
        
        self._setup_ui()
        self._loader = QuickPreviewLoader(self._cache, self._pdf_handler)
        self._setup_navigation()
        self._header.set_zoom_callbacks(self._on_zoom_in, self._on_zoom_out, self._on_zoom_reset)
        self._header.set_zoom_percent(int(self._zoom * 100))
        self._initial_load_started = False
        
        # Evitar animación de entrada que provoca un parpadeo/negro inicial
        # La UI muestra overlay de carga inmediatamente con fondo blanco
    
    def _setup_ui(self) -> None:
        """Build the UI layout."""
        max_size = QuickPreviewUISetup.setup_window(self)
        self._base_max_size = max_size
        self._cache.set_max_size(max_size)
        
        main_layout = QVBoxLayout(self)
        # Reservar espacio para el borde exterior para que no tape el contenido
        main_layout.setContentsMargins(
            self.OUTER_BORDER_WIDTH, 
            self.OUTER_BORDER_WIDTH, 
            self.OUTER_BORDER_WIDTH, 
            self.OUTER_BORDER_WIDTH
        )
        main_layout.setSpacing(0)
        
        # Borde grueso gris oscuro alrededor de toda la ventana de preview
        self.setStyleSheet(f"""
            #QuickPreviewWindow {{
                border: {self.OUTER_BORDER_WIDTH}px solid {self.BORDER_COLOR};
                background-color: #ffffff;
            }}
        """)
        
        header_widget = self._header.create_header()
        self._header_widget = header_widget  # guardar referencia para medir altura
        main_layout.addWidget(header_widget)
        
        thumbnails_panel = self._thumbnails.create_panel()
        self._thumbnails.hide()  # Ensure thumbnails are hidden initially
        self._image_label = QLabel()
        self._image_label.setText(LOADING_PREVIEW)
        self._image_label.setStyleSheet(get_loading_label_style())
        content_layout = QuickPreviewUISetup.create_content_area(
            thumbnails_panel, self._image_label
        )
        # Crear contenedor apilado para poder mostrar un overlay de carga
        stack_container = QWidget()
        self._stack = QStackedLayout(stack_container)
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        self._stack.addWidget(content_widget)
        self._loading_overlay = self._create_loading_overlay()
        self._stack.addWidget(self._loading_overlay)
        self._stack.setCurrentIndex(0)
        main_layout.addWidget(stack_container)

    def _create_loading_overlay(self) -> QWidget:
        """Overlay centrado con mensaje y barra indeterminada."""
        overlay = QWidget()
        # Fondo opaco para evitar ver un fondo negro antes de que cargue el contenido
        overlay.setStyleSheet("background-color: #ffffff;")
        layout = QVBoxLayout(overlay)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        self._loading_label = QLabel(LOADING_PREVIEW)
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        layout.addStretch(1)
        layout.addWidget(self._loading_label)
        layout.addWidget(self._progress_bar)
        layout.addStretch(1)
        return overlay

    def _show_loading(self, show: bool, text: str = LOADING_PREVIEW) -> None:
        """Mostrar/ocultar overlay de carga."""
        try:
            if show:
                if hasattr(self, '_loading_label') and self._loading_label:
                    self._loading_label.setText(text)
                self._stack.setCurrentIndex(1)
            else:
                self._stack.setCurrentIndex(0)
        except Exception:
            pass

    def _set_loading_progress(self, percent: int, text: str = None) -> None:
        """Actualizar porcentaje y texto del overlay."""
        try:
            if self._progress_bar:
                if self._progress_bar.minimum() == 0 and self._progress_bar.maximum() == 0 and percent >= 1:
                    self._progress_bar.setRange(0, 100)
                self._progress_bar.setValue(max(0, min(100, percent)))
            if text and hasattr(self, '_loading_label') and self._loading_label:
                self._loading_label.setText(text)
        except Exception:
            pass

    def _on_thumbnails_finished(self) -> None:
        """Callback cuando termina la generación de miniaturas."""
        self._thumbs_loading = False
        self._show_loading(False)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not getattr(self, '_initial_load_started', False):
            self._initial_load_started = True
            self._start_initial_load()

    def _start_initial_load(self) -> None:
        current_path = self._paths[self._index] if self._paths else ""
        self._thumbnails.hide()
        if QuickPreviewPdfHandler.is_pdf_or_docx_file(current_path):
            self._show_loading(True, LOADING_DOCUMENT)
            def on_info_finished(is_new_file: bool) -> None:
                if self._pdf_handler.total_pages > 1:
                    self._thumbnails.show()
                    self._thumbs_loading = True
                    pdf_path = self._pdf_handler.pdf_path or current_path
                    self._thumbnails.load_thumbnails_async(
                        pdf_path,
                        self._pdf_handler.total_pages,
                        self._pdf_handler.current_page,
                        self._on_thumbnail_clicked,
                        progress_cb=self._set_loading_progress,
                        finished_cb=self._on_thumbnails_finished
                    )
                max_size = self._effective_content_max_size()
                def on_page_finished(pixmap: QPixmap) -> None:
                    header_text = self._pdf_handler.get_header_text(current_path)
                    self._header.update_file(current_path, header_text, self.close)
                    self._header.set_zoom_percent(int(self._zoom * 100))
                    self._apply_pixmap(pixmap, use_crossfade=True)
                    if not self._thumbs_loading:
                        self._show_loading(False)
                def on_page_error(msg: str) -> None:
                    self._header.update_file(current_path, Path(current_path).name, self.close)
                    self._image_label.setText(NO_PREVIEW)
                    self._image_label.setStyleSheet(get_error_label_style())
                    self._show_loading(False)
                self._pdf_handler.render_page_async(
                    max_size,
                    on_finished=on_page_finished,
                    on_error=on_page_error
                )
            def on_info_error(err: str) -> None:
                self._image_label.setText("No preview available")
                self._image_label.setStyleSheet(get_error_label_style())
                self._show_loading(False)
            self._pdf_handler.load_pdf_info_async(current_path, on_info_finished, on_info_error)
        else:
            result = self._loader.load_preview(
                self._paths, self._index, self._image_label, False, self._animations
            )
            pixmap, header_text = result
            self._header.update_file(current_path, header_text, self.close)
            self._header.set_zoom_percent(int(self._zoom * 100))
            self._apply_pixmap(pixmap, use_crossfade=False)
            self._show_loading(False)

    def _apply_pixmap(self, pixmap: QPixmap, use_crossfade: bool) -> None:
        if pixmap and not pixmap.isNull():
            self._image_label.setText("")
            effective_size = self._effective_content_max_size()
            target = QSize(
                int(effective_size.width() * self._zoom),
                int(effective_size.height() * self._zoom)
            )
            scaled = pixmap.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            if use_crossfade:
                self._animations.apply_crossfade(self._image_label, scaled)
            else:
                self._image_label.setPixmap(scaled)
        else:
            self._image_label.clear()
            self._image_label.setText(NO_PREVIEW)
            self._image_label.setStyleSheet(get_error_label_style())
    
    def _setup_navigation(self) -> None:
        """Setup navigation handler."""
        self._navigation = QuickPreviewNavigation(
            self, self._paths, self._index, self._pdf_handler.is_pdf,
            self._pdf_handler.current_page, self._pdf_handler.total_pages,
            self._prev, self._next, self._prev_page, self._next_page,
            self.close
        )

    def _effective_content_max_size(self) -> QSize:
        """Calcula el área útil real para la imagen, descontando miniaturas y cabecera."""
        try:
            # Usar tamaño base estable calculado en setup
            base_size = getattr(self, '_base_max_size', None) or self.DEFAULT_PREVIEW_SIZE

            # Descontar ancho ocupado por miniaturas (panel visible)
            thumbnails_width = 0
            if hasattr(self._thumbnails, '_panel') and self._thumbnails._panel and self._thumbnails._panel.width() > 0:
                thumbnails_width = self._thumbnails._panel.width()

            # Descontar altura de la cabecera
            header_height = 0
            if hasattr(self, '_header_widget') and self._header_widget:
                header_height = self._header_widget.sizeHint().height()

            # Descontar además el borde exterior (dos lados)
            border_offset = self.OUTER_BORDER_WIDTH * 2
            min_size = QuickPreviewUISetup.IMAGE_MIN_SIZE
            effective_width = max(min_size, base_size.width() - thumbnails_width - border_offset)
            effective_height = max(min_size, base_size.height() - header_height - border_offset)
            return QSize(effective_width, effective_height)
        except (AttributeError, RuntimeError):
            return self.DEFAULT_PREVIEW_SIZE
    
    def _load_pdf_info(self, path: str) -> None:
        """Load PDF/DOCX information and setup thumbnails."""
        is_new_file = self._pdf_handler.load_pdf_info(path)
        
        if self._pdf_handler.total_pages > 1:
            self._thumbnails.show()
            if is_new_file:
                pdf_path = self._pdf_handler.pdf_path or path
                # Indicar que estamos cargando miniaturas y mostrar overlay con progreso
                self._thumbs_loading = True
                self._set_loading_progress(0, GENERATING_THUMBNAILS)
                self._show_loading(True, GENERATING_THUMBNAILS)
                self._thumbnails.load_thumbnails_async(
                    pdf_path, self._pdf_handler.total_pages, 
                    self._pdf_handler.current_page,
                    self._on_thumbnail_clicked,
                    progress_cb=self._set_loading_progress,
                    finished_cb=self._on_thumbnails_finished
                )
            else:
                self._thumbnails.update_selection(self._pdf_handler.current_page)
            # No modificar el tamaño base del cache para evitar acumulación de reducciones
        else:
            self._thumbnails.hide()
            # Mantener tamaño base del cache
    
    def _on_thumbnail_clicked(self, page_num: int) -> None:
        """Handle thumbnail click to change page."""
        if 0 <= page_num < self._pdf_handler.total_pages:
            self._pdf_handler.current_page = page_num
            self._load_preview(use_crossfade=True)
            self._thumbnails.update_selection(self._pdf_handler.current_page)
            QTimer.singleShot(50, lambda: self._thumbnails.scroll_to_thumbnail(page_num))
    
    def _load_preview(self, use_crossfade: bool = True) -> None:
        """Load and display the file preview."""
        # Renderizar usando tamaño base; el escalado final usa el tamaño efectivo
        current_path = self._paths[self._index] if self._paths else ""
        
        # Hide thumbnails initially, will show if needed
        self._thumbnails.hide()
        
        if QuickPreviewPdfHandler.is_pdf_or_docx_file(current_path):
            self._show_loading(True, LOADING_DOCUMENT)
            self._load_pdf_info(current_path)
            max_size = self._effective_content_max_size()
            def on_page_finished(pixmap: QPixmap) -> None:
                header_text = self._pdf_handler.get_header_text(current_path)
                self._header.update_file(current_path, header_text, self.close)
                self._header.set_zoom_percent(int(self._zoom * 100))
                self._apply_pixmap(pixmap, use_crossfade)
                if not self._thumbs_loading:
                    self._show_loading(False)
            def on_page_error(msg: str) -> None:
                self._header.update_file(current_path, Path(current_path).name, self.close)
                self._image_label.setText(NO_PREVIEW)
                self._image_label.setStyleSheet(get_error_label_style())
                self._show_loading(False)
            self._pdf_handler.render_page_async(
                max_size,
                on_finished=on_page_finished,
                on_error=on_page_error
            )
            return
        else:
            self._pdf_handler.reset_for_new_file()
        
        result = self._loader.load_preview(
            self._paths, self._index, self._image_label,
            use_crossfade, self._animations
        )
        
        pixmap, header_text = result
        
        self._header.update_file(current_path, header_text, self.close)
        self._header.set_zoom_percent(int(self._zoom * 100))
        
        if pixmap and not pixmap.isNull():
            self._image_label.setText("")
            effective_size = self._effective_content_max_size()
            target = QSize(
                int(effective_size.width() * self._zoom),
                int(effective_size.height() * self._zoom)
            )
            scaled = pixmap.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            if use_crossfade:
                self._animations.apply_crossfade(self._image_label, scaled)
            else:
                self._image_label.setPixmap(scaled)
            # Mantener overlay visible si seguimos generando miniaturas
            if not self._thumbs_loading:
                self._show_loading(False)
        else:
            # Limpiar cualquier pixmap previo para evitar "página en blanco" residual
            self._image_label.clear()
            if not self._image_label.text() or self._image_label.pixmap() is None or self._image_label.pixmap().isNull():
                self._image_label.setText("No preview available")
                self._image_label.setStyleSheet(get_error_label_style())
            if not self._thumbs_loading:
                self._show_loading(False)
        
        self._loader.preload_and_cleanup(self._index, self._paths)
        self._update_navigation_state()

    def _on_zoom_in(self) -> None:
        self._zoom = min(self._zoom * 1.25, 6.0)
        self._header.set_zoom_percent(int(self._zoom * 100))
        self._load_preview(use_crossfade=False)

    def _on_zoom_out(self) -> None:
        self._zoom = max(self._zoom / 1.25, 0.2)
        self._header.set_zoom_percent(int(self._zoom * 100))
        self._load_preview(use_crossfade=False)

    def _on_zoom_reset(self) -> None:
        self._zoom = 1.0
        self._header.set_zoom_percent(100)
        self._load_preview(use_crossfade=False)
    
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

    def closeEvent(self, event) -> None:
        try:
            if hasattr(self, '_preview_service') and self._preview_service:
                if hasattr(self._preview_service, 'stop_workers'):
                    self._preview_service.stop_workers()
        except Exception:
            pass
        super().closeEvent(event)
