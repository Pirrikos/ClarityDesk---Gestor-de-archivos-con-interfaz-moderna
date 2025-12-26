"""
SearchService - Global search service for workspaces.

Searches files by name across all open tabs in all workspaces.
Uses data already available in memory, does not scan filesystem in real-time.
"""

from typing import List, Set
from dataclasses import dataclass
import os

from app.services.file_list_service import get_files
from app.services.file_extensions import SUPPORTED_EXTENSIONS
from app.services.path_utils import normalize_path


@dataclass
class SearchResult:
    """Search result with domain data only."""
    file_path: str
    workspace_id: str


def search_in_workspaces(query: str, workspace_manager) -> List[SearchResult]:
    """
    Search files by name across all workspaces.
    
    Only searches in open folders (tabs) of each workspace.
    Uses data already available in memory, does not scan filesystem.
    
    Args:
        query: Text to search (case-insensitive, searches in filename)
        workspace_manager: WorkspaceManager instance
        
    Returns:
        List of SearchResult with matching files (max 1000)
    """
    if not query or not query.strip():
        return []
    
    query_lower = query.strip().lower()
    results = []
    seen_paths: Set[str] = set()  # Usar set para deduplicación por path normalizado
    MAX_RESULTS = 1000
    
    workspaces = workspace_manager.get_workspaces()
    
    for workspace in workspaces:
        state = workspace_manager.get_workspace_state(workspace.id)
        tabs = state.get('tabs', []) if state else []
        
        for folder_path in tabs:
            if len(results) >= MAX_RESULTS:
                break
            
            try:
                files = get_files(folder_path, SUPPORTED_EXTENSIONS, use_stacks=False)
                
                for file_path in files:
                    if len(results) >= MAX_RESULTS:
                        break
                    
                    # Normalizar path para deduplicación
                    normalized_path = normalize_path(file_path)
                    
                    # Si ya fue añadido, saltar este archivo
                    if normalized_path in seen_paths:
                        continue
                    
                    filename = os.path.basename(file_path).lower()
                    if query_lower in filename:
                        seen_paths.add(normalized_path)
                        results.append(SearchResult(
                            file_path=file_path,
                            workspace_id=workspace.id
                        ))
            except Exception:
                continue
    
    return results

