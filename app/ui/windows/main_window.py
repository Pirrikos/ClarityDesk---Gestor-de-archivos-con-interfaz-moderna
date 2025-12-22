"""
MainWindow - Main application window with Focus Dock layout.

Focus Dock replaces the old sidebar navigation system.
"""

import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeySequence, QShortcut, QPainter, QColor, QCursor
from PySide6.QtWidgets import QWidget, QMessageBox, QApplication, QToolTip

from app.core.constants import DEBUG_LAYOUT, FILE_SYSTEM_DEBOUNCE_MS
from app.core.logger import get_logger
from app.managers.tab_manager import TabManager
from app.managers.workspace_manager import WorkspaceManager
from app.services.desktop_path_helper import is_desktop_focus
from app.services.file_open_service import open_file_with_system
from app.services.icon_service import IconService
from app.services.path_utils import normalize_path
from app.services.preview_service import PreviewService
from app.ui.windows.desktop_window import DesktopWindow
from app.ui.windows.main_window_file_handler import filter_previewable_files
from app.ui.windows.main_window_setup import setup_ui
from app.ui.windows.main_window_state import load_app_state, save_app_state
from app.ui.windows.quick_preview_window import QuickPreviewWindow
from app.ui.widgets.file_view_sync import get_selected_files

logger = get_logger(__name__)


