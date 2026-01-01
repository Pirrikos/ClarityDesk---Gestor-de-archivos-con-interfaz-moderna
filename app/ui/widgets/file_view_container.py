"""
FileViewContainer - Container for grid and list file views.

Manages switching between grid and list views.
Subscribes to TabManager to update files when active tab changes.
"""

import os
from time import perf_counter
from typing import TYPE_CHECKING, Optional, List
from app.ui.windows.error_dialog import ErrorDialog

from PySide6.QtCore import QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QResizeEvent
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QProgressDialog,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import (
    ANIMATION_CLEANUP_DELAY_MS,
    ANIMATION_DURATION_MS,
    CENTRAL_AREA_BG,
    CENTRAL_AREA_BG_LIGHT,
    CURSOR_BUSY_TIMEOUT_MS,
    DOUBLE_CLICK_THRESHOLD_MS,
    PROGRESS_DIALOG_THRESHOLD,
    ROUNDED_BG_RADIUS,
    ROUNDED_BG_TOP_OFFSET,
    SELECTION_RESTORE_DELAY_MS,
    SELECTION_UPDATE_INTERVAL_MS,
    UPDATE_DELAY_MS,
)
from app.core.logger import get_logger
from app.managers.files_manager import FilesManager

logger = get_logger(__name__)
from app.managers.file_state_manager import FileStateManager
from app.managers.tab_manager import TabManager
from app.services.desktop_path_helper import is_desktop_focus
from app.services.icon_service import IconService
from app.services.rename_service import RenameService
from app.ui.widgets.file_grid_view import FileGridView
from app.ui.widgets.file_list_view import FileListView
from app.ui.widgets.file_state_migration import migrate_states_on_rename
from app.ui.widgets.file_view_handlers import FileViewHandlers
from app.ui.widgets.file_view_setup import setup_ui
from app.ui.widgets.file_view_sync import (
    update_files, switch_view, get_selected_files, set_selected_states, clear_selection
)
from app.ui.widgets.file_view_tabs import (
    connect_tab_signals, on_active_tab_changed, on_files_changed,
    update_nav_buttons_state, on_nav_back, on_nav_forward
)
from app.ui.widgets.focus_header_panel import FocusHeaderPanel
from app.ui.widgets.view_toolbar import ViewToolbar
from app.ui.utils.rounded_background_painter import paint_rounded_background
from app.ui.windows.bulk_rename_dialog import BulkRenameDialog

if TYPE_CHECKING:
    from app.ui.widgets.app_header import AppHeader
    from app.ui.widgets.workspace_selector import WorkspaceSelector


