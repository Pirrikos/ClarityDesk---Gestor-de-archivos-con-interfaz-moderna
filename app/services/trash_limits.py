"""
TrashLimits - Trash limits checking.

Checks if trash exceeds age or size limits (only checks, never deletes automatically).
"""

import os
from datetime import datetime
from pathlib import Path

from app.services.trash_storage import (
    MAX_TRASH_AGE_DAYS,
    MAX_TRASH_SIZE_MB,
    get_trash_path,
    load_trash_metadata,
)


def check_trash_limits() -> tuple[bool, str]:
    """
    Check if trash exceeds limits (age or size).
    
    Returns:
        Tuple (exceeds_limit: bool, warning_message: str).
    """
    trash_dir = get_trash_path()
    if not trash_dir.exists():
        return False, ""
    
    metadata = load_trash_metadata()
    now = datetime.now()
    total_size_mb = 0
    oldest_date = None
    
    try:
        for filename, file_metadata in metadata.items():
            trash_file_path = trash_dir / filename
            if not trash_file_path.exists():
                continue
            
            if trash_file_path.is_file():
                total_size_mb += trash_file_path.stat().st_size / (1024 * 1024)
            elif trash_file_path.is_dir():
                for root, dirs, files in os.walk(trash_file_path):
                    for f in files:
                        file_path = Path(root) / f
                        total_size_mb += file_path.stat().st_size / (1024 * 1024)
            
            deleted_date_str = file_metadata.get("deleted_date")
            if deleted_date_str:
                try:
                    deleted_date = datetime.fromisoformat(deleted_date_str)
                    if oldest_date is None or deleted_date < oldest_date:
                        oldest_date = deleted_date
                except Exception:
                    pass
        
        exceeds_size = total_size_mb > MAX_TRASH_SIZE_MB
        exceeds_age = False
        if oldest_date:
            age_days = (now - oldest_date).days
            exceeds_age = age_days > MAX_TRASH_AGE_DAYS
        
        if exceeds_size or exceeds_age:
            messages = []
            if exceeds_size:
                messages.append(f"más de {MAX_TRASH_SIZE_MB}MB")
            if exceeds_age:
                messages.append(f"más de {MAX_TRASH_AGE_DAYS} días")
            
            warning = f"La papelera tiene {', '.join(messages)}. Por favor, revisa y vacía la papelera."
            return True, warning
        
        return False, ""
    except Exception:
        return False, ""


