"""
MainWindow - Main application window with Focus Dock layout.

Focus Dock replaces the old sidebar navigation system.
"""

import os
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QEvent, QPoint, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeySequence, QShortcut, QPainter, QColor, QCursor
from PySide6.QtWidgets import QWidget, QMessageBox, QApplication, QToolTip, QDialog, QGraphicsOpacityEffect

from app.core.constants import DEBUG_LAYOUT, FILE_SYSTEM_DEBOUNCE_MS, CENTRAL_AREA_BG, RESIZE_EDGE_DETECTION_MARGIN
from app.core.logger import get_logger
from app.managers.tab_manager import TabManager
from app.managers.workspace_manager import WorkspaceManager
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
from app.ui.windows.quick_preview_window import QuickPreviewWindow
from app.ui.widgets.file_view_sync import get_selected_files, switch_view

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
            
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
            
            self.setWindowTitle("ClarityDesk Pro")
            self.setMinimumSize(1050, 675)
            self.setMouseTracking(True)
            self._is_resizing = False
            
            self._tab_manager = tab_manager
            self._workspace_manager = workspace_manager
            self._desktop_window = desktop_window  # Inyección de dependencia
            self._icon_service = IconService()
            self._preview_service = PreviewPdfService(self._icon_service)
            self._state_label_manager = StateLabelManager()
            self._current_preview_window = None
            self._is_initializing = True
            self._transition_animation: Optional[QParallelAnimationGroup] = None
            self._fade_out_anim: Optional[QPropertyAnimation] = None
            self._fade_in_anim: Optional[QPropertyAnimation] = None
            
            self.setObjectName("MainWindow")
            self.setAutoFillBackground(False)
            self.setStyleSheet(f"QWidget#MainWindow {{ background-color: {CENTRAL_AREA_BG}; }}")
            
            self._tab_manager.set_workspace_manager(workspace_manager)
            self._setup_ui()
            self._connect_signals()
            self._setup_shortcuts()
            self._load_workspace_state()
            self._is_initializing = False
            
            QApplication.instance().installEventFilter(self)
            
        except Exception as e:
            logger.error(f"Excepción crítica en MainWindow.__init__: {e}", exc_info=True)
            raise

    def paintEvent(self, event):
        """
        Pintar el fondo de la ventana raíz.
        
        Cubre toda el área incluyendo el margen invisible de 3px alrededor
        para mantener apariencia uniforme mientras permite detección de bordes.
        """
        if DEBUG_LAYOUT:
            super().paintEvent(event)
            return
        
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setClipping(False)
        
        rect = self.rect()
        bg_color = QColor(CENTRAL_AREA_BG)
        p.fillRect(rect, bg_color)
        p.end()
        
        super().paintEvent(event)

    def _setup_ui(self) -> None:
        """Build the UI layout with Focus Dock integrated."""
        self._file_view_container, self._sidebar, self._window_header, self._app_header, self._secondary_header, self._workspace_selector, self._history_panel, self._content_splitter, self._current_file_box_panel = setup_ui(
            self, self._tab_manager, self._icon_service, self._workspace_manager
        )
        self._file_box_panel_minimized = False
        
        if self._current_file_box_panel:
            self._current_file_box_panel.close_requested.connect(self._close_file_box_panel)
            self._current_file_box_panel.minimize_requested.connect(self._minimize_file_box_panel)
            self._current_file_box_panel.file_open_requested.connect(self._on_file_open)
        
        if self._history_panel:
            self._history_panel.close_requested.connect(self._close_history_panel_only)

    def _connect_signals(self) -> None:
        """Connect UI signals to TabManager."""
        self._window_header.request_close.connect(self.close)
        self._window_header.request_minimize.connect(self.showMinimized)
        self._window_header.request_toggle_maximize.connect(self._toggle_maximize)
        
        # Conectar señal del AppHeader para mostrar dock de escritorio
        self._app_header.show_desktop_requested.connect(self._on_show_desktop_requested)
        
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
        
        watcher = self._tab_manager.get_watcher()
        if watcher:
            watcher.folder_renamed.connect(self._sidebar.update_focus_path)
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
        
        # Set state label manager
        self._workspace_selector.set_state_label_manager(self._state_label_manager)
        self._state_label_manager.labels_changed.connect(self._on_state_labels_changed)
        
        # Set label callback for file views
        if hasattr(self, '_file_view_container') and self._file_view_container:
            callback = self._get_label_callback()
            self._file_view_container._get_label_callback = callback
            # Update existing widgets
            self._update_widgets_label_callback()
        
        # Set tab_manager and sidebar for workspace deletion operations
        self._workspace_selector.set_tab_manager(self._tab_manager)
        self._workspace_selector.set_sidebar(self._sidebar)
        self._workspace_selector.set_signal_controller(self)

    def _on_show_desktop_requested(self) -> None:
        """Ocultar MainWindow y mostrar DesktopWindow con animación elegante tipo macOS."""
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
        
        # Cancelar animación anterior si existe
        if self._transition_animation:
            self._transition_animation.stop()
            self._transition_animation.deleteLater()
            self._transition_animation = None
        
        # Verificar si DesktopWindow ya está completamente visible
        is_already_visible = desktop_window.isVisible() and desktop_window.windowOpacity() >= 0.99
        
        if is_already_visible:
            # Si ya está visible, solo ocultar MainWindow sin animación
            self.hide()
            desktop_window.raise_()
            desktop_window.activateWindow()
            return
        
        # Asegurar que DesktopWindow esté visible y reconocido por Qt ANTES de ocultar MainWindow
        # Solo llamar a show() si no está visible
        if not desktop_window.isVisible():
            desktop_window.setWindowOpacity(0.01)  # Opacidad mínima pero visible para Qt
            desktop_window.show()
            desktop_window.raise_()
            desktop_window.activateWindow()
            QApplication.processEvents()
        else:
            # Si ya está visible pero con opacidad baja, solo ajustar opacidad
            current_opacity = desktop_window.windowOpacity()
            if current_opacity < 0.01:
                desktop_window.setWindowOpacity(0.01)
        
        # Crear efectos de opacidad
        main_opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(main_opacity_effect)
        main_opacity_effect.setOpacity(1.0)
        
        # Animación de fade out para MainWindow
        fade_out = QPropertyAnimation(main_opacity_effect, b"opacity", self)
        fade_out.setDuration(280)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Animación de fade in para DesktopWindow usando windowOpacity (más confiable)
        current_desktop_opacity = desktop_window.windowOpacity()
        fade_in = QPropertyAnimation(desktop_window, b"windowOpacity", desktop_window)
        fade_in.setDuration(300)
        fade_in.setStartValue(current_desktop_opacity)  # Empezar desde opacidad actual
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Guardar referencias para evitar garbage collection
        self._fade_out_anim = fade_out
        self._fade_in_anim = fade_in
        
        # Callbacks al finalizar
        def on_fade_out_finished():
            self.hide()
            self.setGraphicsEffect(None)
            self._fade_out_anim = None
        
        def on_fade_in_finished():
            desktop_window.activateWindow()
            self._fade_in_anim = None
            if self._transition_animation:
                self._transition_animation.deleteLater()
                self._transition_animation = None
        
        fade_out.finished.connect(on_fade_out_finished)
        fade_in.finished.connect(on_fade_in_finished)
        
        # Iniciar fade out primero, luego fade in con pequeño delay (efecto escalonado elegante)
        fade_out.start()
        QTimer.singleShot(40, fade_in.start)

    def _load_app_state(self) -> None:
        """Load complete application state and restore UI."""
        if not self._workspace_manager:
            load_app_state(self, self._tab_manager)
    
    def _load_workspace_state(self) -> None:
        """Load workspace state and restore UI."""
        if not self._workspace_manager:
            self._load_app_state()
            return
        
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
            edges = self._detect_resize_edges(event.globalPos())
            if edges and self.windowHandle():
                self._is_resizing = True
                self.windowHandle().startSystemResize(edges)
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """Restaurar cursor cuando se suelta el botón del ratón."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_resizing = False
            self.unsetCursor()
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        """Cambiar cursor según posición para indicar zonas de resize."""
        if self._is_resizing:
            super().mouseMoveEvent(event)
            return
        
        global_pos = self.mapToGlobal(event.pos())
        self._update_cursor_for_position(global_pos)
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event) -> None:
        """Restaurar cursor cuando el ratón sale de la ventana."""
        if not self._is_resizing:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)
    
    def eventFilter(self, obj, event) -> bool:
        """Filtrar eventos de mouse para restaurar cursor cuando está fuera del área de resize."""
        if event.type() == QEvent.Type.MouseMove and not self._is_resizing:
            if isinstance(obj, QWidget) and obj.window() == self:
                try:
                    global_pos = event.globalPos() if hasattr(event, 'globalPos') else obj.mapToGlobal(event.pos())
                    self._update_cursor_for_position(global_pos)
                except Exception:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
        
        return super().eventFilter(obj, event)
    
    def _update_cursor_for_position(self, global_pos) -> None:
        """Actualizar cursor según posición global."""
        if self._is_resizing:
            return
        edges = self._detect_resize_edges(global_pos)
        cursor = self._get_resize_cursor(edges)
        self.setCursor(cursor if cursor else Qt.CursorShape.ArrowCursor)
    
    def _detect_resize_edges(self, global_pos: QPoint) -> Qt.Edges:
        """Detectar bordes de ventana para resize nativo."""
        if not self.windowHandle():
            return Qt.Edges()
        
        geo = self.frameGeometry()
        margin = RESIZE_EDGE_DETECTION_MARGIN
        
        edges = Qt.Edges()
        if abs(global_pos.x() - geo.left()) <= margin:
            edges |= Qt.Edge.LeftEdge
        if abs(global_pos.x() - geo.right()) <= margin:
            edges |= Qt.Edge.RightEdge
        if abs(global_pos.y() - geo.top()) <= margin:
            edges |= Qt.Edge.TopEdge
        if abs(global_pos.y() - geo.bottom()) <= margin:
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
        if os.path.isdir(file_path):
            self._navigate_to_folder(file_path)
            return
        else:
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            QTimer.singleShot(180, QApplication.restoreOverrideCursor)
            success = open_file_with_system(file_path)
            if not success:
                QMessageBox.warning(
                    self,
                    "No se puede abrir",
                    "No hay aplicación asociada o el archivo no es reconocible.\n"
                    "Intenta abrirlo manualmente desde el sistema."
                )

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        shortcut.activated.connect(self._open_quick_preview)
        
        back_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        back_shortcut.activated.connect(self._on_nav_back_shortcut)
        
        forward_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        forward_shortcut.activated.connect(self._on_nav_forward_shortcut)

    def _open_quick_preview(self) -> None:
        """Toggle quick preview window (open/close)."""
        if (hasattr(self, "_current_preview_window") and 
            self._current_preview_window and 
            self._current_preview_window.isVisible()):
            self._current_preview_window.close()
            self._current_preview_window = None
            return

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

        preview_window = QuickPreviewWindow(
            self._preview_service,
            file_paths=allowed_files,
            start_index=0,
            parent=None
        )

        self._current_preview_window = preview_window
        preview_window.show()
        preview_window.setFocus()
    
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
        if not os.access(folder_path, os.R_OK):
            QMessageBox.warning(
                self,
                "Permiso requerido",
                "No se puede acceder a esta carpeta. Verifica permisos."
            )
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
            QMessageBox.information(
                self,
                "Sin archivos seleccionados",
                "Por favor, selecciona los archivos que deseas usar."
            )
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
                        QMessageBox.warning(
                            self,
                            "Error",
                            "No se pudieron añadir los archivos a la sesión actual."
                        )
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
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudieron preparar los archivos."
                )
                return
            
            session = file_box_service.create_file_box_session(selected_files, temp_folder)
            history_service.add_session(session)
            
            self._ensure_only_one_panel_visible("file_box")
            
            self._current_file_box_panel.set_session(session)
            self._current_file_box_panel.setVisible(True)
            self._update_right_panel_layout("FILE_BOX")
            self._file_box_panel_minimized = False
            self._update_file_box_button_state()
            
            if self._history_panel.isVisible():
                self._history_panel.refresh()
            
        except Exception as e:
            logger.error(f"Failed to prepare file box: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Error",
                f"Error al preparar la caja de archivos:\n{str(e)}"
            )
    
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
            list_view.viewport().update()
    
    def _on_state_labels_changed(self) -> None:
        """Handle state labels change - refresh UI components."""
        # Update callback in all widgets
        self._update_widgets_label_callback()
        
        # Refresh workspace selector menu
        if hasattr(self, '_workspace_selector') and self._workspace_selector:
            self._workspace_selector._refresh_state_menu()
