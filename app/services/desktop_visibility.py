"""
DesktopVisibility - Desktop file visibility helpers.

Handles detection of system files and hidden files.
"""

import os


def is_system_file(file_path: str) -> bool:
    """Check if file is a system file that should always be hidden."""
    try:
        basename = os.path.basename(file_path)
        
        # Check dot-prefix (Unix convention, also common on Windows)
        if basename.startswith('.'):
            return True
        
        # Known system files to always hide
        system_files = {'desktop.ini', 'thumbs.db', '.ds_store'}
        if basename.lower() in system_files:
            return True
        
        return False
    except Exception:
        return False


def is_hidden_file(item_path: str) -> bool:
    """Check if file is hidden (Windows attribute or dot-prefix)."""
    if os.path.basename(item_path).startswith('.'):
        return True
    try:
        file_stat = os.stat(item_path)
        if hasattr(file_stat, 'st_file_attributes'):
            if file_stat.st_file_attributes & 0x2:  # FILE_ATTRIBUTE_HIDDEN
                return True
    except (OSError, AttributeError):
        pass
    return False

