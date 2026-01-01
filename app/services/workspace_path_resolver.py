"""
WorkspacePathResolver - Resolver workspace for file paths.

Resuelve a qué workspace pertenece un archivo o carpeta dado su path.
Útil para mostrar el workspace de origen cuando se navega por estados.
"""

import os
from typing import Optional

from app.models.path_utils import normalize_path


def resolve_workspace_for_path(file_path: str, workspace_manager) -> Optional[str]:
    """
    Resolver el workspace al que pertenece un archivo o carpeta.

    Algoritmo:
    1. Normalizar el path del archivo
    2. Para cada workspace, verificar si el archivo está dentro de algún tab o focus_tree_path
    3. Retornar el ID del primer workspace que contenga el archivo

    Args:
        file_path: Path del archivo o carpeta
        workspace_manager: Instancia de WorkspaceManager

    Returns:
        ID del workspace que contiene el archivo, o None si no se encuentra
    """
    if not workspace_manager:
        return None

    normalized_file = normalize_path(file_path)

    # Obtener todos los workspaces
    workspaces = workspace_manager.get_workspaces()

    for workspace in workspaces:
        # Verificar tabs (carpetas raíz)
        for tab_path in workspace.tabs:
            normalized_tab = normalize_path(tab_path)

            # Verificar si el archivo ES el tab o está dentro de él
            if normalized_file == normalized_tab or normalized_file.startswith(normalized_tab + os.sep):
                return workspace.id

        # Verificar focus_tree_paths (todas las carpetas en el árbol del sidebar)
        for tree_path in workspace.focus_tree_paths:
            normalized_tree = normalize_path(tree_path)

            # Verificar si el archivo ES el path del árbol o está dentro de él
            if normalized_file == normalized_tree or normalized_file.startswith(normalized_tree + os.sep):
                return workspace.id

    return None


def get_workspace_name_for_path(file_path: str, workspace_manager) -> Optional[str]:
    """
    Obtener el nombre del workspace al que pertenece un archivo o carpeta.

    Args:
        file_path: Path del archivo o carpeta
        workspace_manager: Instancia de WorkspaceManager

    Returns:
        Nombre del workspace que contiene el archivo, o None si no se encuentra
    """
    workspace_id = resolve_workspace_for_path(file_path, workspace_manager)

    if not workspace_id:
        return None

    workspace = workspace_manager.get_workspace(workspace_id)

    if workspace:
        return workspace.name

    return None
