"""
FileViewContainer - Container for grid and list file views.

Manages switching between grid and list views.
Subscribes to TabManager to update files when active tab changes.
"""

from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.managers.files_manager import FilesManager
from app.managers.file_state_manager import FileStateManager
from app.managers.tab_manager import TabManager
from app.models.file_stack import FileStack
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
    connect_tab_signals, on_active_tab_changed, update_nav_buttons_state,
    on_nav_back, on_nav_forward
)
from app.ui.widgets.focus_header_panel import FocusHeaderPanel
from app.ui.widgets.view_toolbar import ViewToolbar
from app.ui.windows.bulk_rename_dialog import BulkRenameDialog


class FileViewContainer(QWidget):
    """Container widget managing grid and list file views."""

    open_file = Signal(str)
    expansion_height_changed = Signal(int)
    stacks_count_changed = Signal(int)
    
    def __init__(
        self,
        tab_manager: TabManager,
        icon_service: Optional[IconService] = None,
        filesystem_service: Optional = None,
        parent=None
    ):
        """Initialize FileViewContainer with TabManager and services."""
        super().__init__(parent)
        self._tab_manager = tab_manager
        self._icon_service = icon_service or IconService()
        rename_service = RenameService()
        self._files_manager = FilesManager(rename_service, tab_manager)
        self._current_view: str = "grid"
        
        self._state_manager = FileStateManager()
        self._handlers = FileViewHandlers(tab_manager, self._update_files)
        
        self.setAcceptDrops(True)
        setup_ui(self)
        connect_tab_signals(self, tab_manager)
        self._setup_selection_timer()
        update_files(self)
        update_nav_buttons_state(self)


    def _setup_selection_timer(self) -> None:
        """Setup timer to periodically update selection count."""
        self._selection_timer = QTimer(self)
        self._selection_timer.timeout.connect(self._update_selection_count)
        self._selection_timer.start(200)
    
    def _update_selection_count(self) -> None:
        """Update focus panel with current selection count."""
        selected_count = len(get_selected_files(self))
        self._focus_panel.update_selection_count(selected_count)

    def _on_active_tab_changed(self, index: int, path: str) -> None:
        """Handle active tab change from TabManager."""
        on_active_tab_changed(self, index, path)
    
    def _on_files_changed(self) -> None:
        """Handle filesystem change event - only refresh if already in a tab."""
        from app.ui.widgets.file_view_tabs import on_files_changed
        on_files_changed(self)

    def _on_focus_cleared(self) -> None:
        """Handle focus cleared - clean up views when active focus is removed."""
        self.clear_current_focus()
    
    def clear_current_focus(self) -> None:
        """Clear current focus - reset grid and list views to empty state."""
        # Clear both grid and list views
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

    def _update_files(self) -> None:
        """Update both views with files from active tab."""
        update_files(self)
    
    def _check_if_desktop_window(self) -> bool:
        """Check if this container is inside a DesktopWindow."""
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == 'DesktopWindow':
                return True
            parent = parent.parent()
        return False
    
    def _on_stack_expand_requested(self, file_stack: FileStack) -> None:
        """Handle stack expansion - handled directly in FileGridView now."""
        pass
    
    def _on_expansion_height_changed(self, height: int) -> None:
        """Forward expansion height change signal."""
        self.expansion_height_changed.emit(height)
    
    def _on_stacks_count_changed(self, count: int) -> None:
        """Forward stacks count change signal."""
        self.stacks_count_changed.emit(count)

    def get_selected_files(self) -> list[str]:
        """Get paths of currently selected files in the active view."""
        return get_selected_files(self)
    
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
            
            success = self._files_manager.rename_batch(old_paths, new_names)
            if not success:
                raise RuntimeError("Error al renombrar archivos")
            
            update_files(self)
            QTimer.singleShot(300, lambda: update_files(self))
        except RuntimeError as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_state_button_clicked(self, state: str) -> None:
        """Handle state button click from toolbar."""
        selected_files = get_selected_files(self)
        if not selected_files:
            return
        set_selected_states(self, state)

    def _update_nav_buttons_state(self) -> None:
        """Update navigation buttons enabled state."""
        update_nav_buttons_state(self)
    
    def _on_files_dropped_on_focus(self, folder_path: str, file_paths: list) -> None:
        """Handle files dropped on Focus dock - move files to Focus root."""
        import os
        from app.services.file_move_service import move_file
        from app.services.desktop_path_helper import is_desktop_focus
        from app.services.desktop_operations import move_out_of_desktop
        
        if not os.path.isdir(folder_path):
            return
        
        # Get watcher from TabManager if available
        watcher = None
        if self._tab_manager and hasattr(self._tab_manager, 'get_watcher'):
            watcher = self._tab_manager.get_watcher()
        
        # Move each file to Focus root
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
            
            # Check if file is from Desktop Focus
            file_dir = os.path.dirname(os.path.abspath(file_path))
            if is_desktop_focus(file_dir):
                result = move_out_of_desktop(file_path, folder_path, watcher=watcher)
            else:
                result = move_file(file_path, folder_path, watcher=watcher)
            
            if result.success:
                # Emit deleted signal to update view
                self._grid_view.file_deleted.emit(file_path)
                self._list_view.file_deleted.emit(file_path)
