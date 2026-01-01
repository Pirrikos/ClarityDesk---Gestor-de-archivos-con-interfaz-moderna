"""
SearchService - Global search service for workspaces.

Searches files by name across all open tabs in all workspaces.
Uses data already available in memory, does not scan filesystem in real-time.
"""

from typing import List, Set, Dict, Optional
from dataclasses import dataclass
import os

from app.services.file_list_service import get_files
from app.services.file_extensions import SUPPORTED_EXTENSIONS
from app.services.path_utils import normalize_path
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Search result with domain data only."""
    file_path: str
    workspace_id: str


@dataclass
class _CachedFolderListing:
    files: List[str]
    mtime: Optional[float]


def _get_tabs_for_workspace(workspace, active_workspace_id: Optional[str], tab_manager) -> List[str]:
    """Return tab list for workspace, preferring live TabManager for the active one."""
    if tab_manager and workspace.id == active_workspace_id:
        try:
            return tab_manager.get_tabs()
        except Exception:
            return workspace.tabs or []
    return workspace.tabs or []


def _get_folder_signature(folder_path: str) -> Optional[float]:
    """Return a lightweight signature (mtime) for cache invalidation."""
    try:
        return os.path.getmtime(folder_path)
    except (OSError, PermissionError):
        return None


def _get_files_cached(folder_path: str, cache: Dict[str, _CachedFolderListing]) -> List[str]:
    """Get file list with simple mtime-based cache to avoid repeat scans."""
    signature = _get_folder_signature(folder_path)
    cached = cache.get(folder_path)
    if cached and cached.mtime == signature:
        return cached.files
    files = get_files(folder_path, SUPPORTED_EXTENSIONS, use_stacks=False)
    cache[folder_path] = _CachedFolderListing(files=files, mtime=signature)
    return files


def search_in_workspaces(
    query: str,
    workspace_manager,
    tab_manager=None,
    cache: Optional[Dict[str, _CachedFolderListing]] = None
) -> List[SearchResult]:
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
    
    if cache is None:
        cache = {}

    query_lower = query.strip().lower()
    results = []
    seen_paths: Set[str] = set()  # Usar set para deduplicación por path normalizado
    MAX_RESULTS = 1000
    
    workspaces = workspace_manager.get_workspaces()
    active_workspace_id = workspace_manager.get_active_workspace_id()
    logger.info(f"Buscando '{query}' en {len(workspaces)} workspaces (in-memory tabs)")
    
    for workspace in workspaces:
        tabs = _get_tabs_for_workspace(workspace, active_workspace_id, tab_manager)
        logger.info(f"Workspace '{workspace.name}' tiene {len(tabs)} tabs en memoria")
        
        for folder_path in tabs:
            if len(results) >= MAX_RESULTS:
                break
            
            try:
                files = _get_files_cached(folder_path, cache)
                logger.info(f"Carpeta '{folder_path}' tiene {len(files)} entradas cacheadas")
                
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
            except Exception as e:
                logger.error(f"Error buscando en {folder_path}: {e}")
                continue
    
    logger.info(f"Búsqueda completada: {len(results)} resultados encontrados")
    return results

