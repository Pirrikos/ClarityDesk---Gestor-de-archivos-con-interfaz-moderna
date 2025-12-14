"""
FileViewHandlers - Event handlers for FileViewContainer.

Handles drag/drop, file operations, and view switching.
"""

from typing import TYPE_CHECKING, Callable, Optional

from PySide6.QtCore import QObject, QTimer

from app.core.constants import FILE_SYSTEM_DEBOUNCE_MS
from app.ui.widgets.file_drop_handler import (
    handle_drag_enter,
    handle_drag_move,
    handle_drop,
    handle_file_drop,
)

if TYPE_CHECKING:
    from app.managers.tab_manager import TabManager


class FileViewHandlers:
    """Event handlers for FileViewContainer."""
    
    def __init__(
        self, 
        tab_manager: 'TabManager', 
        update_files_callback: Callable[[], None],
        parent: Optional[QObject] = None
    ):
        """
        Initialize handlers.
        
        Args:
            tab_manager: TabManager instance.
            update_files_callback: Callback to update files.
            parent: Optional parent QObject for auto-cleanup.
        """
        self._tab_manager = tab_manager
        self._update_files = update_files_callback
        self._pending_update_timer = QTimer(parent)  # With parent for auto-cleanup
        self._pending_update_timer.setSingleShot(True)
        self._pending_update_timer.timeout.connect(self._update_files)
    
    def handle_drag_enter(self, event) -> None:
        """Handle drag enter event."""
        handle_drag_enter(event, self._tab_manager)
    
    def handle_drag_move(self, event) -> None:
        """Handle drag move event."""
        handle_drag_move(event, self._tab_manager)
    
    def handle_drop(self, event) -> None:
        """Handle drop event."""
        handle_drop(event, self._tab_manager, self._update_files)
    
    def handle_file_dropped(self, source_file_path: str) -> tuple[bool, str, str]:
        """Handle file drop into active folder."""
        return handle_file_drop(source_file_path, self._tab_manager, self._update_files)
    
    def handle_file_deleted(self, file_path: str) -> None:
        """
        Handle file deletion (after drag out).
        
        Groups multiple deletions together (e.g., when dragging entire stack)
        to avoid multiple unnecessary updates. Updates once after a short delay.
        """
        # Stop any pending timer and restart it
        # This groups multiple file_deleted signals into a single update
        self._pending_update_timer.stop()
        self._pending_update_timer.start(FILE_SYSTEM_DEBOUNCE_MS)
    
    def cleanup(self) -> None:
        """Cleanup timer before destruction."""
        if hasattr(self, '_pending_update_timer') and self._pending_update_timer.isActive():
            self._pending_update_timer.stop()

