"""
PathUtils - Basic path normalization utilities.

Pure utility functions for path normalization.
No dependencies on other app modules to avoid circular imports.
"""

import os


def normalize_path(path: str) -> str:
    """
    Normalize path using normcase and normpath.
    
    Ensures consistent path comparison regardless of case or trailing slashes.
    Validates empty strings and returns empty string for invalid input.
    
    Args:
        path: Path string to normalize.
        
    Returns:
        Normalized path string, or empty string if input is empty/invalid.
    """
    if not path:
        return ""
    return os.path.normcase(os.path.normpath(path))

