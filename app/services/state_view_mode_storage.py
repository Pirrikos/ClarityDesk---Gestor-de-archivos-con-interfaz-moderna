"""
StateViewModeStorage - Persistence service for view modes per state.

Handles saving and loading view mode (grid/list) for each state view.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)

# Storage file path
_STORAGE_FILE = Path("storage") / "state_view_modes.json"

# Cache para evitar lecturas repetidas del archivo
_view_modes_cache: Optional[Dict[str, str]] = None
_cache_file_mtime: Optional[float] = None

# Modo por defecto
_DEFAULT_VIEW_MODE = "grid"


def _get_storage_path() -> Path:
    """Get path to state view modes storage file."""
    storage_dir = _STORAGE_FILE.parent
    storage_dir.mkdir(parents=True, exist_ok=True)
    return _STORAGE_FILE


def load_view_modes() -> Dict[str, str]:
    """
    Load view modes for all states from storage.
    
    Returns:
        Dictionary mapping state constants to view modes ("grid" or "list").
        Empty dict if no view modes exist.
    """
    global _view_modes_cache, _cache_file_mtime
    
    storage_path = _get_storage_path()
    
    if not storage_path.exists():
        _view_modes_cache = {}
        _cache_file_mtime = None
        return {}
    
    # Verificar si el cache es válido comparando mtime
    try:
        current_mtime = storage_path.stat().st_mtime
        if _view_modes_cache is not None and _cache_file_mtime == current_mtime:
            return _view_modes_cache
    except OSError:
        pass
    
    # Cargar desde archivo
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _view_modes_cache = data.get('view_modes', {})
            _cache_file_mtime = storage_path.stat().st_mtime
            return _view_modes_cache
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.warning(f"Error loading state view modes: {e}")
        _view_modes_cache = {}
        _cache_file_mtime = None
        return {}


def save_view_modes(view_modes: Dict[str, str]) -> bool:
    """
    Save view modes for all states to storage atomically.
    
    Updates cache after successful save.
    
    Args:
        view_modes: Dictionary mapping state constants to view modes ("grid" or "list").
        
    Returns:
        True if saved successfully, False otherwise.
    """
    global _view_modes_cache, _cache_file_mtime
    
    storage_path = _get_storage_path()
    temp_path = storage_path.with_suffix('.tmp')
    
    try:
        data = {
            'view_modes': view_modes,
            'version': 1
        }
        
        # Atomic write: write to temp file first
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename (prevents corruption)
        os.replace(temp_path, storage_path)
        
        # Actualizar cache
        _view_modes_cache = view_modes.copy()
        try:
            _cache_file_mtime = storage_path.stat().st_mtime
        except OSError:
            _cache_file_mtime = None
        
        return True
    except (IOError, OSError) as e:
        logger.error(f"Error saving state view modes: {e}")
        # Clean up temp file if it exists
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        return False


def get_view_mode(state: str) -> str:
    """
    Get view mode for a state constant.
    
    Args:
        state: State constant (e.g., "pending", "delivered").
        
    Returns:
        View mode ("grid" or "list"), defaults to "grid" if not found.
    """
    view_modes = load_view_modes()
    return view_modes.get(state, _DEFAULT_VIEW_MODE)


def set_view_mode(state: str, view_mode: str) -> bool:
    """
    Set view mode for a state constant.
    
    Args:
        state: State constant (e.g., "pending", "delivered").
        view_mode: View mode ("grid" or "list").
        
    Returns:
        True if saved successfully, False otherwise.
    """
    if view_mode not in ("grid", "list"):
        logger.warning(f"Invalid view_mode: {view_mode}")
        return False
    
    view_modes = load_view_modes()
    view_modes[state] = view_mode
    return save_view_modes(view_modes)

