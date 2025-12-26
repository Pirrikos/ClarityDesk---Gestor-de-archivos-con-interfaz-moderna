"""
Signal handlers for TabManager.

Handles folder change events and watch/emit operations.
"""

from typing import TYPE_CHECKING

from app.services.path_utils import is_state_context_path, normalize_path

if TYPE_CHECKING:
    from PySide6.QtCore import Signal
    from app.managers.tab_manager import TabManager
    from app.services.filesystem_watcher_service import FileSystemWatcherService


def on_folder_changed(
    manager: "TabManager",
    folder_path: str,
    files_changed_signal: "Signal"
) -> None:
    """
    Handle folder change event from watcher.
    
    Watcher already handles debounce and snapshot comparison,
    so we just emit the signal.
    """
    # Only process if it's the active folder (normalize for comparison)
    normalized_path = normalize_path(folder_path)
    active_folder = manager.get_active_folder()
    if active_folder and normalize_path(active_folder) == normalized_path:
        # Emit signal - watcher already filtered duplicates
        files_changed_signal.emit()


def watch_and_emit(
    folder_path: str,
    active_index: int,
    watcher: "FileSystemWatcherService",
    active_tab_changed_signal: "Signal"
) -> None:
    """
    Start watching folder and emit active tab changed signal.
    
    IMPORTANTE: No observa paths virtuales (contextos de estado).
    Los contextos de estado NO son paths del filesystem.
    
    NAVEGACIÓN: Este método emite activeTabChanged que dispara refresh de la vista derecha.
    """
    if folder_path and not is_state_context_path(folder_path):
        # Solo observar paths físicos, no contextos de estado
        watcher.watch_folder(folder_path)
    active_tab_changed_signal.emit(active_index, folder_path)

