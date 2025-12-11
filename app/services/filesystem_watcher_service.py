"""
FileSystemWatcherService - Real-time folder monitoring service.

Wraps QFileSystemWatcher to monitor folder changes with debounce,
event blocking, and snapshot comparison to prevent refresh storms.
"""

import os
from typing import Optional

from PySide6.QtCore import QObject, QFileSystemWatcher, QTimer, Signal


class FileSystemWatcherService(QObject):
    """Service for monitoring folder changes in real-time."""

    filesystem_changed = Signal(str)  # Emitted when folder changes (folder path)

    def __init__(self, parent=None, debounce_delay: int = 200):
        """
        Initialize FileSystemWatcherService.
        
        Args:
            parent: Parent QObject.
            debounce_delay: Debounce delay in milliseconds (default 200ms).
        """
        super().__init__(parent)
        self._watcher = QFileSystemWatcher(self)
        self._watched_folder: Optional[str] = None
        self._ignore_events: bool = False
        self._debounce_delay = debounce_delay
        self._previous_snapshot: Optional[list[tuple[str, float]]] = None
        
        # Debounce timer
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._on_debounce_timeout)
        
        # Connect watcher signals
        self._watcher.directoryChanged.connect(self._on_directory_changed)
        self._watcher.fileChanged.connect(self._on_file_changed)

    def watch_folder(self, folder_path: str) -> bool:
        """
        Start watching a folder for changes.

        ALWAYS stops previous watcher before adding new one.
        Only watches the active folder.

        Args:
            folder_path: Path to the folder to watch.

        Returns:
            True if watching started successfully, False otherwise.
        """
        # ALWAYS stop watching previous folder first
        self.stop_watching()

        if not folder_path:
            return False

        # Clear previous snapshot when changing folders
        # Set to empty list (not None) to indicate we have an initial snapshot
        # but don't want to emit on first change detection
        self._previous_snapshot = []

        # Add folder to watcher
        if self._watcher.addPath(folder_path):
            self._watched_folder = folder_path
            # Take initial snapshot but don't emit - this is just for comparison
            self._previous_snapshot = self._take_snapshot(folder_path)
            return True
        return False

    def stop_watching(self) -> None:
        """Stop watching the current folder and clear state."""
        if self._watched_folder:
            self._watcher.removePath(self._watched_folder)
            self._watched_folder = None
        
        # Stop debounce timer
        self._debounce_timer.stop()
        
        # Clear snapshot
        self._previous_snapshot = None

    def get_watched_folder(self) -> Optional[str]:
        """Get the currently watched folder path."""
        return self._watched_folder

    def ignore_events(self, ignore: bool) -> None:
        """
        Set flag to ignore filesystem events.
        
        Used during internal operations (move, rename) to prevent
        refresh loops.
        
        Args:
            ignore: True to ignore events, False to allow.
        """
        self._ignore_events = ignore

    def _take_snapshot(self, folder_path: str) -> list[tuple[str, float]]:
        """
        Take lightweight snapshot of folder contents.
        
        Returns list of (filename, mtime) tuples.
        
        Args:
            folder_path: Path to folder.
            
        Returns:
            List of (filename, mtime) tuples.
        """
        snapshot = []
        try:
            if not os.path.isdir(folder_path):
                return snapshot
            
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                try:
                    mtime = os.path.getmtime(item_path)
                    snapshot.append((item, mtime))
                except (OSError, PermissionError):
                    # Skip items we can't access
                    pass
        except (OSError, PermissionError):
            # Folder doesn't exist or no permission
            pass
        
        # Sort for consistent comparison
        snapshot.sort()
        return snapshot

    def _snapshots_equal(self, snapshot1: list[tuple[str, float]], snapshot2: list[tuple[str, float]]) -> bool:
        """
        Compare two snapshots for equality.
        
        Args:
            snapshot1: First snapshot.
            snapshot2: Second snapshot.
            
        Returns:
            True if snapshots are equal, False otherwise.
        """
        if len(snapshot1) != len(snapshot2):
            return False
        
        return snapshot1 == snapshot2

    def _on_directory_changed(self, path: str) -> None:
        """Handle directory change event."""
        # Only process if it's the watched folder
        if path != self._watched_folder:
            return
        
        # Ignore if events are blocked
        if self._ignore_events:
            return
        
        # Restart debounce timer
        self._debounce_timer.stop()
        self._debounce_timer.start(self._debounce_delay)

    def _on_file_changed(self, path: str) -> None:
        """Handle file change event."""
        # Only process if we have a watched folder
        if not self._watched_folder:
            return
        
        # Ignore if events are blocked
        if self._ignore_events:
            return
        
        # Restart debounce timer
        self._debounce_timer.stop()
        self._debounce_timer.start(self._debounce_delay)

    def _on_debounce_timeout(self) -> None:
        """
        Handle debounce timeout - check snapshot and emit if changed.

        Only emits filesystem_changed if snapshot actually changed.
        Does NOT emit on first snapshot (when folder is first watched).
        """
        if not self._watched_folder:
            return

        # Take new snapshot
        current_snapshot = self._take_snapshot(self._watched_folder)

        # Compare with previous snapshot
        # Empty list means initial snapshot - don't emit, just set it
        if self._previous_snapshot == []:
            # First snapshot after watch_folder - don't emit, just store it
            self._previous_snapshot = current_snapshot
            return

        # Only emit if snapshot changed (and we have a previous snapshot)
        if self._previous_snapshot and not self._snapshots_equal(self._previous_snapshot, current_snapshot):
            self._previous_snapshot = current_snapshot
            self.filesystem_changed.emit(self._watched_folder)

