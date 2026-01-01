"""
TabManagerInit - Initialization helper for TabManager.

Extracted from tab_manager to reduce file size.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer

from app.services.filesystem_watcher_service import FileSystemWatcherService


def setup_watcher_and_timer(tab_manager, debounce_delay: int = 200):
    """
    Setup filesystem watcher with built-in debounce.
    
    Args:
        tab_manager: TabManager instance.
        debounce_delay: Debounce delay in milliseconds (default 200ms).
        
    Returns:
        Tuple of (watcher, None, None) - timer is now internal to watcher.
    """
    watcher = FileSystemWatcherService(tab_manager, debounce_delay=debounce_delay)
    watcher.filesystem_changed.connect(tab_manager._on_folder_changed)
    
    # Timer is now internal to watcher, return None placeholders
    return watcher, None, None


def get_storage_path(storage_path: Optional[str]) -> Path:
    """Get storage path, defaulting to tabs.json in storage folder."""
    if storage_path is None:
        from pathlib import Path as PathLib
        storage_path = PathLib(__file__).parent.parent.parent / 'storage' / 'tabs.json'
    path = Path(storage_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

