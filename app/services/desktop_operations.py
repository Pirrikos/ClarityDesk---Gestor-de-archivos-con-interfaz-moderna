"""
DesktopOperations - Desktop file operations.

Handles file operations on Windows Desktop (move, rename, list).
Never deletes files - use TrashService for deletion.

This module re-exports all public APIs for backward compatibility.
Actual implementations are in separate modules:
- desktop_operations_scan.py: File scanning and dock detection
- desktop_drag_ops.py: Drag & drop operations
- desktop_visibility.py: File visibility helpers
"""

# Re-export public APIs for backward compatibility
from app.services.desktop_operations_scan import (
    load_desktop_files,
    is_file_in_dock
)
from app.services.desktop_drag_ops import (
    copy_into_dock,
    move_into_desktop,
    move_out_of_desktop,
    rename_desktop_file
)

__all__ = [
    'load_desktop_files',
    'is_file_in_dock',
    'copy_into_dock',
    'move_into_desktop',
    'move_out_of_desktop',
    'rename_desktop_file',
]
