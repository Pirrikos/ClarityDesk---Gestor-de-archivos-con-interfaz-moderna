"""
IconPathUtils - Common utilities for icon directory paths.

Centralizes icon directory resolution to avoid duplication.
"""

import os


def get_icons_dir() -> str:
    """
    Get icons directory path.
    
    Returns:
        Path to assets/icons directory.
    """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "icons")


