"""
PathUtils - Basic path normalization utilities.

Pure utility functions for path normalization.
No dependencies on other app modules to avoid circular imports.
"""

import os
from typing import Optional


def is_virtual_path(path: str) -> bool:
    """
    Check if path is virtual (does not exist in filesystem).
    
    Virtual paths include Desktop Focus, Trash Focus, and state contexts.
    Only checks known strings to avoid recursion. Does not verify if a real path is Desktop.
    
    Args:
        path: String to check.
        
    Returns:
        True if known virtual path, False otherwise.
    """
    if not path or not isinstance(path, str):
        return False
    
    if path.startswith("@state://"):
        return True
    
    # No llamar a is_desktop_focus() aquí porque causa recursión (necesita normalize_path)
    if path == "__CLARITY_DESKTOP__" or path == "__CLARITY_TRASH__":
        return True
    
    return False


def normalize_path(path: str) -> str:
    """
    Normalize path using normcase and normpath.
    
    Ensures consistent path comparison regardless of case or trailing slashes.
    Virtual paths are not normalized and returned as-is.
    
    Args:
        path: Path string to normalize.
        
    Returns:
        Normalized path string, or empty string if input is empty/invalid.
    """
    if not path:
        return ""
    
    if is_virtual_path(path):
        return path
    
    return os.path.normcase(os.path.normpath(path))


def is_state_context_path(path: str) -> bool:
    """
    Check if path is a state context logical identifier.
    
    State contexts are not filesystem paths and should not be normalized or validated.
    
    Args:
        path: String to check.
        
    Returns:
        True if state context (@state://...), False otherwise.
    """
    if not path or not isinstance(path, str):
        return False
    return path.startswith("@state://")


def extract_state_from_context(context: str) -> Optional[str]:
    """
    Extract state name from state context.
    
    Example: "@state://pending" -> "pending"
    
    Args:
        context: State context (must start with "@state://").
        
    Returns:
        State name if valid, None otherwise.
    """
    if not is_state_context_path(context):
        return None
    
    state = context.replace("@state://", "", 1)
    return state if state else None

