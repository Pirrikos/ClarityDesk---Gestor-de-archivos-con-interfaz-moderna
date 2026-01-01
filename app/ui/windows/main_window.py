"""
MainWindow - Main application window with Focus Dock layout.

Focus Dock replaces the old sidebar navigation system.
"""

import os
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QEvent, QPoint, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QObject, QElapsedTimer
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeySequence, QShortcut, QCursor, QMouseEvent, QPainter, QColor, QPaintEvent, QResizeEvent
from PySide6.QtWidgets import QWidget, QApplication, QToolTip, QDialog, QGraphicsOpacityEffect, QGraphicsBlurEffect

from app.core.constants import (
    DEBUG_LAYOUT, FILE_SYSTEM_DEBOUNCE_MS, CENTRAL_AREA_BG,
    CENTRAL_AREA_BG_LIGHT, RESIZE_EDGE_DETECTION_MARGIN, SIDEBAR_BG,
    USE_ROUNDED_CORNERS_IN_ROOT
)
from app.core.logger import get_logger
from app.managers.tab_manager import TabManager
from app.managers.workspace_manager import WorkspaceManager
from app.managers.search_manager import SearchManager
from app.services.desktop_path_helper import is_desktop_focus
from app.services.file_box_history_service import FileBoxHistoryService
from app.services.file_box_service import FileBoxService
from app.services.file_open_service import open_file_with_system
from app.services.icon_service import IconService
from app.managers.state_label_manager import StateLabelManager
from app.services.path_utils import normalize_path
from app.services.preview_pdf_service import PreviewPdfService
from app.ui.widgets.file_box_panel import FileBoxPanel
from app.ui.widgets.rename_state_dialog import RenameStateDialog
from app.ui.windows.desktop_window import DesktopWindow
from app.ui.windows.main_window_file_handler import filter_previewable_files
from app.ui.windows.main_window_setup import setup_ui
from app.ui.windows.main_window_state import load_app_state, save_app_state
from app.ui.windows.preview_coordination import close_other_window_preview
from app.ui.windows.quick_preview_window import QuickPreviewWindow
from app.ui.widgets.file_view_sync import get_selected_files, switch_view
from app.ui.windows.error_dialog import ErrorDialog
from app.ui.windows.confirmation_dialog import ConfirmationDialog

logger = get_logger(__name__)


