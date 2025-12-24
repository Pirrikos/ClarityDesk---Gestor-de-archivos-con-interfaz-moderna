"""
FileViewContainer - Container for grid and list file views.

Manages switching between grid and list views.
Subscribes to TabManager to update files when active tab changes.
"""

import os
from time import perf_counter
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QMessageBox,
    QProgressDialog,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import (
    ANIMATION_CLEANUP_DELAY_MS,
    ANIMATION_DURATION_MS,
    CURSOR_BUSY_TIMEOUT_MS,
    DOUBLE_CLICK_THRESHOLD_MS,
    PROGRESS_DIALOG_THRESHOLD,
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
    update_files, switch_view, get_selected_files, set_selected_states
)
from app.ui.widgets.file_view_tabs import (
    connect_tab_signals, on_active_tab_changed, on_files_changed,
    update_nav_buttons_state, on_nav_back, on_nav_forward
)
from app.ui.widgets.focus_header_panel import FocusHeaderPanel
from app.ui.widgets.view_toolbar import ViewToolbar
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
        is_desktop: bool = False
    ):
        """Initialize FileViewContainer with TabManager and services."""
        super().__init__(parent)
        self._tab_manager = tab_manager
        self._icon_service = icon_service or IconService()
        self._is_desktop = is_desktop  # Flag explícito del modo, no se infiere
        rename_service = RenameService()
        self._files_manager = FilesManager(rename_service, tab_manager)
        self._current_view: str = "grid"
        self._saved_selections: dict[str, list[str]] = {}  # Store selections per view
        
        self._state_manager = FileStateManager()
        self._handlers = FileViewHandlers(tab_manager, lambda: update_files(self))
        self._workspace_selector = None
        
        self.setAcceptDrops(True)
        setup_ui(self)
        connect_tab_signals(self, tab_manager)
        self._setup_selection_timer()
        # Umbral anti-doble clic para prevenir aperturas repetidas
        self._last_open_ts_ms: int = 0
        self._open_threshold_ms: int = DOUBLE_CLICK_THRESHOLD_MS
        update_files(self)
        update_nav_buttons_state(self)


    def _setup_selection_timer(self) -> None:
        """Setup timer to periodically update selection count."""
        self._selection_timer = QTimer(self)
        self._selection_timer.timeout.connect(self._update_selection_count)
        self._last_selection_count = 0
        self._selection_timer.start(SELECTION_UPDATE_INTERVAL_MS)
    
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
    
    def _on_active_tab_changed(self, index: int, path: str) -> None:
        """Handle active tab change from TabManager."""
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
        self._handlers.handle_drag_enter(event)

    def dragMoveEvent(self, event) -> None:
        """Handle drag move as fallback."""
        self._handlers.handle_drag_move(event)

    def dropEvent(self, event) -> None:
        """Handle file drop as fallback."""
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
        """Aplicar animación de opacidad breve al área de contenido."""
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
        
        dialog = BulkRenameDialog(selected_files, self)
        dialog.rename_applied.connect(self._on_rename_applied)
        dialog.exec()
    
    def _on_rename_applied(self, old_paths: list[str], new_names: list[str]) -> None:
        """Handle rename operation completion."""
        try:
            if self._state_manager:
                migrate_states_on_rename(self._state_manager, old_paths, new_names)
            
            self._process_renames_with_progress(old_paths, new_names)
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
    
    def _create_progress_dialog_if_needed(self, file_count: int) -> Optional[QProgressDialog]:
        """Create progress dialog if file count exceeds threshold."""
        if file_count <= PROGRESS_DIALOG_THRESHOLD:
            return None
        
        progress = QProgressDialog("Renombrando archivos...", "Cancelar", 0, file_count, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)  # Show immediately
        progress.show()
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
        QMessageBox.critical(self, "Error al renombrar", user_friendly_msg)

    def _on_state_button_clicked(self, state: str) -> None:
        """Handle state button click from toolbar."""
        selected_files = get_selected_files(self)
        if not selected_files:
            return
        set_selected_states(self, state)

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
    
    def closeEvent(self, event) -> None:
        """Cleanup timers before closing."""
        if hasattr(self, '_selection_timer') and self._selection_timer.isActive():
            self._selection_timer.stop()
        if hasattr(self, '_handlers') and hasattr(self._handlers, 'cleanup'):
            self._handlers.cleanup()
        super().closeEvent(event)

