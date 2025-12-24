"""
FileMoveService - File move operations.

Handles moving files between folders with conflict resolution.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from app.core.logger import get_logger
from app.models.file_operation_result import FileOperationResult
from app.services.file_path_utils import resolve_conflict, validate_file, validate_folder, validate_path

logger = get_logger(__name__)


def move_file(
    source: str,
    destination_folder: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Move a file or folder from source to destination folder.

    Args:
        source: Full path to source file or folder.
        destination_folder: Destination folder path.

    Returns:
        FileOperationResult with success status and error message if failed.
    """
    if not validate_path(source):
        return FileOperationResult.error(f"Source path does not exist: {source}")

    if not validate_folder(destination_folder):
        return FileOperationResult.error(f"Destination folder does not exist: {destination_folder}")

    source_path = Path(source)
    dest_path = Path(destination_folder) / source_path.name

    # Handle destination conflict by appending number
    dest_path = resolve_conflict(dest_path)

    # Block watcher events during move operation
    if watcher and hasattr(watcher, 'ignore_events'):
        watcher.ignore_events(True)
    
    try:
        shutil.move(str(source_path), str(dest_path))
        logger.info(f"Moved file: {source} -> {dest_path}")
        result = FileOperationResult.ok()
    except PermissionError as e:
        logger.error(f"Permission denied moving {source} to {destination_folder}: {e}")
        result = FileOperationResult.error(f"Failed to move: {str(e)}")
    except OSError as e:
        logger.error(f"OS error moving {source} to {destination_folder}: {e}")
        result = FileOperationResult.error(f"Failed to move: {str(e)}")
    except shutil.Error as e:
        logger.error(f"Shutil error moving {source} to {destination_folder}: {e}")
        result = FileOperationResult.error(f"Failed to move: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error moving {source} to {destination_folder}: {e}", exc_info=True)
        result = FileOperationResult.error(f"Failed to move: {str(e)}")
    finally:
        # Unblock watcher events
        if watcher and hasattr(watcher, 'ignore_events'):
            watcher.ignore_events(False)
    
    return result


def copy_file(
    source: str,
    destination_folder: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Copy a file to destination folder (used for file box operations).
    
    Validates that source is a file, then delegates to copy_path().

    Args:
        source: Full path to source file.
        destination_folder: Destination folder path.

    Returns:
        FileOperationResult with success status and error message if failed.
    """
    if not validate_file(source):
        return FileOperationResult.error(f"Source file does not exist: {source}")
    
    return copy_path(source, destination_folder, watcher)


def copy_path(
    source: str,
    destination_folder: str,
    watcher: Optional[object] = None
) -> FileOperationResult:
    """
    Copy a file or folder to destination folder.
    
    Handles both files and folders automatically.
    
    Args:
        source: Full path to source file or folder.
        destination_folder: Destination folder path.
        watcher: Optional watcher to block events during copy.
    
    Returns:
        FileOperationResult with success status and error message if failed.
    """
    if not validate_path(source):
        return FileOperationResult.error(f"Source path does not exist: {source}")
    
    if not validate_folder(destination_folder):
        return FileOperationResult.error(f"Destination folder does not exist: {destination_folder}")
    
    source_path = Path(source)
    dest_path = Path(destination_folder) / source_path.name
    
    # Handle destination conflict by appending number
    dest_path = resolve_conflict(dest_path)
    
    # Block watcher events during copy operation
    if watcher and hasattr(watcher, 'ignore_events'):
        watcher.ignore_events(True)
    
    try:
        # Detect if source is file or folder and copy accordingly
        if os.path.isdir(source):
            # Copy directory recursively
            shutil.copytree(str(source_path), str(dest_path), dirs_exist_ok=True)
            logger.info(f"Copied folder: {source} -> {dest_path}")
        else:
            # Copy file
            shutil.copy2(str(source_path), str(dest_path))
            logger.info(f"Copied file: {source} -> {dest_path}")
        
        result = FileOperationResult.ok()
    except PermissionError as e:
        logger.error(f"Permission denied copying {source} to {destination_folder}: {e}")
        result = FileOperationResult.error(f"Failed to copy: {str(e)}")
    except OSError as e:
        logger.error(f"OS error copying {source} to {destination_folder}: {e}")
        result = FileOperationResult.error(f"Failed to copy: {str(e)}")
    except shutil.Error as e:
        logger.error(f"Shutil error copying {source} to {destination_folder}: {e}")
        result = FileOperationResult.error(f"Failed to copy: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error copying {source} to {destination_folder}: {e}", exc_info=True)
        result = FileOperationResult.error(f"Failed to copy: {str(e)}")
    finally:
        # Unblock watcher events
        if watcher and hasattr(watcher, 'ignore_events'):
            watcher.ignore_events(False)
    
    return result
