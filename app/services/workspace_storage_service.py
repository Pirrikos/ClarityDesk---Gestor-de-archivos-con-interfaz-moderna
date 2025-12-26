"""
WorkspaceStorageService - Workspace persistence.

Handles saving and loading workspaces and their state to/from JSON storage.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.models.workspace import Workspace


def get_storage_dir() -> Path:
    """Get storage directory path."""
    storage_dir = Path(__file__).parent.parent.parent / 'storage'
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


def get_workspaces_file() -> Path:
    """Get path to workspaces metadata file."""
    return get_storage_dir() / 'workspaces.json'


def get_workspace_state_file(workspace_id: str) -> Path:
    """Get path to workspace state file."""
    return get_storage_dir() / f'workspace_{workspace_id}.json'


def load_workspaces() -> List[Workspace]:
    """
    Load all workspaces from JSON storage.
    
    Returns:
        List of Workspace instances.
    """
    workspaces_file = get_workspaces_file()
    workspaces_file_str = str(workspaces_file)
    if not os.path.exists(workspaces_file_str):
        return []
    
    try:
        with open(workspaces_file_str, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        workspaces_list = data.get('workspaces', [])
        workspaces = []
        
        for ws_data in workspaces_list:
            workspace_id = ws_data.get('id')
            if not workspace_id:
                continue
            
            state = load_workspace_state(workspace_id)
            if state is None:
                continue
            
            workspace = Workspace(
                id=workspace_id,
                name=ws_data.get('name', 'Unnamed'),
                tabs=state.get('tabs', []),
                active_tab=state.get('active_tab'),
                focus_tree_paths=state.get('focus_tree_paths', []),
                expanded_nodes=state.get('expanded_nodes', []),
                view_mode=state.get('view_mode', 'grid')
            )
            workspaces.append(workspace)
        
        return workspaces
    except (json.JSONDecodeError, IOError, OSError):
        return []


def save_workspaces(workspaces: List[Workspace], active_workspace_id: Optional[str] = None) -> None:
    """
    Save workspaces metadata to JSON storage.
    
    Args:
        workspaces: List of Workspace instances.
        active_workspace_id: ID of currently active workspace.
    """
    workspaces_file = get_workspaces_file()
    workspaces_file_str = str(workspaces_file)
    
    workspaces_data = []
    for workspace in workspaces:
        workspaces_data.append({
            'id': workspace.id,
            'name': workspace.name,
            'created_at': datetime.now().isoformat()
        })
    
    data = {
        'workspaces': workspaces_data,
        'active_workspace_id': active_workspace_id
    }
    
    try:
        temp_path = workspaces_file_str + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, workspaces_file_str)
    except (IOError, OSError):
        pass


def load_workspace_state(workspace_id: str) -> Optional[dict]:
    """
    Load state of a specific workspace.
    
    Args:
        workspace_id: ID of the workspace.
    
    Returns:
        State dict with keys: tabs, active_tab, focus_tree_paths, expanded_nodes, root_folders_order, view_mode
        or None if file doesn't exist or is invalid.
    """
    state_file = get_workspace_state_file(workspace_id)
    state_file_str = str(state_file)
    if not os.path.exists(state_file_str):
        return None
    
    try:
        with open(state_file_str, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'tabs': data.get('tabs', []),
            'active_tab': data.get('active_tab'),
            'focus_tree_paths': data.get('focus_tree_paths', []),
            'expanded_nodes': data.get('expanded_nodes', []),
            'root_folders_order': data.get('root_folders_order'),
            'view_mode': data.get('view_mode', 'grid')
        }
    except (json.JSONDecodeError, IOError, OSError):
        return None


def save_workspace_state(workspace_id: str, state: dict) -> None:
    """
    Save state of a specific workspace.
    
    Args:
        workspace_id: ID of the workspace.
        state: State dict with keys: tabs, active_tab, focus_tree_paths, expanded_nodes, root_folders_order, view_mode
    """
    state_file = get_workspace_state_file(workspace_id)
    state_file_str = str(state_file)
    
    data = {
        'tabs': state.get('tabs', []),
        'active_tab': state.get('active_tab'),
        'focus_tree_paths': state.get('focus_tree_paths', []),
        'expanded_nodes': state.get('expanded_nodes', []),
        'root_folders_order': state.get('root_folders_order'),
        'view_mode': state.get('view_mode', 'grid')
    }
    
    try:
        temp_path = state_file_str + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, state_file_str)
    except (IOError, OSError):
        pass


def get_active_workspace_id() -> Optional[str]:
    """
    Get ID of active workspace from storage.
    
    Returns:
        Workspace ID or None if not found.
    """
    workspaces_file = get_workspaces_file()
    workspaces_file_str = str(workspaces_file)
    if not os.path.exists(workspaces_file_str):
        return None
    
    try:
        with open(workspaces_file_str, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('active_workspace_id')
    except (json.JSONDecodeError, IOError, OSError):
        return None

