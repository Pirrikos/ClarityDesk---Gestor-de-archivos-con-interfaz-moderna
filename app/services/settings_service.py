"""
SettingsService - Application settings management.

Manages reading and writing persistent settings to JSON storage.
"""

import json
from pathlib import Path
from typing import Any, Optional


class SettingsService:
    """Service for application settings management."""
    
    def __init__(self, settings_path: Optional[str] = None):
        """Initialize SettingsService with storage path."""
        if settings_path is None:
            settings_path = Path(__file__).parent.parent.parent / 'storage' / 'settings.json'
        
        self._settings_path = Path(settings_path)
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._defaults = {
            "ui.theme": "dark",
            "ui.icon_size": 96,
            "preview.default_zoom": 1.0,
            "trash.max_age_days": 30
        }
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting value by key."""
        settings = self._load_settings()
        return settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set setting value by key."""
        settings = self._load_settings()
        settings[key] = value
        self._save_settings(settings)
    
    def get_all_settings(self) -> dict:
        """Get all current settings."""
        return self._load_settings()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        self._save_settings(self._defaults.copy())
    
    def _load_settings(self) -> dict:
        """Load settings from JSON file."""
        if not self._settings_path.exists():
            return self._defaults.copy()
        
        try:
            with open(self._settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                settings = self._defaults.copy()
                settings.update(data)
                return settings
        except (json.JSONDecodeError, IOError, OSError):
            return self._defaults.copy()
    
    def _save_settings(self, settings: dict) -> None:
        """Save settings to JSON file."""
        try:
            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except (IOError, OSError):
            pass

