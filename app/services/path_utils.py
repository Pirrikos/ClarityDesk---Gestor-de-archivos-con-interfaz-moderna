"""
PathUtils (Service) - Utilidades de rutas para servicios.

Centraliza funciones relacionadas con rutas usadas por servicios.
normalize_path e is_virtual_path se importan desde app.models.path_utils para
evitar duplicación y respetar separación de capas.
"""

import os
from typing import List, Optional
from app.models.path_utils import normalize_path, is_virtual_path


#
# normalize_path e is_virtual_path ahora provienen de app.models.path_utils
#


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
