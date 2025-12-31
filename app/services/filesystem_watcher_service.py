"""
FileSystemWatcherService - Real-time folder monitoring service.

Wraps QFileSystemWatcher to monitor folder changes with debounce,
event blocking, and snapshot comparison to prevent refresh storms.
"""

import os
from typing import Optional

from app.core.constants import FILE_SYSTEM_DEBOUNCE_MS
from app.services.path_utils import is_state_context_path
from PySide6.QtCore import QObject, QFileSystemWatcher, QTimer, Signal


class FileSystemWatcherService(QObject):
    """Service for monitoring folder changes in real-time."""

    filesystem_changed = Signal(str)  # Emitted when folder changes (folder path)
    folder_renamed = Signal(str, str)  # Emitted when folder is renamed/moved (old_path, new_path)
    folder_disappeared = Signal(str)  # Emitted when folder disappears without replacement (folder_path)
    structural_change_detected = Signal(str)  # Emitted when structural changes detected (moves between parents)
    folder_created = Signal(str)  # Emitted when folder is created (folder_path)
    folder_deleted = Signal(str)  # Emitted when folder is deleted (folder_path)

    def __init__(self, parent=None, debounce_delay: int = FILE_SYSTEM_DEBOUNCE_MS):
        """
        Initialize FileSystemWatcherService.
        
        Args:
            parent: Parent QObject.
            debounce_delay: Debounce delay in milliseconds (default from constants).
        """
        super().__init__(parent)
        self._watcher = QFileSystemWatcher(self)
        self._watched_folder: Optional[str] = None
        self._ignore_events: bool = False
        self._debounce_delay = debounce_delay
        self._previous_snapshot: Optional[list[tuple[str, float, bool, int]]] = None
        
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

        IMPORTANTE: Los contextos de estado (@state://...) NO son paths del filesystem.
        NO se observan. Se retorna True sin observar.

        Args:
            folder_path: Path to the folder to watch.

        Returns:
            True if watching started successfully, False otherwise.
        """
        # ALWAYS stop watching previous folder first
        self.stop_watching()

        if not folder_path:
            return False
        
        # REGLA CRÍTICA: Ignorar paths virtuales de estado
        if is_state_context_path(folder_path):
            return True  # Retornar True sin observar

        # Add folder to watcher
        if self._watcher.addPath(folder_path):
            self._watched_folder = folder_path
            # Take initial snapshot - this is the baseline for comparison
            # Any change from this point will emit filesystem_changed
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
        
        Temporarily ignore filesystem events during controlled operations.
        Se usa para evitar tormentas de eventos mientras se renombra una carpeta.
        """
        self._ignore_events = bool(ignore)
        if ignore and self._debounce_timer.isActive():
            self._debounce_timer.stop()

    def _take_snapshot(self, folder_path: str) -> list[tuple[str, float, bool, int]]:
        """
        Take lightweight snapshot of folder contents.

        Returns list of (filename, mtime, is_dir, size) tuples.

        Args:
            folder_path: Path to folder.

        Returns:
            List of (filename, mtime, is_dir, size) tuples.
        """
        from app.core.logger import get_logger
        logger = get_logger(__name__)

        snapshot = []
        try:
            if not os.path.isdir(folder_path):
                logger.debug(f"Watcher snapshot: path is not a directory: {folder_path}")
                return snapshot

            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                try:
                    stat = os.stat(item_path)
                    mtime = stat.st_mtime
                    is_dir = os.path.isdir(item_path)
                    size = stat.st_size
                    snapshot.append((item, mtime, is_dir, size))
                except (OSError, PermissionError):
                    # Skip items we can't access
                    pass
        except (OSError, PermissionError):
            # Folder doesn't exist or no permission
            pass

        # Sort for consistent comparison
        snapshot.sort()

        logger.debug(f"Watcher snapshot: {len(snapshot)} items in '{folder_path}'")

        return snapshot

    def _snapshots_equal(self, snapshot1: list[tuple], snapshot2: list[tuple]) -> bool:
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
    
    def _detect_folder_rename(
        self,
        old_snapshot: list[tuple[str, float, bool, int]],
        new_snapshot: list[tuple[str, float, bool, int]],
        watched_folder: str
    ) -> Optional[tuple[str, str]]:
        """
        Detect folder rename by comparing snapshots.
        
        Detects safe renames: exactly 1 folder disappeared and 1 folder appeared in same directory.
        No heuristics (size, mtime) - only pattern matching.
        
        Args:
            old_snapshot: Previous snapshot.
            new_snapshot: Current snapshot.
            watched_folder: Path to watched folder.
            
        Returns:
            Tuple of (old_path, new_path) if rename detected, None otherwise.
        """
        # Extract only folders from snapshots (ignore files)
        old_folders = {name for name, mtime, is_dir, size in old_snapshot if is_dir}
        new_folders = {name for name, mtime, is_dir, size in new_snapshot if is_dir}
        
        # Find folders that disappeared and appeared
        disappeared = old_folders - new_folders
        appeared = new_folders - old_folders
        
        # Safe rename: exactly 1 disappeared and 1 appeared in same directory
        if len(disappeared) == 1 and len(appeared) == 1:
            old_name = disappeared.pop()
            new_name = appeared.pop()
            old_path = os.path.join(watched_folder, old_name)
            new_path = os.path.join(watched_folder, new_name)
            return (old_path, new_path)
        
        return None
    
    def _detect_disappeared_folders(
        self,
        old_snapshot: list[tuple[str, float, bool, int]],
        new_snapshot: list[tuple[str, float, bool, int]],
        watched_folder: str
    ) -> list[str]:
        """
        Detect folders that disappeared without replacement.
        
        Used to detect folders moved outside the watched directory.
        
        Args:
            old_snapshot: Previous snapshot.
            new_snapshot: Current snapshot.
            watched_folder: Path to watched folder.
            
        Returns:
            List of folder paths that disappeared.
        """
        # Extract only folders from snapshots (ignore files)
        old_folders = {name for name, mtime, is_dir, size in old_snapshot if is_dir}
        new_folders = {name for name, mtime, is_dir, size in new_snapshot if is_dir}
        
        # Find folders that disappeared
        disappeared = old_folders - new_folders
        
        # Return full paths for disappeared folders
        disappeared_paths = []
        for folder_name in disappeared:
            folder_path = os.path.join(watched_folder, folder_name)
            # Verify it doesn't exist anymore
            if not os.path.exists(folder_path):
                disappeared_paths.append(folder_path)
        
        return disappeared_paths
    
    def _detect_appeared_folders(
        self,
        old_snapshot: list[tuple[str, float, bool, int]],
        new_snapshot: list[tuple[str, float, bool, int]],
        watched_folder: str
    ) -> list[str]:
        """Detect folders that appeared (were created)."""
        old_folders = {name for name, mtime, is_dir, size in old_snapshot if is_dir}
        new_folders = {name for name, mtime, is_dir, size in new_snapshot if is_dir}
        
        appeared = new_folders - old_folders
        appeared_paths = []
        for folder_name in appeared:
            folder_path = os.path.join(watched_folder, folder_name)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                appeared_paths.append(folder_path)
        
        return appeared_paths
    
    def _has_structural_changes(
        self,
        old_snapshot: list[tuple[str, float, bool, int]],
        new_snapshot: list[tuple[str, float, bool, int]]
    ) -> bool:
        """
        Detect if there are structural changes that require sidebar resync.
        
        Structural changes are changes that cannot be mapped to simple renames:
        - Multiple folders disappeared/appeared (not 1:1 rename)
        - Changes that indicate moves between parents
        
        Args:
            old_snapshot: Previous snapshot.
            new_snapshot: Current snapshot.
            
        Returns:
            True if structural changes detected, False otherwise.
        """
        # Extract only folders from snapshots (ignore files)
        old_folders = {name for name, mtime, is_dir, size in old_snapshot if is_dir}
        new_folders = {name for name, mtime, is_dir, size in new_snapshot if is_dir}
        
        # Find folders that disappeared and appeared
        disappeared = old_folders - new_folders
        appeared = new_folders - old_folders
        
        # Structural change: multiple changes or asymmetric changes (not simple 1:1 rename)
        # Simple rename is handled by _detect_folder_rename, so if we're here it's structural
        if len(disappeared) != len(appeared) or len(disappeared) != 1:
            # Multiple changes or asymmetric = structural change
            return len(disappeared) > 0 or len(appeared) > 0
        
        return False

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
        Detects folder rename/move and emits folder_renamed signal.
        """
        from app.core.logger import get_logger
        logger = get_logger(__name__)

        logger.debug(f"Watcher debounce timeout: ignore_events={self._ignore_events}, watched_folder={self._watched_folder}")

        if self._ignore_events:
            logger.debug("Watcher: skipping, events are being ignored")
            return
        if not self._watched_folder:
            logger.debug("Watcher: skipping, no watched folder")
            return

        # Take new snapshot
        current_snapshot = self._take_snapshot(self._watched_folder)

        # Only process if snapshot changed (and we have a previous snapshot)
        if self._previous_snapshot is not None and not self._snapshots_equal(self._previous_snapshot, current_snapshot):
            logger.debug("Watcher: snapshot changed, processing changes")
            # Try to detect folder rename/move (simple rename in same directory)
            rename_info = self._detect_folder_rename(
                self._previous_snapshot,
                current_snapshot,
                self._watched_folder
            )

            if rename_info:
                old_path, new_path = rename_info
                logger.info(f"Watcher detected folder rename: '{old_path}' -> '{new_path}'")
                self.folder_renamed.emit(old_path, new_path)
            else:
                # Detect folders that disappeared without replacement (moved outside watched directory)
                disappeared_folders = self._detect_disappeared_folders(
                    self._previous_snapshot,
                    current_snapshot,
                    self._watched_folder
                )
                for folder_path in disappeared_folders:
                    self.folder_deleted.emit(folder_path)
                    self.folder_disappeared.emit(folder_path)
                
                # Detect folders that appeared (were created)
                appeared_folders = self._detect_appeared_folders(
                    self._previous_snapshot,
                    current_snapshot,
                    self._watched_folder
                )
                for folder_path in appeared_folders:
                    self.folder_created.emit(folder_path)
                
                # Detect structural changes (moves between parents, multiple changes)
                # Si hay cambios que no son renames simples, requiere resincronización estructural
                if self._has_structural_changes(
                    self._previous_snapshot,
                    current_snapshot
                ):
                    self.structural_change_detected.emit(self._watched_folder)
            
            self._previous_snapshot = current_snapshot
            self.filesystem_changed.emit(self._watched_folder)
