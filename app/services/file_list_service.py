"""
FileListService - File listing operations.

Handles listing files from directories with extension filtering.
Supports Desktop Focus and Trash Focus.
Supports file stacking (grouping by type).

This module orchestrates file listing by delegating to:
- file_scan_service.py: File scanning
- file_filter_service.py: Extension filtering
- file_stack_service.py: File stacking
"""

from typing import List, Set, Union

from app.models.file_stack import FileStack
from app.services.file_filter_service import (
    filter_files_by_extensions,
    filter_folder_files_by_extensions,
    is_executable
)
from app.services.file_scan_service import scan_files
from app.services.file_stack_service import create_file_stacks


def get_files(
    folder_path: str,
    extensions: Set[str],
    use_stacks: bool = False
) -> Union[List[str], List[FileStack]]:
    """
    Get filtered file list from folder (includes files and folders).
    Supports Desktop Focus and Trash Focus.
    Supports file stacking (grouping by type).

    Args:
        folder_path: Path to the folder to list (or virtual path).
        extensions: Set of file extensions to filter (e.g., {'.pdf', '.docx'}).
        use_stacks: If True, group files by type into FileStack objects.

    Returns:
        List of file/folder paths OR List of FileStack objects if use_stacks=True.
    """
    if not folder_path:
        return []

    # Get raw file list
    from app.services.desktop_path_helper import is_desktop_focus
    from app.services.trash_storage import TRASH_FOCUS_PATH
    
    if is_desktop_focus(folder_path):
        raw_files = scan_files(folder_path)
        filtered_files = filter_files_by_extensions(raw_files, extensions)
    elif folder_path == TRASH_FOCUS_PATH:
        raw_files = scan_files(folder_path)
        filtered_files = filter_files_by_extensions(raw_files, extensions)
    else:
        # Normal folder: scan and filter in one pass
        filtered_files = filter_folder_files_by_extensions(folder_path, extensions)
    
    # If not using stacks, return sorted flat list
    if not use_stacks:
        return sorted(filtered_files)
    
    # Group files into stacks
    return create_file_stacks(filtered_files, is_executable)
