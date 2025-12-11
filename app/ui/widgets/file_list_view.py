"""
FileListView - List/table view for displaying files.

Shows files in a table with filename, extension, and modified date.
Emits signal on double-click to open file.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from app.managers.tab_manager import TabManager
from app.services.icon_service import IconService
from app.ui.widgets.file_list_handlers import (
    start_drag, drag_enter_event, drag_move_event, drop_event,
    mouse_press_event, on_item_double_clicked, on_checkbox_changed
)
from app.ui.widgets.file_list_renderer import (
    setup_ui, expand_stacks_to_files, refresh_table
)


class FileListView(QTableWidget):
    """Table view widget displaying files as a list."""

    open_file = Signal(str)  # Emitted on double-click (file path)
    file_dropped = Signal(str)  # Emitted when file is dropped (source file path)
    file_deleted = Signal(str)  # Emitted when file is deleted (file path)

    def __init__(
        self,
        icon_service: Optional[IconService] = None,
        filesystem_service: Optional = None,  # Kept for compatibility, not used
        parent=None,
        tab_manager: Optional[TabManager] = None,
        state_manager=None  # Optional FileStateManager instance
    ):
        """Initialize FileListView with empty file list."""
        super().__init__(parent)
        self._files: list[str] = []
        self._icon_service = icon_service or IconService()
        self._tab_manager = tab_manager
        self._checked_paths: set[str] = set()
        # Use provided state manager or create new instance
        try:
            from app.managers.file_state_manager import FileStateManager
            self._state_manager = state_manager or (FileStateManager() if FileStateManager else None)
        except ImportError:
            self._state_manager = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        setup_ui(self, self._on_checkbox_changed, self._on_item_double_clicked)

    def update_files(self, file_list: list) -> None:
        """
        Update displayed files or stacks.
        
        Args:
            file_list: List of file paths OR FileStack objects.
                      Stacks are automatically expanded to show individual files.
        """
        self._files = expand_stacks_to_files(file_list)
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Rebuild table rows from file list."""
        refresh_table(
            self, self._files, self._icon_service,
            self._state_manager, self._checked_paths, self._on_checkbox_changed
        )

    def startDrag(self, supported_actions) -> None:
        """Handle drag start for file copy or move using checkbox selection."""
        start_drag(self, supported_actions, self._icon_service, self.file_deleted)

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter for file drop."""
        drag_enter_event(self, event, self._tab_manager)

    def dragMoveEvent(self, event) -> None:
        """Handle drag move to maintain drop acceptance."""
        drag_move_event(self, event, self._tab_manager)

    def dropEvent(self, event) -> None:
        """Handle file drop into list view."""
        drop_event(self, event, self._tab_manager, self.file_dropped)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press - toggle checkbox with Ctrl+click."""
        mouse_press_event(self, event)

    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click on table row."""
        on_item_double_clicked(self, item, self.open_file)

    def _on_checkbox_changed(self, file_path: str, state: int) -> None:
        """Handle checkbox state change to update selection set."""
        on_checkbox_changed(self, file_path, state)

    def get_selected_paths(self) -> list[str]:
        """Get paths of currently selected files via checkboxes or traditional selection."""
        if self._checked_paths:
            return list(self._checked_paths)
        selected_paths = []
        for item in self.selectedItems():
            if item:
                path = item.data(Qt.ItemDataRole.UserRole)
                if path:
                    selected_paths.append(path)
        return selected_paths

    def set_selected_states(self, state) -> None:
        """
        Set state for all selected files and update display.
        
        Args:
            state: State constant or None to remove state.
        """
        if not self._state_manager:
            return
        
        selected_paths = self.get_selected_paths()
        if not selected_paths:
            return
        
        # Update states in manager
        count = self._state_manager.set_files_state(selected_paths, state)
        
        # Refresh table to update state column
        self._refresh_table()
