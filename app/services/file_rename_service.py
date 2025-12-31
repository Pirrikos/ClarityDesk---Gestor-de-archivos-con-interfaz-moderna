"""
FileRenameService - File rename operations.

Handles renaming files with conflict resolution.
Supports Desktop Focus (uses DesktopRealService).
Handles case-only renames on Windows with two-step process.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from app.core.logger import get_logger
from app.models.file_operation_result import FileOperationResult
from app.services.desktop_path_helper import is_desktop_focus
from app.services.desktop_operations import rename_desktop_file
from app.services.file_path_utils import resolve_conflict, validate_path

logger = get_logger(__name__)


def rename_file(
    file_path: str,
    new_name: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Rename a file safely, handling conflicts and case-only renames.
    Supports Desktop Focus (uses DesktopRealService).

    Args:
        file_path: Full path to the file to rename.
        new_name: New filename (without path).
        watcher: Optional watcher to block events during rename.

    Returns:
        FileOperationResult with success status and error message if failed.
    """
    if not validate_path(file_path):
        return FileOperationResult.error(f"Path does not exist: {file_path}")

    if not new_name or not new_name.strip():
        return FileOperationResult.error("New name cannot be empty")

    # Sanitize new name to prevent path traversal
    new_name = os.path.basename(new_name.strip())
    if not new_name:
        return FileOperationResult.error("Invalid new name")

    # Handle Desktop Focus specially
    file_dir = os.path.dirname(os.path.abspath(file_path))
    if is_desktop_focus(file_dir):
        return rename_desktop_file(file_path, new_name, watcher=watcher)

    source_path = Path(file_path)
    dest_path = source_path.parent / new_name

    # Check if it's exactly the same name (no change at all)
    if source_path.parent == dest_path.parent and source_path.name == dest_path.name:
        return FileOperationResult.ok()

    # Detect case-only rename: same parent, same name ignoring case, but different case
    is_case_only_rename = (
        source_path.parent == dest_path.parent and
        source_path.name.casefold() == dest_path.name.casefold() and
        source_path.name != dest_path.name
    )

    is_dir = source_path.is_dir()

    # Block watcher for:
    # - Normal folder renames (structural changes with child paths)
    # - Case-only renames (both files and folders) to hide two-step temporary file
    should_block_watcher = (
        watcher and
        hasattr(watcher, "ignore_events") and
        (is_case_only_rename or (is_dir and not is_case_only_rename))
    )

    if should_block_watcher:
        watcher.ignore_events(True)

    try:
        if is_case_only_rename:
            # Case-only rename: use two-step process for Windows
            result = _rename_case_only(source_path, dest_path, is_dir)

            # Emit folder_renamed signal manually for case-only folder renames
            # The watcher won't detect it reliably due to two-step process
            if result.success and is_dir and watcher and hasattr(watcher, 'folder_renamed'):
                watcher.folder_renamed.emit(str(source_path), str(dest_path))
                logger.info(f"Emitted folder_renamed signal: {source_path} -> {dest_path}")
        else:
            # Normal rename: handle conflict resolution
            dest_path = resolve_conflict(dest_path)
            source_path.rename(dest_path)
            logger.info(f"Renamed {'folder' if is_dir else 'file'}: {file_path} -> {dest_path}")
            result = FileOperationResult.ok()
    except PermissionError as e:
        logger.error(f"Permission denied renaming {file_path} to {new_name}: {e}")
        result = FileOperationResult.error(f"Failed to rename file: {str(e)}")
    except OSError as e:
        logger.error(f"OS error renaming {file_path} to {new_name}: {e}")
        result = FileOperationResult.error(f"Failed to rename file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error renaming {file_path} to {new_name}: {e}", exc_info=True)
        result = FileOperationResult.error(f"Failed to rename file: {str(e)}")
    finally:
        if should_block_watcher:
            watcher.ignore_events(False)

    return result


def _rename_case_only(source_path: Path, dest_path: Path, is_dir: bool) -> FileOperationResult:
    """
    Handle case-only rename using two-step process for Windows.

    Args:
        source_path: Original path.
        dest_path: Destination path (same name, different case).
        is_dir: Whether the path is a directory.

    Returns:
        FileOperationResult indicating success or failure.
    """
    # Step 1: Rename to temporary name
    temp_name = f"_tmp_cd_{tempfile.mkstemp()[1].split(os.sep)[-1]}"
    temp_path = source_path.parent / temp_name

    try:
        # First rename: original -> temp
        source_path.rename(temp_path)
        logger.info(f"Case-only rename step 1: {source_path} -> {temp_path}")

        # Step 2: Rename to final name with correct case
        temp_path.rename(dest_path)
        logger.info(f"Case-only rename step 2: {temp_path} -> {dest_path}")
        logger.info(f"Renamed {'folder' if is_dir else 'file'} (case-only): {source_path.name} -> {dest_path.name}")

        return FileOperationResult.ok()

    except Exception as e:
        # If something fails, try to restore original name
        if temp_path.exists():
            try:
                temp_path.rename(source_path)
                logger.warning(f"Restored original name after failed case-only rename: {source_path}")
            except Exception as restore_error:
                logger.error(f"Failed to restore original name: {restore_error}")

        logger.error(f"Failed case-only rename: {e}")
        raise
