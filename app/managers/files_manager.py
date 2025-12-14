"""
FilesManager - Manager for file operations.

Orchestrates file operations from UI to services.
Coordinates delete, rename, move, restore, and preview operations.
"""

from typing import Optional

from app.services.file_delete_service import delete_file
from app.services.file_move_service import move_file
from app.services.file_rename_service import rename_file
from app.services.rename_service import RenameService
from app.services.trash_operations import restore_from_trash as restore_file_from_trash_service
from app.services.file_open_service import open_file_with_system


class FilesManager:
    """Manager for file operations."""
    
    def __init__(
        self,
        rename_service: RenameService,
        tab_manager=None,
        watcher=None
    ):
        """Initialize FilesManager with services."""
        self._rename_service = rename_service
        self._tab_manager = tab_manager
        self._watcher = watcher
    
    def delete_files(self, paths: list[str], is_trash_focus: bool = False) -> None:
        """Delete files using appropriate service based on context."""
        watcher = self._get_watcher()
        for path in paths:
            delete_file(path, watcher=watcher, is_trash_focus=is_trash_focus)
    
    def rename_file(self, old_path: str, new_name: str) -> bool:
        """Rename a single file."""
        watcher = self._get_watcher()
        result = rename_file(old_path, new_name, watcher=watcher)
        return result.success
    
    def rename_batch(self, file_paths: list[str], new_names: list[str]) -> bool:
        """
        Apply batch rename to multiple files.
        
        Note: For better UX with progress feedback, use rename_file() in a loop
        instead of this method when processing multiple files.
        """
        watcher = self._get_watcher()
        try:
            self._rename_service.apply_rename(file_paths, new_names, watcher=watcher)
            return True
        except RuntimeError:
            return False
    
    def move_files(self, paths: list[str], target_folder: str) -> None:
        """Move files to target folder."""
        watcher = self._get_watcher()
        for path in paths:
            move_file(path, target_folder, watcher=watcher)
    
    def restore_from_trash(self, file_id: str) -> None:
        """Restore file from trash to original location."""
        watcher = self._get_watcher()
        restore_file_from_trash_service(file_id, watcher=watcher)
    
    def open_file_preview(self, path: str) -> None:
        """Open file with system application or preview."""
        open_file_with_system(path)
    
    def _get_watcher(self):
        """Get watcher from TabManager if available."""
        if self._watcher:
            return self._watcher
        if self._tab_manager and hasattr(self._tab_manager, 'get_watcher'):
            return self._tab_manager.get_watcher()
        return None