class MainWindow(QWidget):
    """Main application window with Focus Dock and content area."""

    def __init__(self, tab_manager: TabManager, workspace_manager: WorkspaceManager, parent=None):
        """Initialize MainWindow with TabManager and WorkspaceManager."""
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
            self.setContentsMargins(0, 0, 0, 0)
            
            self._tab_manager = tab_manager
            self._workspace_manager = workspace_manager
            self._icon_service = IconService()
            self._preview_service = PreviewService(self._icon_service)
            self._current_preview_window = None
            self._is_initializing = True
            
            self.setAutoFillBackground(False)
            self.setStyleSheet("background-color: #1A1D22;")
            
            self._tab_manager.set_workspace_manager(workspace_manager)
            self._setup_ui()
            self._connect_signals()
            self._setup_shortcuts()
            self._load_workspace_state()
            self._is_initializing = False
            
        except Exception as e:
            logger.error(f"Excepción crítica en MainWindow.__init__: {e}", exc_info=True)
            raise

    def paintEvent(self, event):
        """Pintar el fondo de la ventana raíz para cubrir el margen fantasma de Windows."""
        if DEBUG_LAYOUT:
            super().paintEvent(event)
            return
        
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setClipping(False)
        
        rect = self.rect()
        extended_rect = rect.adjusted(-8, -8, 8, 8)
        
        bg_color = QColor("#1A1D22")
        p.fillRect(extended_rect, bg_color)
        p.end()
        
        super().paintEvent(event)

    def _setup_ui(self) -> None:
        """Build the UI layout with Focus Dock integrated."""
        self._file_view_container, self._sidebar, self._window_header, self._app_header, self._workspace_selector, self._history_panel, self._content_splitter, self._file_box_panel_placeholder = setup_ui(
            self, self._tab_manager, self._icon_service, self._workspace_manager
        )
        self._current_file_box_panel = None
        self._history_only_panel = None

    def _connect_signals(self) -> None:
        """Connect UI signals to TabManager."""
        self._window_header.request_close.connect(self.close)
        self._window_header.request_minimize.connect(self.showMinimized)
        self._window_header.request_toggle_maximize.connect(self._toggle_maximize)
        
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
        
        self._sidebar.new_focus_requested.connect(self._on_sidebar_new_focus)
        self._sidebar.folder_selected.connect(self._on_sidebar_folder_selected)
        self._sidebar.focus_remove_requested.connect(self._on_sidebar_remove_focus)
        
        watcher = self._tab_manager.get_watcher()
        if watcher:
            watcher.folder_renamed.connect(self._sidebar.update_focus_path)
            watcher.folder_disappeared.connect(self._on_folder_disappeared)
            watcher.structural_change_detected.connect(self._on_structural_change_detected)
        
        self._workspace_selector.workspace_selected.connect(self._on_workspace_selected)
        self._workspace_manager.workspace_changed.connect(self._on_workspace_changed)
        
        # File box signals
        self._app_header.file_box_button_clicked.connect(self._on_file_box_button_clicked)
        self._app_header.history_panel_toggle_requested.connect(self._on_history_panel_toggle)

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
                state.get('expanded_nodes', [])
            )
        else:
            self._tab_manager.load_workspace_state({
                'tabs': [],
                'active_tab': None
            })
            self._sidebar.load_workspace_state([], [])
        
        self._app_header.update_workspace(active_workspace.name)
    
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
    
    def _on_workspace_changed(self, workspace_id: str) -> None:
        """Handle workspace change - actualizar UI con nuevo estado."""
        if not self._workspace_manager:
            return
        
        workspace = self._workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return
        
        self._app_header.update_workspace(workspace.name)

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
        self._app_header.update_workspace(path)
    
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
        
        normalized_path = os.path.normpath(folder_path)
        
        if normalized_path not in self._sidebar._path_to_item:
            return
        
        tabs = self._tab_manager.get_tabs()
        normalized_tabs = {os.path.normpath(tab) for tab in tabs}
        
        if normalized_path in normalized_tabs:
            self._schedule_sidebar_sync(structural=True)
        else:
            self._sidebar.remove_focus_path(normalized_path)
    
    def _on_structural_change_detected(self, watched_folder: str) -> None:
        """Handle structural changes detected (moves between parents)."""
        self._schedule_sidebar_sync(structural=True)
    
    def _schedule_sidebar_sync(self, structural: bool = False) -> None:
        if not hasattr(self, '_sidebar_sync_timer'):
            self._sidebar_sync_timer = QTimer(self)
            self._sidebar_sync_timer.setSingleShot(True)
            self._sidebar_sync_timer.timeout.connect(self._resync_sidebar_from_tabs)
        
        self._pending_structural_sync = structural
        
        self._sidebar_sync_timer.stop()
        self._sidebar_sync_timer.start(FILE_SYSTEM_DEBOUNCE_MS)
    
    def mousePressEvent(self, event) -> None:
        """Permitir redimensionar desde cualquier borde/corner en ventana sin marco."""
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                edges = self._detect_resize_edges(event.globalPos())
                if edges and self.windowHandle():
                    self.windowHandle().startSystemResize(edges)
                    event.accept()
                    return
        except Exception:
            pass
        super().mousePressEvent(event)
    
    def _detect_resize_edges(self, global_pos) -> Qt.Edges:
        """Detectar bordes cercanos para iniciar resize nativo (Windows)."""
        try:
            geo = self.frameGeometry()
            margin = 6
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
        except Exception:
            return Qt.Edges()
    
    def _resync_sidebar_from_tabs(self) -> None:
        expanded_paths = self._sidebar.get_expanded_paths()
        
        self._sidebar._tree_view.setUpdatesEnabled(False)
        try:
            all_paths = list(self._sidebar._path_to_item.keys())
            for path in all_paths:
                self._sidebar.remove_focus_path(path)
            
            tabs = self._tab_manager.get_tabs()
            for tab_path in tabs:
                normalized_tab = os.path.normpath(tab_path)
                if os.path.exists(normalized_tab) and os.path.isdir(normalized_tab):
                    self._sidebar.add_focus_path(normalized_tab)
        finally:
            self._sidebar._tree_view.setUpdatesEnabled(True)
        
        for path in expanded_paths:
            normalized_path = os.path.normpath(path)
            if normalized_path in self._sidebar._path_to_item:
                item = self._sidebar._path_to_item[normalized_path]
                index = self._sidebar._model.indexFromItem(item)
                if index.isValid():
                    self._sidebar._tree_view.expand(index)

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

        selected = get_selected_files(self._file_view_container)
        if not selected:
            return

        allowed_files = filter_previewable_files(selected)
        if not allowed_files:
            return

        preview = QuickPreviewWindow(
            self._preview_service,
            file_paths=allowed_files,
            start_index=0,
            parent=self
        )

        self._current_preview_window = preview
        preview.show()
        preview.setFocus()
    
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
        
        self._file_view_container.set_desktop_mode(is_desktop)
    
    def _on_sidebar_folder_selected(self, path: str) -> None:
        """Handle folder selection from sidebar - delega en método central."""
        self._navigate_to_folder(path)
    
    def _on_sidebar_remove_focus(self, path: str) -> None:
        """Handle focus removal request from sidebar - solo permite eliminar carpetas raíz."""
        normalized_path = os.path.normpath(path)
        
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
                norm_removed = os.path.normpath(path)
                norm_active = os.path.normpath(active)
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
        """Handle file box button click - prepare files and open file box."""
        from app.services.file_box_service import FileBoxService
        from app.services.file_box_history_service import FileBoxHistoryService
        from app.ui.widgets.file_view_sync import get_selected_files
        from app.ui.widgets.file_box_panel import FileBoxPanel
        
        # Get selected files
        selected_files = get_selected_files(self._file_view_container)
        
        if not selected_files:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Sin archivos seleccionados",
                "Por favor, selecciona los archivos que deseas usar."
            )
            return
        
        try:
            # Initialize services
            file_box_service = FileBoxService()
            history_service = FileBoxHistoryService()
            
            # Prepare files
            temp_folder = file_box_service.prepare_files(selected_files)
            if not temp_folder:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudieron preparar los archivos."
                )
                return
            
            # Create session
            session = file_box_service.create_file_box_session(selected_files, temp_folder)
            
            # Persist to history
            history_service.add_session(session)
            
            # Show/hide file box panel (toggle behavior)
            if self._current_file_box_panel:
                self._close_file_box_panel()
            else:
                # Create and show new panel
                self._current_file_box_panel = FileBoxPanel(
                    session,
                    history_service,
                    self._content_splitter,
                    icon_service=self._icon_service
                )
                
                # Hide placeholder first to avoid flash
                self._file_box_panel_placeholder.hide()
                
                # Temporarily disable updates to prevent flashing
                self._content_splitter.setUpdatesEnabled(False)
                
                try:
                    # Replace placeholder with panel using replaceWidget
                    placeholder_index = self._content_splitter.indexOf(self._file_box_panel_placeholder)
                    if placeholder_index >= 0:
                        self._content_splitter.replaceWidget(placeholder_index, self._current_file_box_panel)
                    
                    # Connect close signal
                    self._current_file_box_panel.close_requested.connect(self._close_file_box_panel)
                    
                    # Adjust splitter sizes: sidebar | files | file box panel
                    self._content_splitter.setSizes([200, 700, 400])
                finally:
                    # Re-enable updates
                    self._content_splitter.setUpdatesEnabled(True)
            
            # Refresh history panel if visible
            if self._history_panel.isVisible():
                self._history_panel.refresh()
            
        except Exception as e:
            logger.error(f"Failed to prepare file box: {e}", exc_info=True)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Error",
                f"Error al preparar la caja de archivos:\n{str(e)}"
            )
    
    def _close_file_box_panel(self) -> None:
        """Close the file box panel and restore placeholder."""
        if not self._current_file_box_panel:
            return
        
        # Replace panel with placeholder
        panel_index = self._content_splitter.indexOf(self._current_file_box_panel)
        if panel_index >= 0:
            self._content_splitter.replaceWidget(panel_index, self._file_box_panel_placeholder)
            self._current_file_box_panel.setParent(None)
            self._current_file_box_panel.deleteLater()
        
        self._current_file_box_panel = None
        self._file_box_panel_placeholder.hide()
        # Adjust splitter to hide panel area
        self._content_splitter.setSizes([200, 1100, 0])
    
    def _on_history_panel_toggle(self) -> None:
        """Handle history panel toggle request - show history in file box panel area."""
        # If file box panel is open, close it first
        if self._current_file_box_panel:
            self._close_file_box_panel()
        
        # Toggle history-only panel in file box panel area
        if hasattr(self, '_history_only_panel') and self._history_only_panel:
            # Close history panel
            panel_index = self._content_splitter.indexOf(self._history_only_panel)
            if panel_index >= 0:
                self._content_splitter.replaceWidget(panel_index, self._file_box_panel_placeholder)
                self._history_only_panel.setParent(None)
                self._history_only_panel.deleteLater()
            
            self._history_only_panel = None
            self._file_box_panel_placeholder.hide()
            # Adjust splitter to hide panel area
            self._content_splitter.setSizes([200, 1100, 0])
        else:
            # Create and show history-only panel
            from app.services.file_box_history_service import FileBoxHistoryService
            from app.ui.widgets.file_box_history_panel import FileBoxHistoryPanel
            
            # Hide placeholder first to avoid flash
            self._file_box_panel_placeholder.hide()
            
            # Temporarily disable updates to prevent flashing
            self._content_splitter.setUpdatesEnabled(False)
            
            try:
                history_service = FileBoxHistoryService()
                self._history_only_panel = FileBoxHistoryPanel(
                    history_service,
                    self._content_splitter,
                    icon_service=self._icon_service
                )
                
                # Connect close signal
                self._history_only_panel.close_requested.connect(self._close_history_only_panel)
                
                # Replace placeholder with panel
                placeholder_index = self._content_splitter.indexOf(self._file_box_panel_placeholder)
                if placeholder_index >= 0:
                    self._content_splitter.replaceWidget(placeholder_index, self._history_only_panel)
                
                # Adjust splitter sizes: sidebar | files | history panel
                self._content_splitter.setSizes([200, 700, 400])
            finally:
                # Re-enable updates
                self._content_splitter.setUpdatesEnabled(True)
    
    def _close_history_only_panel(self) -> None:
        """Close the history-only panel and restore placeholder."""
        if not hasattr(self, '_history_only_panel') or not self._history_only_panel:
            return
        
        # Replace panel with placeholder
        panel_index = self._content_splitter.indexOf(self._history_only_panel)
        if panel_index >= 0:
            self._content_splitter.replaceWidget(panel_index, self._file_box_panel_placeholder)
            self._history_only_panel.setParent(None)
            self._history_only_panel.deleteLater()
        
        self._history_only_panel = None
        self._file_box_panel_placeholder.hide()
        # Adjust splitter to hide panel area
        self._content_splitter.setSizes([200, 1100, 0])
