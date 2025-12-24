"""
StateLabelStorage - Persistence service for custom state labels.

Handles saving and loading custom state label names to/from JSON storage.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)

# Storage file path
_STORAGE_FILE = Path("storage") / "state_labels.json"

# Cache para evitar lecturas repetidas del archivo
_labels_cache: Optional[Dict[str, str]] = None
_cache_file_mtime: Optional[float] = None


def _get_storage_path() -> Path:
    """Get path to state labels storage file."""
    storage_dir = _STORAGE_FILE.parent
    storage_dir.mkdir(parents=True, exist_ok=True)
    return _STORAGE_FILE


def load_custom_labels() -> Dict[str, str]:
    """
    Load custom state labels from storage.
    
    Uses cache to avoid repeated file reads.
    
    Returns:
        Dictionary mapping state constants to custom label names.
        Empty dict if no custom labels exist.
    """
    global _labels_cache, _cache_file_mtime
    
    storage_path = _get_storage_path()
    
    if not storage_path.exists():
        _labels_cache = {}
        _cache_file_mtime = None
        return {}
    
    # Verificar si el cache es válido comparando mtime
    try:
        current_mtime = storage_path.stat().st_mtime
        if _labels_cache is not None and _cache_file_mtime == current_mtime:
            return _labels_cache
    except OSError:
        pass
    
    # Cargar desde archivo
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _labels_cache = data.get('labels', {})
            _cache_file_mtime = storage_path.stat().st_mtime
            return _labels_cache
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.warning(f"Error loading state labels: {e}")
        _labels_cache = {}
        _cache_file_mtime = None
        return {}


def save_custom_labels(labels: Dict[str, str]) -> bool:
    """
    Save custom state labels to storage atomically.
    
    Updates cache after successful save.
    
    Args:
        labels: Dictionary mapping state constants to custom label names.
        
    Returns:
        True if saved successfully, False otherwise.
    """
    global _labels_cache, _cache_file_mtime
    
    storage_path = _get_storage_path()
    temp_path = storage_path.with_suffix('.tmp')
    
    try:
        data = {
            'labels': labels,
            'version': 1
        }
        
        # Atomic write: write to temp file first
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename (prevents corruption)
        os.replace(temp_path, storage_path)
        
        # Actualizar cache
        _labels_cache = labels.copy()
        try:
            _cache_file_mtime = storage_path.stat().st_mtime
        except OSError:
            _cache_file_mtime = None
        
        return True
    except (IOError, OSError) as e:
        logger.error(f"Error saving state labels: {e}")
        # Clean up temp file if it exists
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        return False


def get_custom_label(state: str) -> Optional[str]:
    """
    Get custom label for a state constant.
    
    Args:
        state: State constant (e.g., STATE_PENDING).
        
    Returns:
        Custom label name or None if not customized.
    """
    labels = load_custom_labels()
    return labels.get(state)


def set_custom_label(state: str, label: str) -> bool:
    """
    Set custom label for a state constant.
    
    Args:
        state: State constant (e.g., STATE_PENDING).
        label: Custom label name.
        
    Returns:
        True if saved successfully, False otherwise.
    """
    labels = load_custom_labels()
    labels[state] = label
    return save_custom_labels(labels)


def remove_custom_label(state: str) -> bool:
    """
    Remove custom label for a state constant (revert to default).
    
    Args:
        state: State constant (e.g., STATE_PENDING).
        
    Returns:
        True if removed successfully, False otherwise.
    """
    labels = load_custom_labels()
    if state in labels:
        del labels[state]
        return save_custom_labels(labels)
    return True

