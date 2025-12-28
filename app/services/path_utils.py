"""
PathUtils - Basic path normalization utilities.

Pure utility functions for path normalization.
No dependencies on other app modules to avoid circular imports.
"""

import os
from typing import List, Optional


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


def filter_system_paths_from_list(paths: List[str]) -> List[str]:
    """
    Filtrar rutas del Escritorio/Clarity de una lista.
    
    Excluye rutas que apuntan al Escritorio del sistema o la carpeta Clarity
    y todas sus subcarpetas.
    
    Args:
        paths: Lista de rutas a filtrar.
    
    Returns:
        Lista filtrada sin rutas del sistema.
    """
    from app.services.desktop_path_helper import is_system_desktop
    return [path for path in paths if not is_system_desktop(path)]


def filter_system_paths_from_state(state: dict) -> dict:
    """
    Filtrar rutas del Escritorio/Clarity de un estado completo.
    
    Filtra las siguientes listas si existen:
    - tabs / open_tabs
    - focus_tree_paths
    - expanded_nodes
    - root_folders_order
    - history
    
    Ajusta active_tab si es una ruta del sistema (lo establece como None).
    Preserva todos los demás campos del estado sin modificar.
    
    Args:
        state: Diccionario de estado con rutas a filtrar.
    
    Returns:
        Diccionario de estado con rutas del sistema filtradas.
    """
    from app.services.desktop_path_helper import is_system_desktop
    
    filtered = {}
    
    # Filtrar listas de paths
    if 'tabs' in state:
        filtered['tabs'] = filter_system_paths_from_list(state['tabs'])
    if 'open_tabs' in state:
        filtered['open_tabs'] = filter_system_paths_from_list(state['open_tabs'])
    if 'focus_tree_paths' in state:
        filtered['focus_tree_paths'] = filter_system_paths_from_list(state['focus_tree_paths'])
    if 'expanded_nodes' in state:
        filtered['expanded_nodes'] = filter_system_paths_from_list(state['expanded_nodes'])
    if 'history' in state:
        filtered['history'] = filter_system_paths_from_list(state['history'])
    if 'root_folders_order' in state:
        filtered['root_folders_order'] = filter_system_paths_from_list(state['root_folders_order']) if state['root_folders_order'] else None
    
    # Ajustar active_tab si es ruta del sistema
    active_tab = state.get('active_tab')
    if active_tab and is_system_desktop(active_tab):
        filtered['active_tab'] = None
    elif 'active_tab' in state:
        filtered['active_tab'] = active_tab
    
    # Copiar resto de campos sin modificar
    for key in state:
        if key not in filtered:
            filtered[key] = state[key]
    
    return filtered
