"""
WorkspaceService - Workspace root path configuration.

Provides workspace root directory path for tree navigation.

Dormant feature:

Workspace root definition for future Explorer mode.
"""

import os
from pathlib import Path


def get_workspace_root() -> str:
    """
    Get workspace root directory path.
    
    Returns workspace root (e.g., C:/PROYECTOS).
    Falls back to project parent directory if default doesn't exist.
    
    Returns:
        Workspace root path as string.
    """
    # Default workspace path
    default_workspace = "C:/PROYECTOS"
    
    # Check if default exists
    if os.path.isdir(default_workspace):
        return default_workspace
    
    # Fallback: use project parent directory
    # Project is in: .../PROYECTOS/PROY ORDEN PC/ClarityDesk_29-11-25
    # Workspace should be: .../PROYECTOS
    try:
        project_path = Path(__file__).parent.parent.parent
        parent_path = project_path.parent.parent
        if os.path.isdir(str(parent_path)):
            return str(parent_path)
    except Exception:
        pass
    
    # Final fallback: return default even if doesn't exist
    # User can configure manually via set_root_path()
    return default_workspace

