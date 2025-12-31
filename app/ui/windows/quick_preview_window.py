"""
QuickPreviewWindow - Immersive fullscreen overlay for file preview.

Shows a large preview image with QuickLook-style interface.
Supports navigation, PDF multi-page viewing, and animations.
"""

import uuid
from typing import Optional

from PySide6.QtCore import QEvent, QObject, QSize, Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QMouseEvent, QPixmap, QKeyEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QStackedLayout, QProgressBar, QApplication

from app.services.preview_pdf_service import PreviewPdfService
from app.services.preview_file_extensions import validate_pixmap
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
from app.core.logger import get_logger

logger = get_logger(__name__)


class QuickPreviewWindow(QWidget):
    """Immersive fullscreen overlay for quick preview."""
    
    # Signal emitido cuando el preview se cierra
    closed = Signal()
    
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
        # Asegurar que la ventana pueda recibir eventos de teclado
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
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
        self._current_request_id: Optional[str] = None  # R1: Track current request
        self._is_closing = False  # Flag para indicar que se está cerrando
        self._content_rendered = False  # Flag para saber si el contenido principal ya se renderizó
        self._retry_count = 0  # Contador de reintentos para validación de max_size
        
        # Variables para arrastrar la ventana
        self._drag_position: Optional[QPoint] = None
        
        self._setup_ui()
        self._loader = QuickPreviewLoader(self._cache, self._pdf_handler)
        self._setup_navigation()
        self._header.set_zoom_callbacks(self._on_zoom_in, self._on_zoom_out, self._on_zoom_reset)
        self._header.set_zoom_percent(int(self._zoom * 100))
        self._initial_load_started = False
        
        # Instalar filtro de eventos en todos los widgets hijos para capturar espacio/escape
        from app.ui.widgets.event_filter_utils import install_event_filter_recursive
        install_event_filter_recursive(self, self)
        
        # Evitar animación de entrada que provoca un parpadeo/negro inicial
        # La UI muestra overlay de carga inmediatamente con fondo blanco
    
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Capturar espacio y escape desde cualquier widget hijo para cerrar el preview."""
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Space or key == Qt.Key.Key_Escape:
                event.accept()
                self.close()
                return True
        return False
    
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
        # Configurar el callback de cerrar desde el inicio
        self._header.set_close_callback(self.close)
        
        # Crear funciones wrapper que capturen el widget correcto
        def make_mouse_press_handler(widget):
            def handler(event):
                self._header_mouse_press(event, widget)
            return handler
        
        def make_mouse_move_handler(widget):
            def handler(event):
                self._header_mouse_move(event, widget)
            return handler
        
        def make_mouse_release_handler(widget):
            def handler(event):
                self._header_mouse_release(event, widget)
            return handler
        
        # Hacer que el header y sus hijos sean movibles para arrastrar la ventana
        header_widget.mousePressEvent = make_mouse_press_handler(header_widget)
        header_widget.mouseMoveEvent = make_mouse_move_handler(header_widget)
        header_widget.mouseReleaseEvent = make_mouse_release_handler(header_widget)
        
        # También hacer que el label del nombre sea movible
        name_label = self._header._name_label
        if name_label:
            name_label.mousePressEvent = make_mouse_press_handler(name_label)
            name_label.mouseMoveEvent = make_mouse_move_handler(name_label)
            name_label.mouseReleaseEvent = make_mouse_release_handler(name_label)
            # Permitir que el label reciba eventos de mouse
            name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
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
        if self._is_closing:
            return
        try:
            if show:
                if hasattr(self, '_loading_label') and self._loading_label:
                    self._loading_label.setText(text)
                if hasattr(self, '_stack') and self._stack:
                    self._stack.setCurrentIndex(1)
            else:
                if hasattr(self, '_stack') and self._stack:
                    self._stack.setCurrentIndex(0)
        except RuntimeError:
            pass
        except Exception:
            pass

    def _set_loading_progress(self, percent: int, text: str = None) -> None:
        """Actualizar porcentaje y texto del overlay.
        
        IMPORTANTE: No muestra el overlay si el contenido principal ya se renderizó.
        Solo actualiza el texto y la barra de progreso para thumbnails en segundo plano.
        """
        if self._is_closing:
            return
        try:
            if hasattr(self, '_progress_bar') and self._progress_bar:
                if self._progress_bar.minimum() == 0 and self._progress_bar.maximum() == 0 and percent >= 1:
                    self._progress_bar.setRange(0, 100)
                self._progress_bar.setValue(max(0, min(100, percent)))
            if text and hasattr(self, '_loading_label') and self._loading_label:
                self._loading_label.setText(text)
            # NO mostrar el overlay si el contenido principal ya se renderizó
            # Las thumbnails cargan en segundo plano sin bloquear la vista
            if not getattr(self, '_content_rendered', False):
                # Solo mostrar overlay si el contenido principal aún no se ha renderizado
                if getattr(self, '_thumbs_loading', False) and percent < 100:
                    if hasattr(self, '_stack') and self._stack:
                        self._stack.setCurrentIndex(1)
                elif percent >= 100:
                    if hasattr(self, '_stack') and self._stack:
                        self._stack.setCurrentIndex(0)
        except RuntimeError:
            pass
        except Exception as e:
            logger.warning(f"_set_loading_progress: Error: {e}", exc_info=True)

    def _safe_widget_check(self, widget_name: str = '_image_label') -> bool:
        """Verifica que widget existe y ventana no está cerrando.
        
        Returns:
            True si es seguro acceder al widget, False en caso contrario.
        """
        if self._is_closing:
            return False
        if not self._current_request_id:
            return False
        try:
            if not hasattr(self, widget_name) or not getattr(self, widget_name):
                return False
        except RuntimeError:
            return False
        return True
    
    def _on_thumbnails_finished(self) -> None:
        """Callback cuando termina la generación de miniaturas."""
        if self._is_closing:
            return
        if not self._safe_widget_check():
            return
        try:
            self._thumbs_loading = False
            self._show_loading(False)
        except RuntimeError:
            pass
        except Exception as e:
            logger.warning(f"_on_thumbnails_finished: Unexpected error: {e}", exc_info=True)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Asegurar que la ventana tenga foco para recibir eventos de teclado
        self.setFocus()
        self.activateWindow()
        self.raise_()
        if not getattr(self, '_initial_load_started', False):
            self._initial_load_started = True
            self._start_initial_load()

    def _start_initial_load(self) -> None:
        current_path = self._paths[self._index] if self._paths else ""
        self._thumbnails.hide()
        if QuickPreviewPdfHandler.is_pdf_or_docx_file(current_path):
            self._show_loading(True, LOADING_DOCUMENT)
            def on_info_finished(is_new_file: bool) -> None:
                if self._is_closing:
                    return
                
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
                
                # GUARDA OBLIGATORIA: Validar tamaño mínimo antes de renderizar
                if max_size.width() < 50 or max_size.height() < 50:
                    # Evitar renders duplicados: no reintentar si ya hay request activo
                    if self._current_request_id is not None:
                        logger.debug(f"max_size too small but request active, skipping retry")
                        return
                    
                    # Incrementar contador de reintentos
                    self._retry_count += 1
                    
                    if self._retry_count < 10:
                        logger.debug(f"max_size too small: {max_size.width()}x{max_size.height()}, retry {self._retry_count}/10")
                        QTimer.singleShot(50, lambda: self._start_initial_load())
                    else:
                        logger.warning(f"max_size validation failed after 10 retries, showing error")
                        self._show_loading(False)
                        # Mostrar error al usuario
                        if hasattr(self, '_image_label') and self._image_label:
                            self._image_label.setText("Error: Layout not ready")
                    return
                
                # Resetear contador si el tamaño es válido
                self._retry_count = 0
                
                def on_page_finished(pixmap: QPixmap) -> None:
                    if self._is_closing:
                        return
                    if not self._safe_widget_check():
                        return
                    
                    try:
                        # R14: Validate pixmap before applying
                        if not validate_pixmap(pixmap):
                            logger.warning(f"Pixmap validation failed (null: {pixmap.isNull() if pixmap else 'None'})")
                            # R4: Fallback visual
                            try:
                                if hasattr(self, '_header') and self._header:
                                    self._header.update_file(current_path, Path(current_path).name, self.close)
                                if hasattr(self, '_image_label') and self._image_label:
                                    self._image_label.setText(NO_PREVIEW)
                                    self._image_label.setStyleSheet(get_error_label_style())
                                self._show_loading(False)
                            except RuntimeError:
                                pass
                            return
                        
                        header_text = self._pdf_handler.get_header_text(current_path)
                        try:
                            self._header.update_file(current_path, header_text, self.close)
                            self._header.set_zoom_percent(int(self._zoom * 100))
                        except RuntimeError:
                            pass
                        
                        self._apply_pixmap(pixmap, use_crossfade=True)
                        # Marcar que el contenido principal ya se renderizó
                        self._content_rendered = True
                        # Ocultar loading overlay SIEMPRE cuando se muestra el contenido principal
                        # Las miniaturas pueden seguir cargando en segundo plano sin bloquear la vista
                        self._show_loading(False)
                    except RuntimeError:
                        pass
                    except Exception as e:
                        logger.error(f"Error in on_page_finished: {e}", exc_info=True)
                
                def on_page_error(msg: str) -> None:
                    if self._is_closing:
                        return
                    if not self._safe_widget_check():
                        return
                    
                    try:
                        # R4: Fallback visual
                        if hasattr(self, '_header') and self._header:
                            self._header.update_file(current_path, Path(current_path).name, self.close)
                        if hasattr(self, '_image_label') and self._image_label:
                            self._image_label.setText(NO_PREVIEW)
                            self._image_label.setStyleSheet(get_error_label_style())
                        self._show_loading(False)
                    except RuntimeError:
                        pass
                    except Exception as e:
                        logger.warning(f"Error in on_page_error: {e}", exc_info=True)
                
                try:
                    service_request_id = self._pdf_handler.render_page_async(
                        max_size,
                        on_finished=on_page_finished,
                        on_error=on_page_error
                    )
                except Exception as e:
                    logger.error(f"Error calling render_page_async: {e}", exc_info=True)
                    on_page_error(f"Error starting render: {e}")
                    service_request_id = None
                if service_request_id:
                    self._current_request_id = service_request_id
                else:
                    logger.warning("Cannot start render - previous worker still active")
                    on_page_error("Render busy, please wait")
            def on_info_error(err: str) -> None:
                # Verificar si la ventana se está cerrando
                if self._is_closing:
                    return
                
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
            self._content_rendered = True
            self._show_loading(False)

    def _apply_pixmap(self, pixmap: QPixmap, use_crossfade: bool) -> None:
        """Apply pixmap to UI with fallback visual guarantee.
        
        R4: Always shows something - never blank screen or null pixmap.
        R14: Validates pixmap before applying (not null, minimum size, coherence).
        """
        if self._is_closing:
            return
        
        try:
            if not hasattr(self, '_image_label') or not self._image_label:
                return
        except RuntimeError:
            return
        
        # R14: Validate pixmap before applying
        if validate_pixmap(pixmap):
            try:
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
                # R14: Validate scaled result
                if not validate_pixmap(scaled):
                    # R4: Fallback if scaling failed
                    logger.warning(f"Scaled pixmap invalid")
                    self._image_label.clear()
                    self._image_label.setText(NO_PREVIEW)
                    self._image_label.setStyleSheet(get_error_label_style())
                else:
                    if use_crossfade:
                        self._animations.apply_crossfade(self._image_label, scaled)
                    else:
                        self._image_label.setPixmap(scaled)
                    # Actualizar tamaño lógico del QLabel para activar scrollbars automáticamente
                    self._image_label.setFixedSize(scaled.size())
            except Exception as e:
                # R5: Encapsulate any UI errors
                logger.warning(f"Error applying pixmap: {e}", exc_info=True)
                # R4: Fallback visual
                self._image_label.clear()
                self._image_label.setText(NO_PREVIEW)
                self._image_label.setStyleSheet(get_error_label_style())
        else:
            # R4: Fallback visual - never show blank
            logger.warning(f"Invalid pixmap rejected")
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
        # Verificar si la ventana se está cerrando
        if self._is_closing:
            return
        
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
        if self._is_closing:
            return
        if 0 <= page_num < self._pdf_handler.total_pages:
            self._pdf_handler.current_page = page_num
            self._load_preview(use_crossfade=True)
            self._thumbnails.update_selection(self._pdf_handler.current_page)
            QTimer.singleShot(50, lambda: self._thumbnails.scroll_to_thumbnail(page_num))
    
    def _load_preview(self, use_crossfade: bool = True) -> None:
        """Load and display the file preview."""
        if self._is_closing:
            return
        
        current_path = self._paths[self._index] if self._paths else ""
        
        # Hide thumbnails initially, will show if needed
        self._thumbnails.hide()
        
        if QuickPreviewPdfHandler.is_pdf_or_docx_file(current_path):
            self._show_loading(True, LOADING_DOCUMENT)
            self._load_pdf_info(current_path)
            max_size = self._effective_content_max_size()
            
            # GUARDA OBLIGATORIA: Validar tamaño mínimo antes de renderizar
            if max_size.width() < 50 or max_size.height() < 50:
                # Evitar renders duplicados: no reintentar si ya hay request activo
                if self._current_request_id is not None:
                    logger.debug(f"max_size too small but request active, skipping retry")
                    return
                
                # Incrementar contador de reintentos
                self._retry_count += 1
                
                if self._retry_count < 10:
                    logger.debug(f"max_size too small: {max_size.width()}x{max_size.height()}, retry {self._retry_count}/10")
                    QTimer.singleShot(50, lambda: self._load_preview(use_crossfade=use_crossfade))
                else:
                    logger.warning(f"max_size validation failed after 10 retries, showing error")
                    self._show_loading(False)
                    # Mostrar error al usuario
                    if hasattr(self, '_image_label') and self._image_label:
                        self._image_label.setText("Error: Layout not ready")
                return
            
            # Resetear contador si el tamaño es válido
            self._retry_count = 0
            
            def on_page_finished(pixmap: QPixmap) -> None:
                if self._is_closing:
                    return
                if not self._safe_widget_check():
                    return
                
                try:
                    # R14: Validate pixmap before applying
                    if not validate_pixmap(pixmap):
                        logger.warning(f"Pixmap validation failed in _load_preview")
                        # R4: Fallback visual
                        try:
                            self._header.update_file(current_path, Path(current_path).name, self.close)
                            self._image_label.setText(NO_PREVIEW)
                            self._image_label.setStyleSheet(get_error_label_style())
                            self._show_loading(False)
                        except RuntimeError:
                            pass
                        return
                    
                    header_text = self._pdf_handler.get_header_text(current_path)
                    try:
                        self._header.update_file(current_path, header_text, self.close)
                        self._header.set_zoom_percent(int(self._zoom * 100))
                    except RuntimeError:
                        pass
                    self._apply_pixmap(pixmap, use_crossfade)
                    # Marcar que el contenido principal ya se renderizó
                    self._content_rendered = True
                    self._show_loading(False)
                except RuntimeError:
                    pass
                except Exception as e:
                    logger.error(f"Error in _load_preview on_page_finished: {e}", exc_info=True)
            
            def on_page_error(msg: str) -> None:
                if self._is_closing:
                    return
                if not self._safe_widget_check():
                    return
                
                try:
                    # R4: Fallback visual
                    if hasattr(self, '_header') and self._header:
                        self._header.update_file(current_path, Path(current_path).name, self.close)
                    if hasattr(self, '_image_label') and self._image_label:
                        self._image_label.setText(NO_PREVIEW)
                        self._image_label.setStyleSheet(get_error_label_style())
                    self._show_loading(False)
                except RuntimeError:
                    pass
                except Exception as e:
                    logger.warning(f"Error in _load_preview on_page_error: {e}", exc_info=True)
            
            service_request_id = self._pdf_handler.render_page_async(
                max_size,
                on_finished=on_page_finished,
                on_error=on_page_error
            )
            if service_request_id:
                self._current_request_id = service_request_id
            else:
                logger.warning("Cannot start render - previous worker still active")
                on_page_error("Render busy, please wait")
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
        
        # Marcar que el contenido principal ya se renderizó
        self._content_rendered = True
        
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
            # Actualizar tamaño lógico del QLabel para activar scrollbars automáticamente
            self._image_label.setFixedSize(scaled.size())
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
        if self._is_closing:
            return
        self._zoom = min(self._zoom * 1.25, 6.0)
        self._header.set_zoom_percent(int(self._zoom * 100))
        self._load_preview(use_crossfade=False)

    def _on_zoom_out(self) -> None:
        if self._is_closing:
            return
        self._zoom = max(self._zoom / 1.25, 0.2)
        self._header.set_zoom_percent(int(self._zoom * 100))
        self._load_preview(use_crossfade=False)

    def _on_zoom_reset(self) -> None:
        if self._is_closing:
            return
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
        if self._is_closing:
            return
        if self._index > 0:
            self._index -= 1
            self._pdf_handler.current_page = 0
            self._load_preview(use_crossfade=True)
    
    def _next(self) -> None:
        """Navigate to next file."""
        if self._is_closing:
            return
        if self._index < len(self._paths) - 1:
            self._index += 1
            self._pdf_handler.current_page = 0
            self._load_preview(use_crossfade=True)
    
    def _prev_page(self) -> None:
        """Navigate to previous PDF page."""
        if self._is_closing:
            return
        if self._pdf_handler.current_page > 0:
            self._pdf_handler.current_page -= 1
            self._load_preview(use_crossfade=True)
            self._thumbnails.update_selection(self._pdf_handler.current_page)
            self._thumbnails.scroll_to_thumbnail(self._pdf_handler.current_page)
    
    def _next_page(self) -> None:
        """Navigate to next PDF page."""
        if self._is_closing:
            return
        if self._pdf_handler.current_page < self._pdf_handler.total_pages - 1:
            self._pdf_handler.current_page += 1
            self._load_preview(use_crossfade=True)
            self._thumbnails.update_selection(self._pdf_handler.current_page)
            self._thumbnails.scroll_to_thumbnail(self._pdf_handler.current_page)
    
    def keyPressEvent(self, event) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Space:
            event.accept()
            self.close()
            return
        if self._navigation and self._navigation.handle_key_press(event):
            return
        super().keyPressEvent(event)
    
    def _header_mouse_press(self, event: QMouseEvent, source_widget: QWidget) -> None:
        """Handle mouse press on header for window dragging."""
        # Verificar si el clic es sobre un botón (dejar que el botón maneje el evento)
        from PySide6.QtWidgets import QPushButton
        if isinstance(source_widget, QPushButton):
            QWidget.mousePressEvent(source_widget, event)
            return
        
        # Permitir arrastrar la ventana con el botón izquierdo del ratón desde el header
        if event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            frame_top_left = self.frameGeometry().topLeft()
            self._drag_position = global_pos - frame_top_left
            event.accept()
        else:
            QWidget.mousePressEvent(source_widget, event)
    
    def _header_mouse_move(self, event: QMouseEvent, source_widget: QWidget) -> None:
        """Handle mouse move on header for window dragging."""
        if self._drag_position is not None:
            if event.buttons() == Qt.MouseButton.LeftButton:
                global_pos = event.globalPosition().toPoint()
                new_pos = global_pos - self._drag_position
                self.move(new_pos)
                event.accept()
                return
            else:
                self._drag_position = None
        
        QWidget.mouseMoveEvent(source_widget, event)
    
    def _header_mouse_release(self, event: QMouseEvent, source_widget: QWidget) -> None:
        """Handle mouse release on header."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = None
        
        QWidget.mouseReleaseEvent(source_widget, event)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        if self._navigation and self._navigation.handle_mouse_press(event):
            return
        
        super().mousePressEvent(event)

    def _cancel_all_operations(self) -> None:
        """Cancel all ongoing operations (PDF rendering, thumbnails, DOCX conversion)."""
        self._is_closing = True
        self._current_request_id = None
        if hasattr(self, '_preview_service') and self._preview_service:
            self._preview_service.stop_workers()
    
    def close(self) -> bool:
        """Close the preview window, canceling all ongoing operations."""
        self._is_closing = True
        self._current_request_id = None
        self._initial_load_started = False
        self._content_rendered = False
        self._thumbs_loading = False
        self._retry_count = 0
        self.hide()
        QTimer.singleShot(0, self._cancel_all_operations)
        # Emitir señal closed para que el padre pueda rehabilitar shortcuts
        self.closed.emit()
        result = super().close()
        self.deleteLater()
        return result
    
    def closeEvent(self, event) -> None:
        """Handle window close event, canceling all ongoing operations."""
        self._cancel_all_operations()
        self._initial_load_started = False
        self._content_rendered = False
        self._thumbs_loading = False
        self._retry_count = 0
        event.accept()
        super().closeEvent(event)
