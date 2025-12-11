"""
Signal handlers for TabManager.

Handles folder change events and watch/emit operations.
"""

from app.services.tab_path_normalizer import normalize_path


def on_folder_changed(
    manager,
    folder_path: str,
    files_changed_signal
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
    watcher,
    active_tab_changed_signal
) -> None:
    """Start watching folder and emit active tab changed signal."""
    if folder_path:
        watcher.watch_folder(folder_path)
    active_tab_changed_signal.emit(active_index, folder_path)