class MainWindow(QWidget):
    """Main application window with Focus Dock and content area."""

    def __init__(self, tab_manager: TabManager, workspace_manager: WorkspaceManager, desktop_window: Optional[DesktopWindow] = None, parent=None):
        """Initialize MainWindow with TabManager, WorkspaceManager and optional DesktopWindow."""
        try:
            super().__init__(parent)

            self.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.FramelessWindowHint
            )

            self.setWindowTitle("ClarityDesk Pro")
            self.setMinimumSize(1050, 675)
            self.setMouseTracking(True)
            
            # ATRIBUTOS MAESTROS PARA ESTABILIDAD VISUAL
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

            # WA_OpaquePaintEvent depende del feature flag de esquinas redondeadas
            # True (sistema actual): optimización anti-flicker, pero NO esquinas redondeadas
            # False (sistema antiguo): permite transparencia para esquinas redondeadas
            if USE_ROUNDED_CORNERS_IN_ROOT:
                # Sistema antiguo: permite áreas transparentes fuera del QPainterPath
                self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
            else:
                # Sistema actual: fuerza opacidad para anti-flicker
                self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
            
            self._is_resizing = False
            self._resize_cursor_active = False

            # Asegurar que MainWindow captura eventos del mouse para detección de bordes
            # Esto es necesario para que el resize funcione correctamente en ventana frameless
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            
            self._tab_manager = tab_manager
            self._workspace_manager = workspace_manager
            self._desktop_window = desktop_window  # Inyección de dependencia
            self._icon_service = IconService()
            self._preview_service = PreviewPdfService(self._icon_service)
            self._state_label_manager = StateLabelManager()
            self._search_manager = SearchManager(workspace_manager, tab_manager)
            self._current_preview_window = None
            self._is_initializing = True
            self._transition_animation: Optional[QParallelAnimationGroup] = None
            self._fade_out_anim: Optional[QPropertyAnimation] = None
            self._fade_in_anim: Optional[QPropertyAnimation] = None
            self._resize_edge_overlay = None  # Se inicializa después de setup_ui
            # Instrumentación de ciclos de resize
            self._main_resize_in_progress: bool = False
            self._main_resize_timer: QElapsedTimer = QElapsedTimer()
            self._main_resize_paint_count: int = 0
            self._main_resize_coalesce_timer: QTimer = QTimer(self)
            self._main_resize_coalesce_timer.setSingleShot(True)
            self._main_resize_coalesce_timer.setInterval(150)
            self._main_resize_coalesce_timer.timeout.connect(self._finalize_main_resize)
            # Timer para actualización del overlay con debounce (evitar lag durante resize)
            self._overlay_update_timer: QTimer = QTimer(self)
            self._overlay_update_timer.setSingleShot(True)
            self._overlay_update_timer.setInterval(100)  # 100ms después de terminar resize
            self._overlay_update_timer.timeout.connect(self._update_overlay_geometry)

            self.setObjectName("MainWindow")
            self.setAutoFillBackground(False)
            
            # Inicializar color del área central desde AppSettings (solo para FileViewContainer)
            from app.managers import app_settings as app_settings_module
            if app_settings_module.app_settings is not None:
                color_theme = app_settings_module.app_settings.central_area_color
                self._central_area_color = CENTRAL_AREA_BG_LIGHT if color_theme == "light" else CENTRAL_AREA_BG
            else:
                self._central_area_color = CENTRAL_AREA_BG

            # Nota: La pintura del fondo se delega al BackgroundContainer interno

            self._tab_manager.set_workspace_manager(workspace_manager)
            self._setup_ui()
            self._setup_antiflicker_attributes()
            self._setup_resize_overlay()
            self._connect_signals()
            self._setup_shortcuts()
            self._load_workspace_state()
            self._is_initializing = False

            # TEMPORAL: Ocultar headers para diagnóstico de parpadeo
            # self._hide_headers_for_diagnosis()  # DESHABILITADO PARA PROBAR SOLUCIÓN
            
        except Exception as e:
            logger.error(f"Excepción crítica en MainWindow.__init__: {e}", exc_info=True)
            raise

    def resizeEvent(self, event):
        """Manejar resize con repintado fluido estilo aplicaciones profesionales."""
        # Inicio del ciclo de resize (coalesce)
        if not self._main_resize_in_progress:
            try:
                self._main_resize_timer.start()
                self._main_resize_paint_count = 0
            except Exception:
                pass
            self._main_resize_in_progress = True

        # Reiniciar coalesce
        self._main_resize_coalesce_timer.stop()
        self._main_resize_coalesce_timer.start()
        super().resizeEvent(event)

        # Programar actualización del overlay con debounce (evita lag durante resize)
        if hasattr(self, '_overlay_update_timer') and self._overlay_update_timer:
            self._overlay_update_timer.start()  # Reinicia el timer en cada resize


    def _finalize_main_resize(self) -> None:
        """Finalizar coalesce de resize y registrar métricas."""
        if self._main_resize_in_progress:
            try:
                elapsed_ms = self._main_resize_timer.elapsed() if self._main_resize_timer.isValid() else 0
                if DEBUG_LAYOUT:
                    logger.info(f"✅ Fin resize main | duración={elapsed_ms}ms, paints={self._main_resize_paint_count}")
            except Exception:
                pass
            self._main_resize_in_progress = False

    def _update_overlay_geometry(self) -> None:
        """Actualizar geometría del overlay solo cuando resize ha terminado (debounce)."""
        if hasattr(self, '_resize_edge_overlay') and self._resize_edge_overlay:
            self._resize_edge_overlay.setGeometry(self.rect())
            self._resize_edge_overlay.raise_()

    def _setup_ui(self) -> None:
        """Build the UI layout with Focus Dock integrated."""
        self._file_view_container, self._sidebar, self._window_header, self._app_header, self._secondary_header, self._workspace_selector, self._history_panel, self._content_splitter, self._current_file_box_panel = setup_ui(
            self, self._tab_manager, self._icon_service, self._workspace_manager, self._state_label_manager
        )
        self._file_box_panel_minimized = False

        # Obtener footer desde FileViewContainer
        self._path_footer = getattr(self._file_view_container, '_path_footer', None)

        if self._current_file_box_panel:
            self._current_file_box_panel.close_requested.connect(self._close_file_box_panel)
            self._current_file_box_panel.minimize_requested.connect(self._minimize_file_box_panel)
            self._current_file_box_panel.file_open_requested.connect(self._on_file_open)

        if self._history_panel:
            self._history_panel.close_requested.connect(self._close_history_panel_only)

    def _setup_antiflicker_attributes(self) -> None:
        """
        Configurar atributos de Qt para resize fluido sin parpadeo.

        Ahora que sizeHint() está correctamente implementado en el delegate,
        estas optimizaciones deberían funcionar sin problemas de pintado.
        """
        widgets_to_fix = []

        if hasattr(self, '_app_header') and self._app_header:
            widgets_to_fix.append(self._app_header)
        if hasattr(self, '_secondary_header') and self._secondary_header:
            widgets_to_fix.append(self._secondary_header)
        if hasattr(self, '_workspace_selector') and self._workspace_selector:
            widgets_to_fix.append(self._workspace_selector)
        if hasattr(self, '_sidebar') and self._sidebar:
            widgets_to_fix.append(self._sidebar)
        if hasattr(self, '_path_footer') and self._path_footer:
            widgets_to_fix.append(self._path_footer)

        # Aplicar atributos de optimización solo a headers/sidebar/footer
        for widget in widgets_to_fix:
            widget.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
            widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
            widget.setAutoFillBackground(False)

        # Optimizaciones para la ventana principal
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

    def _setup_resize_overlay(self) -> None:
        """
        Crear overlay invisible para captura de eventos en los bordes.

        Este overlay se superpone a toda la ventana pero solo captura eventos
        en los bordes (definidos por RESIZE_EDGE_DETECTION_MARGIN). El resto
        es transparente para eventos, permitiendo interacción normal con widgets.
        """
        from app.ui.widgets.resize_edge_overlay import ResizeEdgeOverlay

        self._resize_edge_overlay = ResizeEdgeOverlay(self)
        # Posicionar el overlay para que cubra toda la ventana
        self._resize_edge_overlay.setGeometry(self.rect())
        # Elevar el overlay por encima de todos los widgets
        self._resize_edge_overlay.raise_()
        self._resize_edge_overlay.show()

    def _connect_signals(self) -> None:
        """Connect UI signals to TabManager."""
        self._window_header.request_close.connect(self.close)
        self._window_header.request_minimize.connect(self.showMinimized)
        self._window_header.request_toggle_maximize.connect(self._toggle_maximize)
        
        # Conectar señal del AppHeader para mostrar dock de escritorio
        self._app_header.show_desktop_requested.connect(self._on_show_desktop_requested)
        
        # Conectar señal del AppHeader para mostrar ventana de ajustes
        self._app_header.show_settings_requested.connect(self._on_show_settings_requested)
        
        # Conectar señal de cambio de color del área central
        from app.managers import app_settings as app_settings_module
        if app_settings_module.app_settings is not None:
            app_settings_module.app_settings.central_area_color_changed.connect(self._on_central_area_color_changed)
        
        self._tab_manager_connections = [
            (self._tab_manager.tabsChanged, self._on_tabs_changed),
            (self._tab_manager.tabsChanged, self._on_tabs_changed_sync_sidebar),
            (self._tab_manager.activeTabChanged, self._on_active_tab_changed),
            (self._tab_manager.activeTabChanged, self._on_active_tab_changed_update_nav),
            (self._tab_manager.activeTabChanged, self._on_active_tab_changed_update_app_header),
        ]
        
        for signal, slot in self._tab_manager_connections:
            signal.connect(slot)
        
        self._file_view_container.open_file.connect(self._on_file_open)
        self._file_view_container.folder_moved.connect(self._on_folder_moved)
        
        self._workspace_selector.new_focus_requested.connect(self._on_sidebar_new_focus)
        self._sidebar.folder_selected.connect(self._on_sidebar_folder_selected)
        self._sidebar.focus_remove_requested.connect(self._on_sidebar_remove_focus)
        self._sidebar.state_selected.connect(self._on_state_selected)
        
        watcher = self._tab_manager.get_watcher()
        if watcher:
            watcher.folder_renamed.connect(self._sidebar.update_focus_path)
            watcher.folder_renamed.connect(self._on_watcher_folder_renamed_update_tabs)
            watcher.folder_disappeared.connect(self._on_folder_disappeared)
            watcher.structural_change_detected.connect(self._on_structural_change_detected)
            
            # Nuevas conexiones para actualización granular
            watcher.folder_created.connect(self._on_folder_created)
            watcher.folder_deleted.connect(self._on_folder_deleted)
        
        self._workspace_selector.workspace_selected.connect(self._on_workspace_selected)
        self._workspace_manager.workspace_changed.connect(self._on_workspace_changed)
        self._workspace_manager.view_mode_changed.connect(self._on_view_mode_changed)
        
        # File box signals
        self._workspace_selector.file_box_requested.connect(self._on_file_box_button_clicked)
        self._workspace_selector.state_button_clicked.connect(self._file_view_container._on_state_button_clicked)
        self._workspace_selector.rename_state_requested.connect(self._on_rename_state_requested)
        self._secondary_header.history_panel_toggle_requested.connect(self._on_history_panel_toggle)
        
        self._workspace_selector.rename_clicked.connect(self._file_view_container._on_rename_clicked)

        # Connect window size change to column adjustment (ONLY on button clicks, not drag resize)
        self._app_header.window_size_changed.connect(self._on_window_size_changed)

        # Set state label manager
        self._workspace_selector.set_state_label_manager(self._state_label_manager)
        self._state_label_manager.labels_changed.connect(self._on_state_labels_changed)
        
        # Set label callback for file views
        if hasattr(self, '_file_view_container') and self._file_view_container:
            callback = self._get_label_callback()
            self._file_view_container._get_label_callback = callback
            # Conectar señal de cambio de label específico para refrescar vistas
            self._file_view_container.set_state_label_manager(self._state_label_manager)
            # Update existing widgets
            self._update_widgets_label_callback()
        
        # Set tab_manager and sidebar for workspace deletion operations
        self._workspace_selector.set_tab_manager(self._tab_manager)
        self._workspace_selector.set_sidebar(self._sidebar)
        self._workspace_selector.set_signal_controller(self)
        
        # Conectar señales de búsqueda
        self._secondary_header.search_changed.connect(self._search_manager.search)
        self._search_manager.search_mode_changed.connect(self._on_search_mode_changed)
        self._search_manager.search_results_changed.connect(self._on_search_results_changed)
        
        # Inyectar WorkspaceManager a FileViewContainer para resolver workspace_name
        self._file_view_container.set_workspace_manager(self._workspace_manager)
        
        # Setup footer update timer
        self._setup_footer_timer()

    def _cancel_search_if_active(self) -> None:
        """Cancelar búsqueda si está activa antes de navegar."""
        if self._search_manager and self._search_manager.is_search_mode():
            # Marcar que estamos navegando para que set_search_mode no recargue archivos
            # La navegación normal se encargará de recargar los archivos
            self._file_view_container._is_navigating = True
            # Limpiar texto del campo de búsqueda PRIMERO (sin disparar señales)
            if self._secondary_header:
                self._secondary_header.clear_search_text()
            # Luego cancelar la búsqueda (esto ya no disparará búsqueda porque el texto está vacío)
            self._search_manager.clear_search()
            # Procesar eventos para asegurar que las señales se procesen antes de continuar
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            # Resetear flag después de que la navegación haya procesado las señales
            from PySide6.QtCore import QTimer
            QTimer.singleShot(200, lambda: setattr(self._file_view_container, '_is_navigating', False))

    def _setup_footer_timer(self) -> None:
        """Setup timer to periodically update footer with selected file path."""
        from app.core.constants import SELECTION_UPDATE_INTERVAL_MS
        self._footer_timer = QTimer(self)
        self._footer_timer.timeout.connect(self._update_footer_path)
        self._last_selected_path = ""
        self._footer_timer.start(SELECTION_UPDATE_INTERVAL_MS)
    
    def _update_footer_path(self) -> None:
        """Update footer with path of selected file (first selected if multiple)."""
        if not self._path_footer:
            return  # Footer no disponible (desktop mode)
        
        selected_files = get_selected_files(self._file_view_container)
        if selected_files:
            current_path = selected_files[0]
            if current_path != self._last_selected_path:
                self._last_selected_path = current_path
                self._path_footer.set_text(current_path)
        else:
            if self._last_selected_path:
                self._last_selected_path = ""
                self._path_footer.set_text("")

    def _on_show_settings_requested(self) -> None:
        """Abrir ventana de ajustes cuando se hace clic en el icono de ajustes."""
        from app.ui.windows.settings_window import get_settings_window
        # Usar la misma función que SettingsStackTile para consistencia
        get_settings_window()
    
    def _on_central_area_color_changed(self, color_theme: str) -> None:
        """Actualizar color del área central cuando cambia el tema."""
        # El MainWindow no cambia de color, solo el FileViewContainer
        # FileViewContainer se actualiza automáticamente mediante su señal conectada
        pass
    
    def _on_show_desktop_requested(self) -> None:
        """Ocultar MainWindow y mostrar DesktopWindow sin animaciones."""
        # Usar DesktopWindow inyectado o buscar como fallback
        desktop_window = self._desktop_window
        if not desktop_window:
            # Fallback: buscar DesktopWindow si no fue inyectado
            for widget in QApplication.allWidgets():
                if isinstance(widget, DesktopWindow):
                    desktop_window = widget
                    break
        
        if not desktop_window:
            logger.warning("DesktopWindow no encontrada al intentar mostrar dock de escritorio")
            return
        
        # Cancelar cualquier animación/effecto anterior
        if self._transition_animation:
            try:
                self._transition_animation.stop()
                self._transition_animation.deleteLater()
            except Exception:
                pass
            self._transition_animation = None
        try:
            self.setGraphicsEffect(None)
            desktop_window.setGraphicsEffect(None)
        except Exception:
            pass

        # Mostrar DesktopWindow inmediatamente
        if not desktop_window.isVisible():
            desktop_window.show()
        desktop_window.raise_()
        desktop_window.activateWindow()
        # Ocultar MainWindow sin animación
        self.hide()

    def _load_app_state(self) -> None:
        """Load complete application state and restore UI."""
        if not self._workspace_manager:
            load_app_state(self, self._tab_manager)
    
    def _load_workspace_state(self) -> None:
        """
        Load workspace state and restore UI.
        
        REGLA OBLIGATORIA: El contexto de estado solo puede existir cuando el origen activo es un estado.
        Cambiar de workspace es un cambio de origen → debe limpiar siempre el contexto de estado.
        """
        if not self._workspace_manager:
            self._load_app_state()
            return
        
        # REGLA OBLIGATORIA: Limpiar contexto de estado antes de cargar workspace
        if hasattr(self._tab_manager, '_current_state_context') and self._tab_manager._current_state_context:
            self._tab_manager.clear_state_context()
            # Restaurar modo del workspace al volver a carpeta normal
            if self._workspace_manager:
                workspace_mode = self._workspace_manager.get_view_mode()
                self._tab_manager._current_view_mode = workspace_mode
                if hasattr(self._tab_manager, 'view_mode_changed'):
                    self._tab_manager.view_mode_changed.emit(workspace_mode)
        
        active_workspace = self._workspace_manager.get_active_workspace()
        if not active_workspace:
            return
        
        state = self._workspace_manager.get_workspace_state(active_workspace.id)
        
        if state:
            self._tab_manager.load_workspace_state({
                'tabs': state.get('tabs', []),
                'active_tab': state.get('active_tab')
            })
            
            self._sidebar.load_workspace_state(
                state.get('focus_tree_paths', []),
                state.get('expanded_nodes', []),
                state.get('root_folders_order')
            )
            
            view_mode = state.get('view_mode', 'grid')
            switch_view(self._file_view_container, view_mode)
        else:
            self._tab_manager.load_workspace_state({
                'tabs': [],
                'active_tab': None
            })
            self._sidebar.load_workspace_state([], [])
    
    def _on_workspace_selected(self, workspace_id: str) -> None:
        """Handle workspace selection - delegar a WorkspaceManager."""
        # Cancelar búsqueda si está activa antes de cambiar workspace
        self._cancel_search_if_active()
        
        if self._workspace_manager:
            self._workspace_manager.switch_workspace(
                workspace_id,
                self._tab_manager,
                self._sidebar,
                signal_controller=self
            )
    
    def disconnect_signals(self) -> None:
        """Temporarily disconnect TabManager signals during workspace switch."""
        for signal, slot in self._tab_manager_connections:
            signal.disconnect(slot)
    
    def reconnect_signals(self) -> None:
        """Reconnect TabManager signals after workspace switch."""
        for signal, slot in self._tab_manager_connections:
            signal.connect(slot)
    
    def clear_file_view(self) -> None:
        """Explicitly clear file view when workspace has no active tab."""
        self._file_view_container.clear_current_focus()
    
    def _on_view_mode_changed(self, view_mode: str) -> None:
        """Handle view mode change from WorkspaceManager - aplicar cambio visual."""
        switch_view(self._file_view_container, view_mode)

    def _on_window_size_changed(self) -> None:
        """Handle window size change from header buttons - adjust list view columns."""
        if not hasattr(self, '_file_view_container') or not self._file_view_container:
            return

        # Solo ajustar columnas de la vista de lista si está activa
        if hasattr(self._file_view_container, '_list_view') and self._file_view_container._list_view:
            list_view = self._file_view_container._list_view
            if hasattr(list_view, '_adjust_columns_to_viewport_width'):
                list_view._adjust_columns_to_viewport_width()

    def _on_workspace_changed(self, workspace_id: str) -> None:
        """Handle workspace change - actualizar UI con nuevo estado."""
        if not self._workspace_manager:
            return
        
        workspace = self._workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return
        
        view_mode = self._workspace_manager.get_view_mode()
        switch_view(self._file_view_container, view_mode)

    def _on_tabs_changed(self, tabs: list) -> None:
        """Handle tabs list change from TabManager."""
        if self._is_initializing:
            return
        self._schedule_sidebar_sync()

    def _on_active_tab_changed(self, index: int, path: str) -> None:
        """Handle active tab change from TabManager."""
        pass
    
    def _on_active_tab_changed_update_app_header(self, index: int, path: str) -> None:
        """Update AppHeader when active tab changes."""
        if self._is_initializing:
            return
        # Placeholder: AppHeader ya no muestra información de workspace/tab
    
    def _toggle_maximize(self) -> None:
        """Toggle window maximize/restore state."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def _on_active_tab_changed_update_nav(self, index: int, path: str) -> None:
        """Update navigation buttons state when active tab changes."""
        if self._is_initializing:
            return
        self._file_view_container._update_nav_buttons_state()
    
    def _on_nav_back_shortcut(self) -> None:
        """Handle Alt+Left keyboard shortcut for back navigation."""
        if self._tab_manager.can_go_back():
            self._tab_manager.go_back()
    
    def _on_nav_forward_shortcut(self) -> None:
        """Handle Alt+Right keyboard shortcut for forward navigation."""
        if self._tab_manager.can_go_forward():
            self._tab_manager.go_forward()
    
    def _on_files_moved(self, source_path: str, target_path: str) -> None:
        """Handle files moved - refresh affected Focus."""
        source_dir = os.path.dirname(source_path)
        active_folder = self._tab_manager.get_active_folder()
        
        if source_dir == active_folder:
            QTimer.singleShot(100, lambda: self._file_view_container._update_files())
        
        if target_path == active_folder:
            QTimer.singleShot(100, lambda: self._file_view_container._update_files())
    
    def _on_folder_moved(self, old_path: str, new_path: str) -> None:
        """Handle folder moved from file view area - update sidebar."""
        if old_path and new_path:
            self._sidebar.update_focus_path(old_path, new_path)
    
    def _on_folder_disappeared(self, folder_path: str) -> None:
        """Handle folder disappeared (moved outside watched directory) - resync sidebar."""
        if not folder_path:
            return
        
        normalized_path = normalize_path(folder_path)
        
        if normalized_path not in self._sidebar._path_to_item:
            return
        
        tabs = self._tab_manager.get_tabs()
        normalized_tabs = {normalize_path(tab) for tab in tabs}
        
        if normalized_path in normalized_tabs:
            self._schedule_sidebar_sync(structural=True)
        else:
            self._sidebar.remove_focus_path(normalized_path)
    
    def _get_folder_children(self, folder_path: str) -> set[str]:
        """
        Obtener lista de hijos (carpetas) de una carpeta.
        
        Returns:
            Set de paths normalizados de carpetas hijas.
        """
        children = set()
        try:
            if os.path.isdir(folder_path):
                for item_name in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item_name)
                    if os.path.isdir(item_path):
                        children.add(normalize_path(item_path))
        except (OSError, PermissionError):
            pass
        return children
    
    def _on_structural_change_detected(self, watched_folder: str) -> None:
        """
        Actualizar solo la carpeta afectada en el sidebar.
        
        Si la carpeta está en el sidebar, sincroniza solo sus hijos.
        """
        normalized_watched = normalize_path(watched_folder)
        
        if self._sidebar.has_path(normalized_watched):
            # Obtener hijos reales del filesystem (una sola vez)
            real_children = self._get_folder_children(normalized_watched)
            
            # Pedir al sidebar que sincronice solo este nodo
            self._sidebar.sync_children(normalized_watched, real_children)
    
    def _on_folder_created(self, folder_path: str) -> None:
        """
        Manejar creación de carpeta: agregar al sidebar si su padre existe.
        """
        normalized_path = normalize_path(folder_path)
        parent_path = os.path.dirname(normalized_path)
        normalized_parent = normalize_path(parent_path)
        
        # Solo agregar si el padre existe en el sidebar
        if self._sidebar.has_path(normalized_parent):
            # Verificar que la carpeta realmente existe
            if os.path.exists(normalized_path) and os.path.isdir(normalized_path):
                # Obtener hijos reales del padre para sincronización completa
                real_children = self._get_folder_children(normalized_parent)
                self._sidebar.sync_children(normalized_parent, real_children)
    
    def _on_folder_deleted(self, folder_path: str) -> None:
        """
        Manejar eliminación de carpeta: eliminar del sidebar si existe.
        """
        normalized_path = normalize_path(folder_path)
        
        if self._sidebar.has_path(normalized_path):
            self._sidebar.remove_path(normalized_path)
    
    def _on_watcher_folder_renamed_update_tabs(self, old_path: str, new_path: str) -> None:
        """
        Actualizar la lista de tabs cuando el watcher detecta rename de carpeta.
        
        Si el tab existe con old_path, reemplazarlo por new_path y emitir tabsChanged.
        Si el tab activo fue renombrado, reiniciar observación sobre el nuevo path.
        """
        try:
            if not hasattr(self._tab_manager, 'get_tabs'):
                return
            tabs = self._tab_manager.get_tabs()
            if not tabs:
                return
            
            from app.services.path_utils import normalize_path
            normalized_old = normalize_path(old_path)
            normalized_new = normalize_path(new_path)
            
            # Encontrar índice del tab correspondiente al antiguo path
            idx = None
            for i, t in enumerate(tabs):
                if normalize_path(t) == normalized_old:
                    idx = i
                    break
            if idx is None:
                return
            
            # Reemplazar por el nuevo path preservando posición
            tabs[idx] = new_path
            # Asignar directamente y emitir señal de cambio para que UI se sincronice
            self._tab_manager._tabs = tabs
            self._tab_manager.tabsChanged.emit(tabs.copy())
            
            # Si el tab activo fue renombrado, reiniciar watcher y activeTabChanged
            if hasattr(self._tab_manager, '_active_index') and self._tab_manager._active_index == idx:
                if hasattr(self._tab_manager, '_watch_and_emit_internal'):
                    self._tab_manager._watch_and_emit_internal(new_path)
        except Exception:
            pass
    
    def _schedule_sidebar_sync(self, structural: bool = False) -> None:
        if not hasattr(self, '_sidebar_sync_timer'):
            self._sidebar_sync_timer = QTimer(self)
            self._sidebar_sync_timer.setSingleShot(True)
            self._sidebar_sync_timer.timeout.connect(self._resync_sidebar_from_tabs)
        
        self._pending_structural_sync = structural
        
        self._sidebar_sync_timer.stop()
        self._sidebar_sync_timer.start(FILE_SYSTEM_DEBOUNCE_MS)
    
    def mousePressEvent(self, event) -> None:
        """Iniciar resize nativo desde cualquier borde o esquina."""
        if event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPos()
            edges = self._detect_resize_edges(global_pos)

            if edges and self.windowHandle():
                # Solo iniciar resize si estamos en los bordes de la ventana
                # Esto evita interferir con drag and drop de archivos
                self._is_resizing = True
                self.windowHandle().startSystemResize(edges)
                event.accept()
                return

        # Si no estamos redimensionando, permitir que el evento se propague
        # para que el drag and drop funcione correctamente
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """Restaurar cursor cuando se suelta el botón del ratón."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Limpiar estado de redimensionamiento
            self._is_resizing = False
            self._clear_resize_cursor()
            # Actualizar cursor inmediatamente después de soltar para reflejar posición actual
            if not self.isMaximized():
                self._update_resize_cursor()

        super().mouseReleaseEvent(event)

    def showEvent(self, event) -> None:
        """Instalar filtro de eventos global cuando la ventana se muestra."""
        super().showEvent(event)
        QApplication.instance().installEventFilter(self)
        # Asegurar que el overlay esté por encima después de mostrar
        if self._resize_edge_overlay:
            self._resize_edge_overlay.raise_()

    def hideEvent(self, event) -> None:
        """Desinstalar filtro de eventos global cuando la ventana se oculta."""
        QApplication.instance().removeEventFilter(self)
        self._clear_resize_cursor()
        super().hideEvent(event)

    def leaveEvent(self, event) -> None:
        """Restaurar cursor cuando el ratón sale de la ventana."""
        self._clear_resize_cursor()
        super().leaveEvent(event)
    
    def _update_resize_cursor(self) -> None:
        """Actualizar cursor según si el mouse está cerca de los bordes."""
        # Solo actualizar cursor si esta ventana está activa
        if not self.isActiveWindow():
            self._clear_resize_cursor()
            return

        global_pos = QCursor.pos()
        edges = self._detect_resize_edges(global_pos)

        if edges:
            cursor = self._get_resize_cursor(edges)
            if cursor:
                if not self._resize_cursor_active:
                    QApplication.setOverrideCursor(cursor)
                    self._resize_cursor_active = True
                else:
                    QApplication.changeOverrideCursor(cursor)
        else:
            self._clear_resize_cursor()
    
    def _clear_resize_cursor(self) -> None:
        """Limpiar cursor de redimensionamiento si está activo."""
        if self._resize_cursor_active:
            QApplication.restoreOverrideCursor()
            self._resize_cursor_active = False
    
    def _detect_resize_edges(self, global_pos: QPoint) -> Qt.Edges:
        """Detectar bordes de ventana para resize nativo."""
        if not self.windowHandle():
            return Qt.Edges()

        geo = self.frameGeometry()
        margin = RESIZE_EDGE_DETECTION_MARGIN

        # Verificar que el cursor está dentro de la geometría de la ventana (con tolerancia extendida)
        # Permitir un área ligeramente más amplia para capturar bordes externos
        extended_geo = geo.adjusted(-2, -2, 2, 2)
        if not extended_geo.contains(global_pos):
            return Qt.Edges()

        edges = Qt.Edges()

        # Calcular distancias desde los bordes EXTERIORES de la ventana
        # Esto es crítico para que la detección funcione con el margen de layout
        x = global_pos.x()
        y = global_pos.y()

        left_dist = x - geo.left()
        right_dist = geo.right() - x
        top_dist = y - geo.top()
        bottom_dist = geo.bottom() - y

        # Detectar bordes usando distancias positivas hacia el interior
        # Esto permite capturar tanto el borde exacto como el área cercana
        if 0 <= left_dist <= margin:
            edges |= Qt.Edge.LeftEdge
        if 0 <= right_dist <= margin:
            edges |= Qt.Edge.RightEdge
        if 0 <= top_dist <= margin:
            edges |= Qt.Edge.TopEdge
        if 0 <= bottom_dist <= margin:
            edges |= Qt.Edge.BottomEdge

        return edges
    
    def _get_resize_cursor(self, edges: Qt.Edges):
        """Obtener cursor según bordes detectados."""
        if not edges:
            return None
        
        if (edges & Qt.Edge.TopEdge) and (edges & Qt.Edge.LeftEdge):
            return QCursor(Qt.CursorShape.SizeFDiagCursor)
        if (edges & Qt.Edge.TopEdge) and (edges & Qt.Edge.RightEdge):
            return QCursor(Qt.CursorShape.SizeBDiagCursor)
        if (edges & Qt.Edge.BottomEdge) and (edges & Qt.Edge.LeftEdge):
            return QCursor(Qt.CursorShape.SizeBDiagCursor)
        if (edges & Qt.Edge.BottomEdge) and (edges & Qt.Edge.RightEdge):
            return QCursor(Qt.CursorShape.SizeFDiagCursor)
        
        if edges & Qt.Edge.LeftEdge or edges & Qt.Edge.RightEdge:
            return QCursor(Qt.CursorShape.SizeHorCursor)
        if edges & Qt.Edge.TopEdge or edges & Qt.Edge.BottomEdge:
            return QCursor(Qt.CursorShape.SizeVerCursor)
        
        return None
    
    def _resync_sidebar_from_tabs(self) -> None:
        """
        Asegurar que todos los tabs raíz existen en el sidebar.
        
        Método idempotente e incremental: solo añade tabs que faltan,
        no borra ni reconstruye nada.
        """
        tabs = self._tab_manager.get_tabs()
        
        # Solo añadir tabs raíz que no existen en el sidebar
        for tab_path in tabs:
            normalized_tab = normalize_path(tab_path)
            if normalized_tab not in self._sidebar._path_to_item:
                if os.path.exists(tab_path) and os.path.isdir(tab_path):
                    self._sidebar.add_focus_path(tab_path)

    def _on_file_open(self, file_path: str) -> None:
        """Handle file open request from file box panel or other sources.
        
        El doble clic siempre abre el archivo normalmente con el sistema,
        no hace preview. El preview solo se abre con la barra espaciadora.
        """
        if os.path.isdir(file_path):
            self._navigate_to_folder(file_path)
            return
        
        # Siempre abrir con el sistema (doble clic no hace preview)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        QTimer.singleShot(180, QApplication.restoreOverrideCursor)
        success = open_file_with_system(file_path)
        if not success:
            error_dialog = ErrorDialog(
                parent=self,
                title="No se puede abrir",
                message="No hay aplicación asociada o el archivo no es reconocible.\n"
                        "Intenta abrirlo manualmente desde el sistema.",
                is_warning=True
            )
            error_dialog.exec()

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        self._back_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        self._back_shortcut.activated.connect(self._on_nav_back_shortcut)
        
        self._forward_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        self._forward_shortcut.activated.connect(self._on_nav_forward_shortcut)
        
        # Instalar filtro de eventos en toda la ventana para capturar espacio
        from app.ui.widgets.event_filter_utils import install_event_filter_recursive
        install_event_filter_recursive(self, self)
    
    def eventFilter(self, watched: QObject, event) -> bool:
        """Filtrar eventos globales: cursor de bordes y barra espaciadora."""
        # Cursor de bordes: actualizar en cada movimiento de mouse
        if event.type() == QEvent.Type.MouseMove:
            # Solo actualizar cursor si NO estamos redimensionando y la ventana NO está maximizada
            # Esto evita interferir con el drag and drop de archivos
            if not self._is_resizing and not self.isMaximized():
                mouse_event = event
                # Verificar que no hay botones presionados (no hay drag en curso)
                if mouse_event.buttons() == Qt.MouseButton.NoButton:
                    self._update_resize_cursor()
                else:
                    # Si hay botones presionados, limpiar cursor de resize para no interferir con drag
                    self._clear_resize_cursor()

        if event.type() == QEvent.Type.KeyPress:
            key_event = event
            key = key_event.key()
            
            if key == Qt.Key.Key_Space and not key_event.modifiers():
                # Solo procesar si MainWindow está visible y es la ventana activa
                if not self.isVisible():
                    return False
                
                # Verificar que el foco está en MainWindow o sus hijos
                focus_widget = QApplication.focusWidget()
                if focus_widget:
                    # Verificar si el widget con foco pertenece a MainWindow
                    if not self.isAncestorOf(focus_widget) and focus_widget != self:
                        return False
                    
                    focus_class = focus_widget.__class__.__name__
                    if focus_class in ('QLineEdit', 'QTextEdit', 'QPlainTextEdit', 'SearchLineEdit'):
                        return False
                
                self._open_quick_preview()
                return True
        
        return False

    def _open_quick_preview(self) -> None:
        """Toggle quick preview window (open/close)."""
        # Verificar si hay un preview existente
        try:
            if self._current_preview_window and self._current_preview_window.isVisible():
                self._current_preview_window.close()
                self._current_preview_window = None
                return
        except RuntimeError:
            self._current_preview_window = None

        # Limpiar referencia si existe pero no está visible
        if self._current_preview_window:
            self._current_preview_window = None

        selected = []
        if self._current_file_box_panel and self._current_file_box_panel.isVisible():
            selected = self._current_file_box_panel.get_selected_files()
        
        if not selected:
            selected = get_selected_files(self._file_view_container)
        
        if not selected:
            return

        allowed_files = filter_previewable_files(selected)
        if not allowed_files:
            return

        # Cerrar cualquier preview abierto en DesktopWindow para evitar conflictos
        close_other_window_preview(self, DesktopWindow, self._desktop_window)

        preview_window = QuickPreviewWindow(
            self._preview_service,
            file_paths=allowed_files,
            start_index=0,
            parent=self
        )

        self._current_preview_window = preview_window
        # Conectar señal closed para limpiar referencia cuando se cierra
        preview_window.closed.connect(self._on_preview_closed)
        preview_window.show()
        preview_window.setFocus()
    
    def _on_preview_closed(self) -> None:
        """Limpiar referencia cuando preview se cierra."""
        self._current_preview_window = None
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter - let FileViewContainer handle it."""
        super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move - let FileViewContainer handle it."""
        super().dragMoveEvent(event)
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop - let FileViewContainer handle it, or ignore if DesktopWindow should handle."""
        desktop_window_under_cursor = None
        cursor_pos = event.pos()
        global_pos = self.mapToGlobal(cursor_pos)
        
        for widget in QApplication.allWidgets():
            if isinstance(widget, DesktopWindow) and widget.isVisible():
                desktop_rect = widget.geometry()
                if desktop_rect.contains(global_pos):
                    desktop_window_under_cursor = widget
                    break
        
        if desktop_window_under_cursor:
            logger.debug("dropEvent - cursor sobre DesktopWindow, rechazando para que DesktopWindow lo capture")
            event.ignore()
            return
        
        super().dropEvent(event)
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close - cleanup resources and save state."""
        if hasattr(self._tab_manager, 'get_watcher'):
            watcher = self._tab_manager.get_watcher()
            if watcher:
                watcher.stop_watching()
        
        if self._workspace_manager:
            self._workspace_manager.save_current_state(self._tab_manager, self._sidebar)
        else:
            self._save_app_state()
        
        if self._current_preview_window:
            self._current_preview_window.close()
        if hasattr(self._preview_service, "stop_workers"):
            self._preview_service.stop_workers()
        self._preview_service.clear_cache()
        event.accept()
    
    def _save_app_state(self) -> None:
        """Save complete application state before closing (backward compatibility only)."""
        save_app_state(self, self._tab_manager)
    
    def _on_sidebar_new_focus(self, path: str) -> None:
        """Handle new focus request from sidebar."""
        self._tab_manager.add_tab(path)
    
    def _navigate_to_folder(self, folder_path: str) -> None:
        # Cancelar búsqueda si está activa antes de navegar
        self._cancel_search_if_active()
        
        if not os.access(folder_path, os.R_OK):
            error_dialog = ErrorDialog(
                parent=self,
                title="Permiso requerido",
                message="No se puede acceder a esta carpeta. Verifica permisos.",
                is_warning=True
            )
            error_dialog.exec()
            return
        
        is_desktop = is_desktop_focus(folder_path)
        
        tabs = self._tab_manager.get_tabs()
        normalized_path = normalize_path(folder_path)
        tab_index = None
        
        for idx, tab_path in enumerate(tabs):
            normalized_tab = normalize_path(tab_path)
            if normalized_tab == normalized_path:
                tab_index = idx
                break
        
        if tab_index is not None:
            self._tab_manager.select_tab(tab_index)
        else:
            self._tab_manager.add_tab(folder_path)
        
        # Añadir subcarpeta al sidebar si su padre existe
        parent_path = os.path.dirname(normalized_path)
        normalized_parent = normalize_path(parent_path)
        
        if self._sidebar.has_path(normalized_parent):
            # El padre existe en el sidebar, añadir esta carpeta como hija
            self._sidebar.add_path(folder_path)
        
        self._file_view_container.set_desktop_mode(is_desktop)
    
    def _on_sidebar_folder_selected(self, path: str) -> None:
        """Handle folder selection from sidebar - delega en método central."""
        self._navigate_to_folder(path)
    
    def _on_state_selected(self, state: str) -> None:
        """Handle state selection from sidebar - cancelar búsqueda si está activa."""
        self._cancel_search_if_active()
    
    def _on_sidebar_remove_focus(self, path: str) -> None:
        """Handle focus removal request from sidebar - solo permite eliminar carpetas raíz."""
        normalized_path = normalize_path(path)
        
        if normalized_path not in self._sidebar._path_to_item:
            return
        
        item = self._sidebar._path_to_item[normalized_path]
        if item.parent() and item.parent() != self._sidebar._model.invisibleRootItem():
            return
        
        self._tab_manager.remove_tab_by_path(path)
        self._sidebar.remove_focus_path(path)
        try:
            active = self._tab_manager.get_active_folder()
            if active:
                norm_removed = normalize_path(path)
                norm_active = normalize_path(active)
                if norm_active == norm_removed or norm_active.startswith(norm_removed + os.sep):
                    self._file_view_container.clear_current_focus()
        except Exception as e:
            logger.warning(f"Failed to clear focus after removing tab {path}: {e}")
        try:
            state_manager = self._tab_manager.get_state_manager()
            tabs = self._tab_manager.get_tabs()
            active_tab = self._tab_manager.get_active_folder()
            history = self._tab_manager.get_history()
            history_index = self._tab_manager.get_history_index()
            focus_tree_paths = self._sidebar.get_focus_tree_paths()
            expanded_nodes = self._sidebar.get_expanded_paths()
            state = state_manager.build_app_state(
                tabs=tabs,
                active_tab_path=active_tab,
                history=history,
                history_index=history_index,
                focus_tree_paths=focus_tree_paths,
                expanded_nodes=expanded_nodes
            )
            state_manager.save_app_state(state)
        except Exception as e:
            logger.error(f"Failed to save app state after removing tab {path}: {e}", exc_info=True)
        try:
            QToolTip.showText(QCursor.pos(), "Quitado del sidebar")
        except Exception as e:
            logger.debug(f"Failed to show tooltip: {e}")
    
    def _on_tabs_changed_sync_sidebar(self, tabs: list) -> None:
        """Sync sidebar with current tabs."""
        if self._is_initializing:
            return
        self._sidebar._tree_view.setUpdatesEnabled(False)
        try:
            for tab_path in tabs:
                self._sidebar.add_focus_path(tab_path)
        finally:
            self._sidebar._tree_view.setUpdatesEnabled(True)
    
    def _on_file_box_button_clicked(self) -> None:
        """Handle file box button click - add files to active session or create new one."""
        
        # Si hay panel minimizado, reabrirlo y salir
        if self._file_box_panel_minimized and self._current_file_box_panel:
            self._restore_file_box_panel()
            return
        
        selected_files = get_selected_files(self._file_view_container)
        
        if not selected_files:
            error_dialog = ErrorDialog(
                parent=self,
                title="Sin archivos seleccionados",
                message="Por favor, selecciona los archivos que deseas usar.",
                is_warning=True
            )
            error_dialog.exec()
            return
        
        try:
            file_box_service = FileBoxService()
            history_service = FileBoxHistoryService()
            
            if self._current_file_box_panel and not self._file_box_panel_minimized:
                current_session = self._current_file_box_panel.get_current_session()
                if current_session:
                    temp_folder = current_session.temp_folder_path
                    added_count = file_box_service.add_files_to_existing_folder(selected_files, temp_folder)
                    
                    if added_count == 0:
                        error_dialog = ErrorDialog(
                            parent=self,
                            title="Error",
                            message="No se pudieron añadir los archivos a la sesión actual.",
                            is_warning=False
                        )
                        error_dialog.exec()
                        return
                    
                    self._current_file_box_panel.add_files_to_session(selected_files)
                    
                    updated_session = self._current_file_box_panel.get_current_session()
                    history_service.add_session(updated_session)
                    
                    if self._history_panel.isVisible():
                        self._history_panel.refresh()
                    
                    self._update_file_box_button_state()
                    return
            
            temp_folder = file_box_service.prepare_files(selected_files)
            if not temp_folder:
                error_dialog = ErrorDialog(
                    parent=self,
                    title="Error",
                    message="No se pudieron preparar los archivos.",
                    is_warning=False
                )
                error_dialog.exec()
                return
            
            session = file_box_service.create_file_box_session(selected_files, temp_folder)
            history_service.add_session(session)
            
            self._ensure_only_one_panel_visible("file_box")
            
            self._current_file_box_panel.set_session(session)
            self._current_file_box_panel.setVisible(True)
            # Instalar filtro de eventos para capturar barra espaciadora
            from app.ui.widgets.event_filter_utils import install_event_filter_recursive
            install_event_filter_recursive(self._current_file_box_panel, self)
            self._update_right_panel_layout("FILE_BOX")
            self._file_box_panel_minimized = False
            self._update_file_box_button_state()
            
            if self._history_panel.isVisible():
                self._history_panel.refresh()
            
        except Exception as e:
            logger.error(f"Failed to prepare file box: {e}", exc_info=True)
            error_dialog = ErrorDialog(
                parent=self,
                title="Error",
                message=f"Error al preparar la caja de archivos:\n{str(e)}",
                is_warning=False
            )
            error_dialog.exec()
    
    def _update_right_panel_layout(self, mode: str) -> None:
        """
        Actualiza el layout del panel derecho según el modo.
        
        Args:
            mode: "NONE" | "FILE_BOX" | "HISTORY"
        """
        if mode == "NONE":
            self._content_splitter.setSizes([200, 1100, 0, 0])
        elif mode == "FILE_BOX":
            self._content_splitter.setSizes([200, 700, 400, 0])
        elif mode == "HISTORY":
            self._content_splitter.setSizes([200, 700, 0, 400])
    
    def _minimize_file_box_panel(self) -> None:
        """Minimize the file box panel without closing the session."""
        if not self._current_file_box_panel:
            return
        
        self._current_file_box_panel.setVisible(False)
        self._file_box_panel_minimized = True
        self._update_right_panel_layout("NONE")
        self._update_file_box_button_state()
    
    def _restore_file_box_panel(self) -> None:
        """Restore the minimized file box panel."""
        if not self._current_file_box_panel or not self._file_box_panel_minimized:
            return
        
        self._ensure_only_one_panel_visible("file_box")
        
        self._current_file_box_panel.setVisible(True)
        # Instalar filtro de eventos para capturar barra espaciadora
        from app.ui.widgets.event_filter_utils import install_event_filter_recursive
        install_event_filter_recursive(self._current_file_box_panel, self)
        self._file_box_panel_minimized = False
        self._update_right_panel_layout("FILE_BOX")
        self._update_file_box_button_state()
    
    def _close_file_box_panel(self) -> None:
        """Close the file box panel and save session to history."""
        if not self._current_file_box_panel:
            return
        
        history_service = FileBoxHistoryService()
        current_session = self._current_file_box_panel.get_current_session()
        if current_session:
            history_service.add_session(current_session)
        
        self._current_file_box_panel.set_session(None)
        self._current_file_box_panel.setVisible(False)
        self._file_box_panel_minimized = False
        self._update_right_panel_layout("NONE")
        self._update_file_box_button_state()
    
    def _update_file_box_button_state(self) -> None:
        """Update file box button visual state to indicate active session."""
        has_active_session = (self._current_file_box_panel is not None and 
                             self._current_file_box_panel.get_current_session() is not None)
        is_minimized = self._file_box_panel_minimized
        
        if has_active_session:
            self._workspace_selector.set_file_box_button_active(True, is_minimized)
        else:
            self._workspace_selector.set_file_box_button_active(False, False)
    
    def _ensure_only_one_panel_visible(self, show_panel: str) -> None:
        """Asegura que solo un panel esté visible: 'file_box' o 'history'."""
        if show_panel == "file_box":
            if self._history_panel and self._history_panel.isVisible():
                self._history_panel.setVisible(False)
        elif show_panel == "history":
            if self._current_file_box_panel and self._current_file_box_panel.isVisible():
                self._current_file_box_panel.setVisible(False)
                self._file_box_panel_minimized = True
    
    def _on_history_panel_toggle(self) -> None:
        """Handle history panel toggle request - show history in file box panel area."""
        if not self._history_panel:
            return
        
        is_history_visible = self._history_panel.isVisible()
        
        if is_history_visible:
            self._history_panel.setVisible(False)
            if self._current_file_box_panel and self._current_file_box_panel.isVisible():
                self._current_file_box_panel.setVisible(False)
                self._file_box_panel_minimized = True
            self._update_right_panel_layout("NONE")
        else:
            self._ensure_only_one_panel_visible("history")
            self._history_panel.setVisible(True)
            self._history_panel.refresh()
            self._update_right_panel_layout("HISTORY")
    
    def _close_history_panel_only(self) -> None:
        """Cerrar HistoryPanel (ocultar sin limpiar datos)."""
        if not self._history_panel:
            return
        
        self._history_panel.setVisible(False)
        self._update_right_panel_layout("NONE")
    
    def _on_rename_state_requested(self) -> None:
        """Handle rename state label request - show dialog."""
        if not self._state_label_manager:
            return
        
        current_labels = self._state_label_manager.get_all_labels()
        dialog = RenameStateDialog(self._state_label_manager, current_labels, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Labels already updated by manager, just refresh UI
            self._on_state_labels_changed()
    
    def _get_label_callback(self):
        """Get callback function for retrieving state labels."""
        if not self._state_label_manager:
            from app.ui.widgets.state_badge_widget import STATE_LABELS
            return lambda state: STATE_LABELS.get(state, "")
        return self._state_label_manager.get_label
    
    def _update_widgets_label_callback(self) -> None:
        """Update label callback in all existing widgets."""
        if not hasattr(self, '_file_view_container'):
            return
        
        container = self._file_view_container
        callback = self._get_label_callback()
        
        # Update grid view tiles
        if hasattr(container, '_grid_view') and container._grid_view:
            grid_view = container._grid_view
            grid_view._get_label_callback = callback
            # Update existing badges
            for i in range(grid_view.layout().count()):
                item = grid_view.layout().itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if hasattr(widget, '_state_badge') and widget._state_badge:
                        widget._state_badge.set_get_label_callback(callback)
                    widget.update()
        
        # Update list view cells
        if hasattr(container, '_list_view') and container._list_view:
            list_view = container._list_view
            list_view._get_label_callback = callback
            try:
                delegate = getattr(list_view, '_state_delegate', None)
                if delegate and hasattr(delegate, 'set_get_label_callback'):
                    delegate.set_get_label_callback(callback)
            except Exception:
                pass
            list_view.viewport().update()
    
    def _on_state_labels_changed(self) -> None:
        """Handle state labels change - refresh UI components."""
        # Update callback in all widgets
        self._update_widgets_label_callback()
        
        # Refresh workspace selector menu
        if hasattr(self, '_workspace_selector') and self._workspace_selector:
            self._workspace_selector._refresh_state_menu()
    
    def _on_search_mode_changed(self, enabled: bool) -> None:
        """Handle search mode change."""
        if not enabled:
            # Limpiar modo búsqueda y restaurar vista normal
            self._file_view_container.set_search_mode(False, [])
        else:
            logger.info("search mode enabled")
    
    def _on_search_results_changed(self, results: list) -> None:
        """Handle search results change - update file view with results."""
        # Siempre actualizar (incluso con lista vacía si está en modo búsqueda)
        # Esto muestra resultados encontrados o lista vacía si no hay coincidencias
        logger.info(f"search results received | count={len(results)}")
        self._file_view_container.set_search_mode(True, results)

    def _hide_headers_for_diagnosis(self) -> None:
        """
        TEMPORAL: Ocultar headers, sidebar y footer para diagnóstico de parpadeo.

        Componentes a ocultar:
        - AppHeader ← CAUSA PARPADEO
        - SecondaryHeader ← CAUSA PARPADEO
        - WorkspaceSelector (WorkspaceHeader) ← CAUSA PARPADEO
        - Header del modo vista de lista (QTableWidget header) ← CAUSA PARPADEO
        - Sidebar ← CAUSA PARPADEO
        - Footer (PathFooterWidget) ← CAUSA PARPADEO

        CONFIRMACIÓN FINAL: TODOS OCULTOS PARA VERIFICAR QUE SIN ELLOS NO HAY PARPADEO
        """
        # Ocultar AppHeader (CAUSA PARPADEO)
        if hasattr(self, '_app_header') and self._app_header:
            self._app_header.hide()

        # Ocultar SecondaryHeader (CAUSA PARPADEO)
        if hasattr(self, '_secondary_header') and self._secondary_header:
            self._secondary_header.hide()

        # Ocultar WorkspaceSelector (CAUSA PARPADEO)
        if hasattr(self, '_workspace_selector') and self._workspace_selector:
            self._workspace_selector.hide()

        # Ocultar Sidebar (CAUSA PARPADEO)
        if hasattr(self, '_sidebar') and self._sidebar:
            self._sidebar.hide()

        # Ocultar Footer (CAUSA PARPADEO)
        if hasattr(self, '_path_footer') and self._path_footer:
            self._path_footer.hide()

        # Ocultar header de FileListView (CAUSA PARPADEO)
        if hasattr(self, '_file_view_container') and self._file_view_container:
            container = self._file_view_container
            if hasattr(container, '_list_view') and container._list_view:
                list_view = container._list_view
                # Ocultar header horizontal del QTableWidget
                list_view.horizontalHeader().hide()
                # Ocultar header vertical también
                list_view.verticalHeader().hide()

    def paintEvent(self, event) -> None:
        """
        Pintar fondo de MainWindow según feature flag.

        Sistema antiguo (USE_ROUNDED_CORNERS_IN_ROOT=True):
          - Pinta con QPainterPath redondeado directamente en la raíz
          - Áreas fuera del path quedan transparentes (esquinas redondeadas visibles)

        Sistema actual (USE_ROUNDED_CORNERS_IN_ROOT=False):
          - Pinta rectángulo sólido completo (sin esquinas redondeadas)
          - Optimizado para anti-flicker durante resize
        """
        if DEBUG_LAYOUT:
            logger.info(f"🎨 [Main] ENTRY paintEvent | resize_flag={self._main_resize_in_progress}")
        start_time = QElapsedTimer()
        start_time.start()

        if DEBUG_LAYOUT:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        from app.core.constants import SIDEBAR_BG, ROUNDED_BG_RADIUS

        if USE_ROUNDED_CORNERS_IN_ROOT:
            # SISTEMA ANTIGUO: Pintar con esquinas redondeadas usando QPainterPath
            rect = self.rect()
            corner_radius = ROUNDED_BG_RADIUS

            # Crear path con esquinas redondeadas
            from PySide6.QtGui import QPainterPath
            path = QPainterPath()
            path.addRoundedRect(rect, corner_radius, corner_radius)

            # Rellenar SOLO el área dentro del path (esquinas quedan transparentes)
            bg_color = QColor(SIDEBAR_BG)
            painter.fillPath(path, bg_color)
        else:
            # SISTEMA ACTUAL: Pintar rectángulo sólido completo (anti-flicker)
            painter.fillRect(self.rect(), QColor(SIDEBAR_BG))

        painter.end()

        if not hasattr(self, '_paint_count_total'): self._paint_count_total = 0
        self._paint_count_total += 1
        elapsed = start_time.nsecsElapsed() / 1000000.0
        if DEBUG_LAYOUT:
            logger.info(f"🎨 [Main] Paint #{self._paint_count_total} | dur={elapsed:.2f}ms | resize={self._main_resize_in_progress}")
