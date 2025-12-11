"""
RenameService - Service for bulk file renaming.

Handles pattern-based renaming with preview and validation.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional


class RenameService:
    """Service for generating and applying bulk file renames."""
    
    def __init__(self):
        """Initialize RenameService with templates file path."""
        self._templates_file = Path(__file__).parent.parent / "data" / "rename_templates.json"
        self._templates_file.parent.mkdir(parents=True, exist_ok=True)

    def generate_preview(self, paths: list[str], pattern: str) -> list[str]:
        """
        Generate preview of new filenames based on pattern.
        
        Args:
            paths: List of file paths to rename.
            pattern: Pattern string with {n}, {name}, {date} placeholders.
        
        Returns:
            List of new filenames (without paths).
        """
        if "{n}" not in pattern:
            pattern = pattern + " {n}"
        
        preview = []
        for i, path in enumerate(paths):
            new_name = self._apply_pattern(path, pattern, i + 1, len(paths))
            preview.append(new_name)
        return preview
    
    def _apply_pattern(self, path: str, pattern: str, index: int, total: int) -> str:
        """Apply pattern to single file path."""
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        
        try:
            mtime = os.path.getmtime(path)
            dt = datetime.fromtimestamp(mtime)
            date_str = dt.strftime("%Y-%m-%d")
        except (OSError, ValueError):
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        number_str = f"{index:02d}"
        
        new_name = pattern
        new_name = new_name.replace("{n}", number_str)
        new_name = new_name.replace("{name}", name)
        new_name = new_name.replace("{date}", date_str)
        
        return new_name + ext
    
    def validate_names(self, names: list[str], base_dir: str) -> tuple[bool, Optional[str]]:
        """
        Validate that new names don't conflict with existing files.
        
        Args:
            names: List of new filenames.
            base_dir: Directory where files will be renamed.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            existing_files = set(os.listdir(base_dir))
        except OSError:
            existing_files = set()
        
        for name in names:
            if name in existing_files:
                return False, f"El archivo '{name}' ya existe"
            
            if not name or name.strip() == "":
                return False, "No se permiten nombres vacíos"
            
            invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            for char in invalid_chars:
                if char in name:
                    return False, f"El nombre contiene caracteres inválidos: {char}"
        
        return True, None
    
    def apply_rename(
        self,
        paths: list[str],
        names: list[str],
        on_progress: Optional[Callable[[int, int], None]] = None,
        watcher: Optional[object] = None
    ) -> None:
        """
        Apply renaming to files.
        
        Args:
            paths: List of original file paths.
            names: List of new filenames (without paths).
            on_progress: Optional callback for progress updates (current, total).
            watcher: Optional FileSystemWatcherService to block events during rename.
        """
        # Block watcher events during rename operation
        if watcher and hasattr(watcher, 'ignore_events'):
            watcher.ignore_events(True)
        
        try:
            for i, (path, name) in enumerate(zip(paths, names)):
                dir_path = os.path.dirname(path)
                new_path = os.path.join(dir_path, name)
                
                try:
                    os.rename(path, new_path)
                    if on_progress:
                        on_progress(i + 1, len(paths))
                except OSError as e:
                    raise RuntimeError(f"Error renombrando '{os.path.basename(path)}': {str(e)}")
        finally:
            # Unblock watcher events
            if watcher and hasattr(watcher, 'ignore_events'):
                watcher.ignore_events(False)
    
    def load_templates(self) -> list[str]:
        """
        Load rename templates from JSON file.
        
        Returns:
            List of template patterns.
        """
        try:
            if self._templates_file.exists():
                with open(self._templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                    return templates if isinstance(templates, list) else []
        except (json.JSONDecodeError, OSError):
            pass
        return []
    
    def save_template(self, pattern: str) -> None:
        """
        Save a template pattern to JSON file.
        
        Args:
            pattern: Pattern string to save.
        """
        if not pattern or not pattern.strip():
            return
        
        templates = self.load_templates()
        if pattern not in templates:
            templates.append(pattern)
            self._save_templates(templates)
    
    def delete_template(self, pattern: str) -> None:
        """
        Delete a template pattern from JSON file.
        
        Args:
            pattern: Pattern string to delete.
        """
        templates = self.load_templates()
        if pattern in templates:
            templates.remove(pattern)
            self._save_templates(templates)
    
    def _save_templates(self, templates: list[str]) -> None:
        """Save templates list to JSON file."""
        try:
            with open(self._templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

