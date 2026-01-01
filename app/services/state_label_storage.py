"""
StateLabelStorage - Persistence service for custom state labels.

Handles saving and loading custom state label names to/from JSON storage.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from app.core.logger import get_logger
from app.services.storage_path_service import get_storage_file

logger = get_logger(__name__)

# Storage file path
_STORAGE_FILE = get_storage_file("state_labels.json")

# Cache para evitar lecturas repetidas del archivo
_labels_cache: Optional[Dict[str, str]] = None
_order_cache: Optional[List[str]] = None
_cache_file_mtime: Optional[float] = None

# Orden por defecto de estados
_DEFAULT_STATE_ORDER = ["pending", "delivered", "corrected", "review"]


def _get_storage_path() -> Path:
    """Get path to state labels storage file."""
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
            # Cargar orden si existe, sino usar default
            global _order_cache
            _order_cache = data.get('order', _DEFAULT_STATE_ORDER.copy())
            _cache_file_mtime = storage_path.stat().st_mtime
            return _labels_cache
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.warning(f"Error loading state labels: {e}")
        _labels_cache = {}
        _order_cache = _DEFAULT_STATE_ORDER.copy()
        _cache_file_mtime = None
        return {}


def save_custom_labels(labels: Dict[str, str]) -> bool:
    """
    Save custom state labels to storage atomically.
    
    Updates cache after successful save.
    Preserves existing order if present.
    
    Args:
        labels: Dictionary mapping state constants to custom label names.
        
    Returns:
        True if saved successfully, False otherwise.
    """
    global _labels_cache, _order_cache, _cache_file_mtime
    
    storage_path = _get_storage_path()
    temp_path = storage_path.with_suffix('.tmp')
    
    # Cargar orden actual si existe, sino usar default
    if _order_cache is None:
        _order_cache = load_state_order()
    
    try:
        data = {
            'labels': labels,
            'order': _order_cache,
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


def load_state_order() -> List[str]:
    """
    Load state order from storage.
    
    Returns:
        List of state constants in display order.
        Default order if not found in storage.
    """
    global _order_cache, _cache_file_mtime
    
    storage_path = _get_storage_path()
    
    if not storage_path.exists():
        _order_cache = _DEFAULT_STATE_ORDER.copy()
        return _order_cache.copy()
    
    # Verificar si el cache es válido
    try:
        current_mtime = storage_path.stat().st_mtime
        if _order_cache is not None and _cache_file_mtime == current_mtime:
            return _order_cache.copy()
    except OSError:
        pass
    
    # Cargar desde archivo
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _order_cache = data.get('order', _DEFAULT_STATE_ORDER.copy())
            _cache_file_mtime = storage_path.stat().st_mtime
            return _order_cache.copy()
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.warning(f"Error loading state order: {e}")
        _order_cache = _DEFAULT_STATE_ORDER.copy()
        return _order_cache.copy()


def save_state_order(order: List[str]) -> bool:
    """
    Save state order to storage atomically.
    
    Updates cache after successful save.
    Preserves existing labels if present.
    
    Args:
        order: List of state constants in display order.
        
    Returns:
        True if saved successfully, False otherwise.
    """
    global _labels_cache, _order_cache, _cache_file_mtime
    
    storage_path = _get_storage_path()
    temp_path = storage_path.with_suffix('.tmp')
    
    # Cargar labels actuales si existen
    if _labels_cache is None:
        _labels_cache = load_custom_labels()
    
    try:
        data = {
            'labels': _labels_cache,
            'order': order,
            'version': 1
        }
        
        # Atomic write: write to temp file first
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename (prevents corruption)
        os.replace(temp_path, storage_path)
        
        # Actualizar cache
        _order_cache = order.copy()
        try:
            _cache_file_mtime = storage_path.stat().st_mtime
        except OSError:
            _cache_file_mtime = None
        
        return True
    except (IOError, OSError) as e:
        logger.error(f"Error saving state order: {e}")
        # Clean up temp file if it exists
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        return False