class FileViewContainer(QWidget):
    """Container widget managing grid and list file views."""

    open_file = Signal(str)
    expansion_height_changed = Signal(int)
    stacks_count_changed = Signal(int)
    folder_moved = Signal(str, str)  # Emitted when folder is moved (old_path, new_path)
    
    def __init__(
        self,
        tab_manager: TabManager,
        icon_service: Optional[IconService] = None,
        filesystem_service: Optional = None,
        parent=None,
        is_desktop: bool = False,
        get_label_callback: Optional = None
    ):
        """
        Initialize FileViewContainer with TabManager and services.
        
        Args:
            tab_manager: TabManager instance.
            icon_service: Optional IconService instance.
            filesystem_service: Deprecated, kept for compatibility.
            parent: Parent widget.
            is_desktop: True if this is desktop mode.
            get_label_callback: Optional callback to get state labels.
        """
        super().__init__(parent)
        self._tab_manager = tab_manager
        self._icon_service = icon_service or IconService()
        self._is_desktop = is_desktop  # Flag explícito del modo, no se infiere
        rename_service = RenameService()
        self._files_manager = FilesManager(rename_service, tab_manager)
        self._current_view: str = "grid"
        self._saved_selections: dict[str, list[str]] = {}  # Store selections per view
        
        self._state_manager = FileStateManager()
        self._get_label_callback = get_label_callback
        self._handlers = FileViewHandlers(tab_manager, lambda: update_files(self))
        self._workspace_selector = None
        self._state_label_manager = None  # Se inyecta desde MainWindow
        self._workspace_manager = None  # Se inyecta desde MainWindow para resolver workspace_name
        
        # Modo búsqueda
        self._is_search_mode = False
        self._search_results: List = []  # List[SearchResult]
        self._file_to_workspace: dict[str, str] = {}  # file_path -> workspace_id
        self._is_navigating = False  # Flag para indicar si estamos en medio de una navegación
        
        self.setAcceptDrops(True)
        if not self._is_desktop:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)

        # Inicializar color del tema desde AppSettings
        from app.managers import app_settings as app_settings_module
        if app_settings_module.app_settings is not None:
            color_theme = app_settings_module.app_settings.central_area_color
            self._theme_color = CENTRAL_AREA_BG_LIGHT if color_theme == "light" else CENTRAL_AREA_BG
        else:
            self._theme_color = CENTRAL_AREA_BG
        
        setup_ui(self)
        connect_tab_signals(self, tab_manager)
        
        # Conectar señal de cambio de tema después de que el objeto esté completamente inicializado
        if app_settings_module.app_settings is not None:
            app_settings_module.app_settings.central_area_color_changed.connect(self._on_theme_changed)
        
        # Conectar señal de cambio de estado para refrescar vista si hay contexto de estado activo
        self._state_manager.state_changed.connect(self._on_state_changed)
        self._state_manager.states_changed.connect(self._on_states_changed)
        
        # Conectar señal de cambio de modo de visualización para estados
        if tab_manager:
            tab_manager.view_mode_changed.connect(self._on_state_view_mode_changed)
        
        self._setup_selection_timer()
        # Umbral anti-doble clic para prevenir aperturas repetidas
        self._last_open_ts_ms: int = 0
        self._open_threshold_ms: int = DOUBLE_CLICK_THRESHOLD_MS
        
        # Warm-up de primer paint: contenedor con vistas ya añadidas, primera activación en siguiente ciclo
        self.setVisible(False)
        QTimer.singleShot(0, self._activate_first_paint)
        
        update_files(self)
        update_nav_buttons_state(self)


    def _activate_first_paint(self) -> None:
        """Activar primera visualización después de estabilizar layout."""
        self.setVisible(True)
    
    def _setup_selection_timer(self) -> None:
        """Setup selection change handlers (event-based, not timer-based)."""
        self._last_selection_count = 0

        # Conectar señales de selección de las vistas para actualizar solo cuando cambie
        # Esto reemplaza el timer periódico que causaba repintados innecesarios
        if self._list_view:
            self._list_view.itemSelectionChanged.connect(self._update_selection_count)
        if self._grid_view and hasattr(self._grid_view, 'selection_changed'):
            self._grid_view.selection_changed.connect(self._update_selection_count)
    
    def _update_selection_count(self) -> None:
        """Update focus panel with current selection count."""
        selected_count = len(get_selected_files(self))
        # Only update if count changed (optimization)
        if selected_count != self._last_selection_count:
            self._last_selection_count = selected_count
            self._focus_panel.update_selection_count(selected_count)
            if self._workspace_selector:
                self._workspace_selector.update_selection_count(selected_count)

    def set_desktop_mode(self, is_desktop: bool) -> None:
        """
        Actualizar explícitamente el estado de Desktop Focus.
        
        Este método asegura que las vistas (grid y lista) sepan correctamente
        si están mostrando Desktop Focus o una carpeta normal.
        
        Args:
            is_desktop: True si la carpeta activa es Desktop Focus, False en caso contrario.
        """
        self._is_desktop = is_desktop
        # Actualizar estado en FileGridView
        # _grid_view siempre existe después de setup_ui() en __init__()
        if self._grid_view:
            self._grid_view.set_desktop_mode(is_desktop)
    
    def _on_active_tab_changed(self, index: int, path: Optional[str]) -> None:
        """
        Handle active tab change from TabManager.
        
        Si path es None, significa que hay contexto de estado activo.
        """
        # Si hay contexto de estado, el modo se restaurará desde la señal view_mode_changed
        if path is None:
            # Vista por estado activa - el modo se restaurará automáticamente
            on_active_tab_changed(self, index, path or "")
        else:
            # Actualizar estado de Desktop Focus basado en el path del tab activo
            if index >= 0 and path:
                is_desktop = is_desktop_focus(path)
                self.set_desktop_mode(is_desktop)
            
            on_active_tab_changed(self, index, path)
    
    def _on_files_changed(self) -> None:
        """Handle filesystem change event - only refresh if already in a tab."""
        on_files_changed(self)

    def _on_focus_cleared(self) -> None:
        """Handle focus cleared - clean up views when active focus is removed."""
        self.clear_current_focus()
    
    def clear_current_focus(self, skip_render: bool = False) -> None:
        """
        Clear current focus - reset grid and list views to empty state.
        
        Args:
            skip_render: Si True, solo limpia los datos sin renderizar (útil cuando
                        inmediatamente se van a cargar nuevos datos).
        """
        # Limpiar selección visual en ambas vistas
        clear_selection(self)
        
        # Limpiar datos pero no renderizar si skip_render=True
        if skip_render:
            # Solo limpiar datos internos sin disparar render
            self._grid_view._files = []
            self._grid_view._stacks = []
            self._grid_view._expanded_stacks = {}
            self._grid_view._previous_files = None
            self._list_view._files = []
        else:
            # Limpiar y renderizar (caso normal cuando no hay tab activo)
            self._grid_view.update_files([])
            self._list_view.update_files([])
        
        # Reset navigation buttons
        self._update_nav_buttons_state()

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter as fallback."""
        if self._is_search_mode:
            event.ignore()
            return
        self._handlers.handle_drag_enter(event)

    def dragMoveEvent(self, event) -> None:
        """Handle drag move as fallback."""
        if self._is_search_mode:
            event.ignore()
            return
        self._handlers.handle_drag_move(event)

    def dropEvent(self, event) -> None:
        """Handle file drop as fallback."""
        if self._is_search_mode:
            event.ignore()
            return
        self._handlers.handle_drop(event)

    def _on_open_file(self, file_path: str) -> None:
        """Aplicar prevención de doble clic y feedback visual, luego emitir open_file."""
        now_ms = int(perf_counter() * 1000)
        if self._last_open_ts_ms and (now_ms - self._last_open_ts_ms) < self._open_threshold_ms:
            # Ignorar doble clics dentro del umbral para evitar ejecuciones duplicadas
            return
        self._last_open_ts_ms = now_ms
        # Feedback visual: cursor ocupado breve para indicar acción en curso
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        QTimer.singleShot(CURSOR_BUSY_TIMEOUT_MS, QApplication.restoreOverrideCursor)
        self.open_file.emit(file_path)
    
    def _animate_content_transition(self) -> None:
        """
        Aplicar animación de opacidad breve al área de contenido.
        
        NOTA: Desactivado temporalmente para evitar transparencias hacia el escritorio
        en ventanas translúcidas durante la navegación.
        """
        return
        try:
            target = self._stacked
            if not isinstance(target, QWidget):
                return
            effect = QGraphicsOpacityEffect(target)
            target.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity", self)
            anim.setDuration(ANIMATION_DURATION_MS)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.start()
            # Limpiar efecto tras la animación
            QTimer.singleShot(ANIMATION_CLEANUP_DELAY_MS, lambda: target.setGraphicsEffect(None))
        except Exception as e:
            logger.debug(f"Failed to animate focus highlight: {e}")
    
    def _on_expansion_height_changed(self, height: int) -> None:
        """Forward expansion height change signal."""
        self.expansion_height_changed.emit(height)
    
    def _on_stacks_count_changed(self, count: int) -> None:
        """Forward stacks count change signal."""
        self.stacks_count_changed.emit(count)
    
    def _on_rename_clicked(self) -> None:
        """Handle rename button click."""
        selected_files = get_selected_files(self)
        if len(selected_files) < 1:
            return

        # Sort files Finder-style: folders first, then files, both alphabetically (case-insensitive)
        selected_files = sorted(
            selected_files,
            key=lambda p: (not os.path.isdir(p), os.path.basename(p).lower())
        )

        dialog = BulkRenameDialog(selected_files, self)
        dialog.rename_applied.connect(self._on_rename_applied)
        dialog.exec()
    
    def _on_rename_applied(self, old_paths: list[str], new_names: list[str]) -> None:
        """Handle rename operation completion."""
        try:
            if self._state_manager:
                migrate_states_on_rename(self._state_manager, old_paths, new_names)
            
            self._process_renames_with_progress(old_paths, new_names)

            # 🔴 MUY IMPORTANTE: invalidar selección y estado previo
            self._clear_selection_after_rename()

            self._refresh_after_rename()
        except RuntimeError as e:
            self._show_rename_error(str(e))
    
    def _process_renames_with_progress(self, old_paths: list[str], new_names: list[str]) -> None:
        """Process renames with progress feedback for multiple files."""
        progress = self._create_progress_dialog_if_needed(len(old_paths))

        for i, (old_path, new_name) in enumerate(zip(old_paths, new_names)):
            if progress and progress.wasCanceled():
                break
            self._update_progress(progress, i, old_path)
            self._rename_single_file(old_path, new_name)

        if progress:
            progress.setValue(len(old_paths))
            progress.close()  # Close explicitly to prevent orphan window flash
    
    def _create_progress_dialog_if_needed(self, file_count: int) -> Optional[QProgressDialog]:
        """Create progress dialog if file count exceeds threshold."""
        if file_count <= PROGRESS_DIALOG_THRESHOLD:
            return None

        progress = QProgressDialog("Renombrando archivos...", "Cancelar", 0, file_count, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)  # Only show if operation takes >500ms
        # Don't call show() - let QProgressDialog decide based on minimumDuration
        return progress
    
    def _update_progress(self, progress: Optional[QProgressDialog], index: int, file_path: str) -> None:
        """Update progress dialog with current file."""
        if progress:
            progress.setValue(index)
            progress.setLabelText(f"Renombrando: {os.path.basename(file_path)}")
            QApplication.processEvents()  # Keep UI responsive
    
    def _rename_single_file(self, old_path: str, new_name: str) -> None:
        """Rename a single file, raising exception on failure."""
        success = self._files_manager.rename_file(old_path, new_name)
        if not success:
            raise RuntimeError(f"No se pudo renombrar '{os.path.basename(old_path)}'")
    
    def _clear_selection_after_rename(self) -> None:
        """Clear selection and invalidate rename-related UI state.

        Use the stable `clearSelection()` API on views — we added minimal aliases
        so FileViewContainer can call the same method on both views.
        """
        # Llamar siempre a la API estable `clearSelection()` cuando esté disponible
        if self._grid_view and hasattr(self._grid_view, "clearSelection"):
            self._grid_view.clearSelection()
        if self._list_view and hasattr(self._list_view, "clearSelection"):
            self._list_view.clearSelection()

        # Resetear contador de selección
        self._last_selection_count = 0

    def _refresh_after_rename(self) -> None:
        """Refresh file views after rename operation."""
        update_files(self)
        QTimer.singleShot(UPDATE_DELAY_MS, lambda: update_files(self))
    
    def _show_rename_error(self, error_msg: str) -> None:
        """Show user-friendly error message for rename failures."""
        user_friendly_msg = (
            f"No se pudieron renombrar todos los archivos:\n\n{error_msg}\n\n"
            "Por favor, verifica los nombres e intenta nuevamente."
        )
        error_dialog = ErrorDialog(
            parent=self,
            title="Error al renombrar",
            message=user_friendly_msg,
            is_warning=False
        )
        error_dialog.exec()

    def _on_state_button_clicked(self, state: str) -> None:
        """Handle state button click from toolbar."""
        selected_files = get_selected_files(self)
        if not selected_files:
            return
        set_selected_states(self, state)
    
    def _on_state_changed(self, file_path: str, state: Optional[str]) -> None:
        """Manejar cambio de estado de un archivo."""
        current_state_context = self._tab_manager.get_state_context() if self._tab_manager.has_state_context() else None
        
        if current_state_context:
            item_exists = self._item_exists_in_current_view(file_path)
            will_match_filter = state == current_state_context
            
            if item_exists != will_match_filter:
                self._force_full_refresh()
                QTimer.singleShot(0, lambda: update_files(self))
            elif item_exists:
                self._update_item_visual(file_path, state)
        else:
            self._update_item_visual(file_path, state)
    
    def _item_exists_in_current_view(self, file_path: str) -> bool:
        """Verificar si un item existe en la vista actual."""
        if self._current_view == "grid":
            return self._grid_view._tile_manager and \
                   self._grid_view._tile_manager.get_tile(file_path) is not None
        return file_path in self._list_view._files
    
    def _force_full_refresh(self) -> None:
        """Limpiar estado del diff incremental para forzar refresh completo."""
        if self._current_view == "grid":
            self._grid_view._grid_state = {}
            self._grid_view._previous_files = None
    
    def _update_item_visual(self, file_path: str, state: Optional[str]) -> None:
        """Actualizar badge visual en la vista actual."""
        if self._current_view == "grid":
            self._grid_view.update_tile_state_visual(file_path, state)
        else:
            self._list_view.update_item_state_visual(file_path, state)
    
    def _on_states_changed(self, changes: list) -> None:
        """Manejar cambio de estados de múltiples archivos."""
        if not self._tab_manager or not changes:
            return
        
        current_state_context = self._tab_manager.get_state_context() if self._tab_manager.has_state_context() else None
        needs_full_refresh = False
        
        if current_state_context:
            for file_path, new_state in changes:
                item_exists = self._item_exists_in_current_view(file_path)
                will_match_filter = new_state == current_state_context
                
                if item_exists != will_match_filter:
                    self._force_full_refresh()
                    needs_full_refresh = True
                    break
        
        if needs_full_refresh:
            QTimer.singleShot(0, lambda: update_files(self))
        else:
            for file_path, new_state in changes:
                if self._item_exists_in_current_view(file_path):
                    self._update_item_visual(file_path, new_state)
            
            if current_state_context:
                self._list_view.refresh_state_labels(current_state_context)
            else:
                affected_states = {new_state for _, new_state in changes if new_state}
                for state_id in affected_states:
                    self._list_view.refresh_state_labels(state_id)
    
    def _on_state_view_mode_changed(self, view_mode: str) -> None:
        """
        Manejar cambio de modo de visualización para vista por estado.
        
        Restaura el modo guardado cuando se activa un estado.
        
        Args:
            view_mode: Modo de visualización ("grid" o "list").
        """
        from app.ui.widgets.file_view_sync import switch_view
        switch_view(self, view_mode)

    def _update_nav_buttons_state(self) -> None:
        """Update navigation buttons enabled state."""
        update_nav_buttons_state(self)
    
    def set_header(self, header: Optional['AppHeader']) -> None:
        """Inyectar referencia al AppHeader para control de navegación y estilos.
        
        Permite que la lógica existente actualice el estado de flechas y estilos
        de botones de vista delegando en el header cuando no hay toolbar interna.
        """
        self._header = header
    
    def set_workspace_selector(self, workspace_selector: Optional['WorkspaceSelector']) -> None:
        """Inyectar referencia al WorkspaceSelector para actualización de botones."""
        self._workspace_selector = workspace_selector
    
    def set_state_label_manager(self, state_label_manager) -> None:
        """
        Inyectar StateLabelManager y conectar señal para refrescar labels.
        
        Cuando se renombra un label de estado, todas las vistas deben actualizarse
        inmediatamente sin necesidad de reconstruir completamente.
        """
        self._state_label_manager = state_label_manager
        if state_label_manager:
            state_label_manager.state_label_changed.connect(self._on_state_label_changed)
    
    def set_workspace_manager(self, workspace_manager) -> None:
        """
        Inyectar WorkspaceManager para resolver workspace_name en UI.

        Necesario para mostrar el nombre del workspace en resultados de búsqueda.
        """
        self._workspace_manager = workspace_manager

        # También inyectar en FileListView si existe
        if hasattr(self, '_list_view') and self._list_view:
            self._list_view._workspace_manager = workspace_manager
    
    def set_search_mode(self, enabled: bool, results: List = None) -> None:
        """
        Activar/desactivar modo búsqueda y mostrar resultados.
        
        Args:
            enabled: True para activar modo búsqueda, False para restaurar vista normal
            results: Lista de SearchResult cuando enabled=True, None cuando enabled=False
        """
        was_search_mode = self._is_search_mode
        self._is_search_mode = enabled
        
        if results is not None:
            self._search_results = results if enabled else []
            # Crear mapa file_path -> workspace_id para acceso rápido
            if enabled:
                self._file_to_workspace = {result.file_path: result.workspace_id for result in results}
            else:
                self._file_to_workspace = {}
        else:
            self._search_results = []
            self._file_to_workspace = {}
        
        if enabled and self._search_results:
            # Mostrar resultados de búsqueda
            file_paths = [result.file_path for result in self._search_results]
            self._grid_view.update_files(file_paths)
            self._list_view.update_files(file_paths)
        elif not enabled and was_search_mode:
            # Restaurar vista normal solo si estábamos en modo búsqueda
            # Si estamos navegando, NO recargar aquí - la navegación lo hará
            # Si NO estamos navegando (ej: borrar texto de búsqueda), restaurar la vista
            if not getattr(self, '_is_navigating', False):
                update_files(self)
    
    def get_workspace_id_for_file(self, file_path: str) -> Optional[str]:
        """
        Obtener workspace_id para un archivo (solo en modo búsqueda).
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            workspace_id si está en modo búsqueda, None en caso contrario
        """
        if self._is_search_mode:
            return self._file_to_workspace.get(file_path)
        return None
    
    def get_workspace_name_for_file(self, file_path: str) -> Optional[str]:
        """
        Obtener nombre del workspace para un archivo (solo en modo búsqueda).
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Nombre del workspace si está en modo búsqueda, None en caso contrario
        """
        if self._is_search_mode and self._workspace_manager:
            workspace_id = self._file_to_workspace.get(file_path)
            if workspace_id:
                workspace = self._workspace_manager.get_workspace(workspace_id)
                if workspace:
                    return workspace.name
        return None
    
    def _on_state_label_changed(self, state_id: str) -> None:
        """
        Manejar cambio de label de estado - refrescar solo el texto visible.
        
        No reconstruye las vistas, solo actualiza el texto de los badges/cells existentes.
        """
        if self._grid_view:
            self._grid_view.refresh_state_labels(state_id)
        if self._list_view:
            self._list_view.refresh_state_labels(state_id)
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Propagar resize."""
        super().resizeEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Pintar fondo redondeado y refuerzo sólido."""
        if self._is_desktop:
            super().paintEvent(event)
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg_color = QColor(self._theme_color)
        
        # REFUERZO: Llenar todo el rect con color sólido para evitar parpadeos
        painter.fillRect(self.rect(), bg_color)
        
        widget_rect = self.rect().adjusted(0, 0, -1, -1)
        
        # Pintar el redondeado
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(widget_rect, ROUNDED_BG_RADIUS, ROUNDED_BG_RADIUS)
        
        painter.end()
        super().paintEvent(event)
    
    def _on_theme_changed(self, color_theme: str) -> None:
        """Actualizar color del tema cuando cambia."""
        from app.core.constants import CENTRAL_AREA_BG, CENTRAL_AREA_BG_LIGHT
        self._theme_color = CENTRAL_AREA_BG_LIGHT if color_theme == "light" else CENTRAL_AREA_BG
        self.update()  # Forzar repintado
    
    def closeEvent(self, event) -> None:
        """Cleanup handlers before closing."""
        if hasattr(self, '_handlers') and hasattr(self._handlers, 'cleanup'):
            self._handlers.cleanup()
        super().closeEvent(event)

