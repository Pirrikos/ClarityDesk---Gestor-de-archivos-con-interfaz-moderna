"""
StoragePathService - Centralized storage path management.

Provides consistent storage directory location across development and production environments.
Handles executable mode (.exe) and development mode (Python) transparently.
"""

from pathlib import Path
import sys
import os
from typing import Optional

from app.core.logger import get_logger

logger = get_logger(__name__)

# Cache para evitar múltiples verificaciones
_storage_dir_cache: Optional[Path] = None


def get_storage_dir() -> Path:
    """
    Get application storage directory.

    Behavior:
        - Both development and executable modes use: %APPDATA%/ClarityDesk/storage/
        - This ensures consistent data location regardless of execution mode

    Returns:
        Path to storage directory (creates if missing).

    Raises:
        RuntimeError: If storage cannot be created or is not writable.
    """
    global _storage_dir_cache

    # Retornar cache si ya fue validado
    if _storage_dir_cache is not None:
        return _storage_dir_cache

    try:
        # Usar AppData para ambos modos (desarrollo y ejecutable)
        appdata = os.environ.get('APPDATA')
        if not appdata:
            raise RuntimeError("APPDATA environment variable not found")
        
        base_dir = Path(appdata) / "ClarityDesk"
        logger.debug(f"Using AppData storage, base_dir: {base_dir}")

        storage_dir = base_dir / "storage"

        # Crear directorio con permisos (parents=True para crear intermedios si es necesario)
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Verificar que es escribible
        if not os.access(storage_dir, os.W_OK):
            raise PermissionError(f"Storage directory not writable: {storage_dir}")

        # Cachear resultado válido
        _storage_dir_cache = storage_dir
        logger.info(f"Storage directory initialized: {storage_dir}")
        return storage_dir

    except PermissionError as e:
        logger.error(f"Permission error accessing storage: {e}")
        raise RuntimeError(f"Cannot access storage directory (permission denied): {e}")
    except OSError as e:
        logger.error(f"OS error creating storage directory: {e}")
        raise RuntimeError(f"Cannot create storage directory (OS error): {e}")


def get_storage_file(filename: str) -> Path:
    """
    Get full path to a storage file.

    Args:
        filename: Name of file in storage directory.

    Returns:
        Full path to storage file.

    Example:
        >>> config_path = get_storage_file("state_labels.json")
        >>> db_path = get_storage_file("claritydesk.db")
    """
    return get_storage_dir() / filename


def clear_cache() -> None:
    """
    Clear storage directory cache.

    Useful for testing or when storage location changes at runtime.
    """
    global _storage_dir_cache
    _storage_dir_cache = None
    logger.debug("Storage directory cache cleared")
