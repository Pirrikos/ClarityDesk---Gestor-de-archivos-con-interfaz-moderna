"""
MainWindow - Main application window with Focus Dock layout.

Focus Dock replaces the old sidebar navigation system.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QMessageBox

from app.managers.focus_manager import FocusManager
from app.managers.tab_manager import TabManager
from app.managers.workspace_manager import WorkspaceManager
from app.services.desktop_path_helper import is_desktop_focus
from app.services.file_open_service import open_file_with_system
from app.services.icon_service import IconService
from app.services.path_utils import normalize_path
from app.services.preview_service import PreviewService
from app.core.constants import FILE_SYSTEM_DEBOUNCE_MS
from app.core.logger import get_logger
from app.ui.windows.main_window_file_handler import filter_previewable_files
from app.ui.windows.main_window_setup import setup_ui
from app.ui.windows.main_window_state import load_app_state, save_app_state
from app.ui.windows.quick_preview_window import QuickPreviewWindow
from app.ui.widgets.file_view_sync import get_selected_files

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with Focus Dock and content area."""

    def __init__(self, tab_manager: TabManager, focus_manager: FocusManager, workspace_manager: WorkspaceManager, parent=None):
        """Initialize MainWindow with TabManager, FocusManager, and WorkspaceManager."""
        super().__init__(parent)
        self._tab_manager = tab_manager
        self._focus_manager = focus_manager
        self._workspace_manager = workspace_manager
        self._icon_service = IconService()
        self._preview_service = PreviewService(self._icon_service)
        self._current_preview_window = None
        self._is_initializing = True
        
        # Configurar TabManager para usar WorkspaceManager
        self._tab_manager.set_workspace_manager(workspace_manager)
        
        self._setup_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._load_workspace_state()
        # AppHeader ya se actualiza en _load_workspace_state() con el nombre del workspace
        self._is_initializing = False

    def _setup_ui(self) -> None:
        """Build the UI layout with Focus Dock integrated."""
        self._file_view_container, self._sidebar, self._window_header, self._app_header, self._workspace_selector = setup_ui(
            self, self._tab_manager, self._icon_service, self._workspace_manager
        )

    def _connect_signals(self) -> None:
        """Connect UI signals to TabManager and FocusManager."""
        # WindowHeader -> MainWindow (botones de ventana)
        self._window_header.request_close.connect(self.close)
        self._window_header.request_minimize.connect(self.showMinimized)
        self._window_header.request_toggle_maximize.connect(self._toggle_maximize)
        
        # NOTE: FocusManager is not currently used - Dock calls TabManager directly
        # Keeping FocusManager connection commented for potential future use
        # self._focus_manager.focus_opened.connect(
        #     lambda path: self._tab_manager.add_tab(path)
        # )
        
        # TabManager -> UI (centralizar conexiones para disconnect/reconnect)
        self._tab_manager_connections = [
            (self._tab_manager.tabsChanged, self._on_tabs_changed),
            (self._tab_manager.tabsChanged, self._on_tabs_changed_sync_sidebar),
            (self._tab_manager.activeTabChanged, self._on_active_tab_changed),
            (self._tab_manager.activeTabChanged, self._on_active_tab_changed_update_nav),
            (self._tab_manager.activeTabChanged, self._on_active_tab_changed_update_app_header),
        ]
        
        # Conectar todas las señales
        for signal, slot in self._tab_manager_connections:
            signal.connect(slot)
        
        # FileViewContainer -> file open handler
        self._file_view_container.open_file.connect(self._on_file_open)
        # FileViewContainer -> sidebar update when folder is moved
        self._file_view_container.folder_moved.connect(self._on_folder_moved)
        
        # Sidebar -> TabManager
        self._sidebar.new_focus_requested.connect(self._on_sidebar_new_focus)
        self._sidebar.folder_selected.connect(self._on_sidebar_folder_selected)
        self._sidebar.focus_remove_requested.connect(self._on_sidebar_remove_focus)
        
        
        # Watcher -> Sidebar (rename externo detectado)
        watcher = self._tab_manager.get_watcher()
        if watcher:
            watcher.folder_renamed.connect(self._sidebar.update_focus_path)
            watcher.folder_disappeared.connect(self._on_folder_disappeared)
            # Resincronización estructural cuando hay moves entre padres
            watcher.structural_change_detected.connect(self._on_structural_change_detected)
        
        # WorkspaceSelector -> WorkspaceManager (delegar)
        self._workspace_selector.workspace_selected.connect(self._on_workspace_selected)
        
        # WorkspaceManager -> MainWindow (actualizar UI)
        self._workspace_manager.workspace_changed.connect(self._on_workspace_changed)

    def _load_app_state(self) -> None:
        """Load complete application state and restore UI."""
        # Backward compatibility: si no hay WorkspaceManager, cargar estado antiguo
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
        
        # Obtener estado del workspace (puede ser None si es workspace nuevo)
        state = self._workspace_manager.get_workspace_state(active_workspace.id)
        
        if state:
            # Cargar estado en TabManager (sin historial)
            self._tab_manager.load_workspace_state({
                'tabs': state.get('tabs', []),
                'active_tab': state.get('active_tab')
            })
            
            # Cargar estado en Sidebar
            self._sidebar.load_workspace_state(
                state.get('focus_tree_paths', []),
                state.get('expanded_nodes', [])
            )
        else:
            # Workspace nuevo sin estado - inicializar vacío
            self._tab_manager.load_workspace_state({
                'tabs': [],
                'active_tab': None
            })
            self._sidebar.load_workspace_state([], [])
        
        # Actualizar AppHeader con nombre del workspace (siempre, incluso si está vacío)
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
        
        # El estado ya fue cargado en switch_workspace(), solo actualizar AppHeader
        # Esto evita recargar el estado dos veces
        self._app_header.update_workspace(workspace.name)

    def _on_tabs_changed(self, tabs: list) -> None:
        """Handle tabs list change from TabManager."""
        if self._is_initializing:
            return
        # Focus Dock handles this automatically via its own TabManager connection
        # Schedule sidebar sync with debounce
        self._schedule_sidebar_sync()

    def _on_active_tab_changed(self, index: int, path: str) -> None:
        """Handle active tab change from TabManager."""
        # FileViewContainer will auto-update via its own TabManager connection
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
            # Las flechas se actualizarán automáticamente vía activeTabChanged signal
    
    def _on_nav_forward_shortcut(self) -> None:
        """Handle Alt+Right keyboard shortcut for forward navigation."""
        if self._tab_manager.can_go_forward():
            self._tab_manager.go_forward()
            # Las flechas se actualizarán automáticamente vía activeTabChanged signal
    
    def _on_files_moved(self, source_path: str, target_path: str) -> None:
        """Handle files moved - refresh affected Focus."""
        import os
        from PySide6.QtCore import QTimer
        
        source_dir = os.path.dirname(source_path)
        active_folder = self._tab_manager.get_active_folder()
        
        # Refresh source folder if it's the active Focus
        if source_dir == active_folder:
            QTimer.singleShot(100, lambda: self._file_view_container._update_files())
        
        # Refresh target folder if it's the active Focus  
        if target_path == active_folder:
            QTimer.singleShot(100, lambda: self._file_view_container._update_files())
    
    def _on_folder_moved(self, old_path: str, new_path: str) -> None:
        """Handle folder moved from file view area - update sidebar."""
        if old_path and new_path:
            self._sidebar.update_focus_path(old_path, new_path)
    
    def _on_folder_disappeared(self, folder_path: str) -> None:
        """Handle folder disappeared (moved outside watched directory) - resync sidebar."""
        import os
        if not folder_path:
            return
        
        normalized_path = os.path.normpath(folder_path)
        
        # Verificar si el path está en el sidebar
        if normalized_path not in self._sidebar._path_to_item:
            return
        
        # Verificar si el path está en los tabs
        tabs = self._tab_manager.get_tabs()
        normalized_tabs = {os.path.normpath(tab) for tab in tabs}
        
        if normalized_path in normalized_tabs:
            # El path está en los tabs pero desapareció del filesystem
            # Esto significa que la carpeta fue movida/reorganizada fuera del directorio observado
            # Resincronizar sidebar completo para reconstruir jerarquía correcta desde tabs actuales
            self._schedule_sidebar_sync(structural=True)
        else:
            # El path no está en tabs pero está en sidebar (nodo huérfano)
            # Eliminar del sidebar
            self._sidebar.remove_focus_path(normalized_path)
    
    def _on_structural_change_detected(self, watched_folder: str) -> None:
        """
        Handle structural changes detected (moves between parents).
        
        Resincroniza el sidebar estructuralmente desde los tabs actuales,
        reconstruyendo la jerarquía desde disco sin usar heurísticas.
        """
        # Use centralized sync method with debounce
        self._schedule_sidebar_sync(structural=True)
    
    def _schedule_sidebar_sync(self, structural: bool = False) -> None:
        """
        Schedule sidebar synchronization with debounce.
        
        Centralized method to sync sidebar with tabs, preventing multiple
        rapid syncs by using a single debounced timer.
        
        Args:
            structural: If True, perform full structural resync from disk.
        """
        from PySide6.QtCore import QTimer
        
        # Create timer if it doesn't exist
        if not hasattr(self, '_sidebar_sync_timer'):
            self._sidebar_sync_timer = QTimer(self)
            self._sidebar_sync_timer.setSingleShot(True)
            self._sidebar_sync_timer.timeout.connect(self._resync_sidebar_from_tabs)
        
        # Store structural flag for the sync operation
        self._pending_structural_sync = structural
        
        # Restart timer with debounce delay
        self._sidebar_sync_timer.stop()
        self._sidebar_sync_timer.start(FILE_SYSTEM_DEBOUNCE_MS)
    
    def _resync_sidebar_from_tabs(self) -> None:
        """
        Resync sidebar tree structure from current tabs - structural resync from disk.
        
        Reconstruye el árbol completo desde los tabs actuales verificando paths desde disco.
        No usa heurísticas: reconstruye nodos afectados desde disco.
        Mantiene tabs y focos, solo actualiza la vista del sidebar.
        
        find_parent_item() buscará el padre correcto basándose en os.path.dirname()
        del path actual de cada tab, reconstruyendo la jerarquía correcta.
        """
        import os
        # Guardar paths expandidos antes de limpiar
        expanded_paths = self._sidebar.get_expanded_paths()
        
        # Deshabilitar actualizaciones durante reconstrucción completa para mayor velocidad
        self._sidebar._tree_view.setUpdatesEnabled(False)
        try:
            # Limpiar sidebar completamente
            all_paths = list(self._sidebar._path_to_item.keys())
            for path in all_paths:
                self._sidebar.remove_focus_path(path)
            
            # Reconstruir desde tabs actuales verificando desde disco
            # No usar heurísticas: verificar cada path desde disco
            tabs = self._tab_manager.get_tabs()
            for tab_path in tabs:
                normalized_tab = os.path.normpath(tab_path)
                # Verificar desde disco que el path existe y es directorio
                if os.path.exists(normalized_tab) and os.path.isdir(normalized_tab):
                    # add_focus_path() usa find_parent_item() que busca el padre desde disco
                    # basándose en os.path.dirname(), reconstruyendo la jerarquía correcta
                    self._sidebar.add_focus_path(normalized_tab)
        finally:
            self._sidebar._tree_view.setUpdatesEnabled(True)
        
        # Restaurar estado expandido para paths que todavía existen
        for path in expanded_paths:
            normalized_path = os.path.normpath(path)
            if normalized_path in self._sidebar._path_to_item:
                item = self._sidebar._path_to_item[normalized_path]
                index = self._sidebar._model.indexFromItem(item)
                if index.isValid():
                    self._sidebar._tree_view.expand(index)

    def _on_file_open(self, file_path: str) -> None:
        """
        Handle file or folder open request from FileViewContainer.
        
        IMPORTANT: When opening folders from Grid:
        - Only activates Focus if folder already exists as a Focus in Dock
        - Does NOT create new Focus - user must use "+" button in Dock
        - This keeps Dock stable and independent from Grid navigation
        """
        import os
        if os.path.isdir(file_path):
            # Delegar en método central para unificar navegación
            self._navigate_to_folder(file_path)
            return
        else:
            # Abrir archivo con la aplicación predeterminada y manejar errores
            from PySide6.QtWidgets import QApplication, QMessageBox
            # Feedback visual breve a nivel de ventana (cursor ocupado)
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(180, QApplication.restoreOverrideCursor)
            success = open_file_with_system(file_path)
            if not success:
                # Aviso amigable si el sistema no tiene asociación para el tipo de archivo
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
        
        # Navegación con flechas (Alt+Left/Right)
        back_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        back_shortcut.activated.connect(self._on_nav_back_shortcut)
        
        forward_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        forward_shortcut.activated.connect(self._on_nav_forward_shortcut)

    def _open_quick_preview(self) -> None:
        """Toggle quick preview window (open/close)."""
        # Si la ventana existe y está visible, cerrarla (toggle)
        if (hasattr(self, "_current_preview_window") and 
            self._current_preview_window and 
            self._current_preview_window.isVisible()):
            self._current_preview_window.close()
            self._current_preview_window = None
            return

        # Si no hay ventana o está cerrada, abrir nueva
        selected = get_selected_files(self._file_view_container)
        if not selected:
            return

        # Filtrar solo archivos de texto e imágenes
        allowed_files = filter_previewable_files(selected)
        if not allowed_files:
            return

        # Pasar lista completa para navegación secuencial
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
        """Handle drag enter - let FileViewContainer handle it, or ignore if DesktopWindow should handle."""
        # Verificar si estamos en Desktop Focus
        from app.services.desktop_path_helper import is_desktop_focus
        active_folder = self._tab_manager.get_active_folder()
        if active_folder and is_desktop_focus(active_folder):
            # Si estamos en Desktop Focus, el DesktopWindow debería manejar esto
            # Pero si el evento llegó aquí, dejamos que FileViewContainer lo maneje
            super().dragEnterEvent(event)
        else:
            # Si no estamos en Desktop Focus, dejar que FileViewContainer maneje normalmente
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move - let FileViewContainer handle it."""
        super().dragMoveEvent(event)
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop - let FileViewContainer handle it, or ignore if DesktopWindow should handle."""
        # Verificar si hay un DesktopWindow visible - si es así, verificar si el cursor está sobre él
        from PySide6.QtWidgets import QApplication
        from app.ui.windows.desktop_window import DesktopWindow
        
        # Buscar DesktopWindow visible y verificar si el cursor está sobre él
        desktop_window_under_cursor = None
        cursor_pos = event.pos()
        global_pos = self.mapToGlobal(cursor_pos)
        
        for widget in QApplication.allWidgets():
            if isinstance(widget, DesktopWindow) and widget.isVisible():
                # Verificar si el cursor global está sobre el DesktopWindow
                desktop_rect = widget.geometry()
                if desktop_rect.contains(global_pos):
                    desktop_window_under_cursor = widget
                    break
        
        if desktop_window_under_cursor:
            # El cursor está sobre el DesktopWindow - rechazar el evento aquí
            # para que el DesktopWindow pueda capturarlo
            logger.debug("dropEvent - cursor sobre DesktopWindow, rechazando para que DesktopWindow lo capture")
            event.ignore()
            return
        
        # Si el cursor no está sobre DesktopWindow, manejar normalmente
        super().dropEvent(event)
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event - save state and cleanup resources."""
        # Stop filesystem watcher
        if hasattr(self._tab_manager, 'get_watcher'):
            watcher = self._tab_manager.get_watcher()
            if watcher:
                watcher.stop_watching()
        
        # Delegar guardado final a WorkspaceManager (MainWindow NO guarda directamente)
        if self._workspace_manager:
            self._workspace_manager.save_current_state(self._tab_manager, self._sidebar)
        else:
            # Backward compatibility: guardar estado antiguo si no hay WorkspaceManager
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
        """
        ÚNICO PUNTO DE ENTRADA para navegación a carpetas.
        
        Este método centraliza TODA la navegación de carpetas en la aplicación.
        Todos los caminos de navegación (sidebar, grid, lista) DEBEN delegar
        en este método para garantizar comportamiento consistente.
        
        Responsabilidades:
        1. Validar permisos de acceso a la carpeta
        2. Determinar si la carpeta es Desktop Focus
        3. Activar tab existente o crear nuevo tab
        4. Establecer explícitamente el estado de Desktop Focus en las vistas
        
        Puntos de entrada que DEBEN usar este método:
        - Sidebar: doble clic en carpeta
        - Grid: doble clic en tile de carpeta
        - Lista: doble clic en fila de carpeta
        - Navegación programática: cualquier código que necesite abrir una carpeta
        
        Regla de diseño:
        NUNCA llamar directamente a TabManager.add_tab() o select_tab() desde
        código de UI. Siempre usar este método para mantener consistencia.
        
        Args:
            folder_path: Ruta de la carpeta a abrir.
        """
        # Validar permisos de lectura antes de navegar
        if not os.access(folder_path, os.R_OK):
            QMessageBox.warning(
                self,
                "Permiso requerido",
                "No se puede acceder a esta carpeta. Verifica permisos."
            )
            return
        
        # Determinar si es Desktop Focus
        is_desktop = is_desktop_focus(folder_path)
        
        # Buscar si la carpeta ya existe como tab (usar normalize_path para comparación consistente)
        tabs = self._tab_manager.get_tabs()
        normalized_path = normalize_path(folder_path)
        tab_index = None
        
        for idx, tab_path in enumerate(tabs):
            normalized_tab = normalize_path(tab_path)
            if normalized_tab == normalized_path:
                tab_index = idx
                break
        
        # Activar tab existente o crear nuevo
        if tab_index is not None:
            self._tab_manager.select_tab(tab_index)
        else:
            self._tab_manager.add_tab(folder_path)
        
        # Actualizar explícitamente el estado de Desktop Focus en FileViewContainer
        # Esto asegura que las vistas sepan correctamente qué carpeta están mostrando
        self._file_view_container.set_desktop_mode(is_desktop)
    
    def _on_sidebar_folder_selected(self, path: str) -> None:
        """Handle folder selection from sidebar - delega en método central."""
        self._navigate_to_folder(path)
    
    def _on_sidebar_remove_focus(self, path: str) -> None:
        """Handle focus removal request from sidebar - solo permite eliminar carpetas raíz."""
        import os
        normalized_path = os.path.normpath(path)
        
        # Verificar que es una carpeta raíz (no tiene padre en el sidebar)
        if normalized_path not in self._sidebar._path_to_item:
            return
        
        item = self._sidebar._path_to_item[normalized_path]
        # Solo eliminar si no tiene padre (es raíz)
        if item.parent() and item.parent() != self._sidebar._model.invisibleRootItem():
            return  # No es raíz, no permitir eliminación
        
        self._tab_manager.remove_tab_by_path(path)
        self._sidebar.remove_focus_path(path)
        try:
            import os
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
            from PySide6.QtWidgets import QToolTip
            from PySide6.QtGui import QCursor
            QToolTip.showText(QCursor.pos(), "Quitado del sidebar")
        except Exception as e:
            logger.debug(f"Failed to show tooltip: {e}")
    
    def _on_tabs_changed_sync_sidebar(self, tabs: list) -> None:
        """Sync sidebar with current tabs."""
        if self._is_initializing:
            return
        # Deshabilitar actualizaciones durante sincronización batch para mayor velocidad
        self._sidebar._tree_view.setUpdatesEnabled(False)
        try:
            for tab_path in tabs:
                self._sidebar.add_focus_path(tab_path)
        finally:
            self._sidebar._tree_view.setUpdatesEnabled(True)
