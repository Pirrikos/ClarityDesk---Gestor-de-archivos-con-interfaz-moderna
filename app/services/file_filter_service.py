"""
FileFilterService - File filtering operations.

Handles filtering files by extensions and detecting executables.
"""

import os
from typing import List, Set


def is_executable(file_path: str) -> bool:
    """
    Check if a file is a Windows executable (PE file).
    
    Args:
        file_path: Path to the file to check.
        
    Returns:
        True if file appears to be an executable.
    """
    try:
        with open(file_path, 'rb') as f:
            # Check for PE header (MZ signature)
            header = f.read(2)
            if header != b'MZ':
                return False
            
            # Check for PE signature at offset 0x3C
            f.seek(0x3C)
            pe_offset_bytes = f.read(4)
            if len(pe_offset_bytes) != 4:
                return False
            
            pe_offset = int.from_bytes(pe_offset_bytes, 'little')
            f.seek(pe_offset)
            pe_sig = f.read(4)
            
            return pe_sig == b'PE\x00\x00'
    except (OSError, PermissionError, ValueError):
        return False


def filter_files_by_extensions(files: List[str], extensions: Set[str]) -> List[str]:
    """
    Filter files by extensions (includes folders and executables).
    
    Args:
        files: List of file paths.
        extensions: Set of file extensions to filter.
        
    Returns:
        Filtered list of file paths.
    """
    filtered = []
    for item_path in files:
        if os.path.isdir(item_path):
            # Always include folders
            filtered.append(item_path)
        elif os.path.isfile(item_path):
            ext = os.path.splitext(os.path.basename(item_path))[1].lower()
            is_exe = is_executable(item_path) if not ext else False
            
            if ext in extensions:
                filtered.append(item_path)
            elif not ext and is_exe:
                filtered.append(item_path)
    return filtered


def filter_folder_files_by_extensions(
    folder_path: str,
    extensions: Set[str]
) -> List[str]:
    """
    Scan and filter files from a normal folder.
    
    Args:
        folder_path: Path to folder to scan.
        extensions: Set of file extensions to filter.
        
    Returns:
        Filtered list of file paths.
    """
    from app.services.file_scan_service import scan_folder_files
    
    if not folder_path:
        return []
    
    raw_files = scan_folder_files(folder_path)
    return _filter_raw_folder_files(raw_files, extensions)


def _filter_raw_folder_files(raw_files: List[str], extensions: Set[str]) -> List[str]:
    """Filter raw folder files by extensions."""
    filtered = []
    try:
        for item_path in raw_files:
            if os.path.isdir(item_path):
                filtered.append(item_path)
            elif os.path.isfile(item_path):
                ext = os.path.splitext(os.path.basename(item_path))[1].lower()
                is_exe = is_executable(item_path) if not ext else False
                if ext in extensions or (not ext and is_exe):
                    filtered.append(item_path)
    except (OSError, PermissionError):
        return []
    return filtered

