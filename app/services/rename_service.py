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

    def generate_preview(
        self, 
        paths: list[str], 
        pattern: str,
        search_text: str = "",
        replace_text: str = "",
        use_uppercase: bool = False,
        use_lowercase: bool = False,
        use_title_case: bool = False
    ) -> list[str]:
        """
        Generate preview of new filenames based on pattern.
        
        Args:
            paths: List of file paths to rename.
            pattern: Pattern string with {n}, {name}, {date} placeholders.
            search_text: Text to search for (simple literal, no regex).
            replace_text: Text to replace with.
            use_uppercase: Convert to uppercase.
            use_lowercase: Convert to lowercase.
            use_title_case: Capitalize words.
        
        Returns:
            List of new filenames (without paths).
        """
        is_single_file = len(paths) == 1
        
        # Solo agregar {n} automáticamente si hay múltiples archivos
        if not is_single_file and "{n}" not in pattern:
            pattern = pattern + " {n}"
        
        preview = []
        for i, path in enumerate(paths):
            # Obtener extensión original del archivo
            _, original_ext = os.path.splitext(path)
            
            # Aplicar patrón (devuelve nombre sin extensión)
            new_name = self._apply_pattern(path, pattern, i + 1, len(paths), is_single_file)
            
            # Aplicar búsqueda/reemplazo si está configurado
            if search_text:
                new_name = new_name.replace(search_text, replace_text)
            
            # Aplicar formato de texto (solo al nombre, no a la extensión)
            if use_uppercase:
                new_name = new_name.upper()
            elif use_lowercase:
                new_name = new_name.lower()
            elif use_title_case:
                new_name = new_name.title()
            
            # Preservar extensión original siempre
            preview.append(new_name + original_ext)
        
        return preview
    
    def _apply_pattern(self, path: str, pattern: str, index: int, total: int, is_single_file: bool = False) -> str:
        """
        Apply pattern to single file path.
        
        Args:
            path: File path.
            pattern: Pattern string with placeholders.
            index: Current file index (1-based).
            total: Total number of files.
            is_single_file: If True, ignore {n} placeholder.
        
        Returns:
            New filename WITHOUT extension (la extensión se preserva en generate_preview).
        """
        filename = os.path.basename(path)
        name, _ = os.path.splitext(filename)
        
        try:
            mtime = os.path.getmtime(path)
            dt = datetime.fromtimestamp(mtime)
            date_str = dt.strftime("%Y-%m-%d")
        except (OSError, ValueError):
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        new_name = pattern
        
        # Reemplazar placeholders
        new_name = new_name.replace("{name}", name)
        new_name = new_name.replace("{date}", date_str)
        
        # {n} solo se aplica si NO es un archivo único
        if not is_single_file:
            number_str = f"{index:02d}"
            new_name = new_name.replace("{n}", number_str)
        else:
            # Si es archivo único, eliminar {n} silenciosamente
            new_name = new_name.replace("{n}", "")
        
        # Limpiar espacios dobles que puedan quedar al eliminar {n}
        new_name = " ".join(new_name.split())
        
        return new_name
    
    def validate_names(
        self, 
        names: list[str], 
        base_dir: str, 
        original_paths: Optional[list[str]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that new names don't conflict with existing files in filesystem.
        
        Only validates against filesystem real (os.path.exists), excluding files
        that are being renamed. Internal batch conflicts are resolved automatically
        by {n} numbering or conflict resolution in rename_file().
        
        Args:
            names: List of new filenames.
            base_dir: Directory where files will be renamed.
            original_paths: Optional list of original file paths being renamed.
                          Used to exclude them from validation.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        # Build set of original filenames being renamed (to exclude from validation)
        original_names = set()
        if original_paths:
            for path in original_paths:
                original_names.add(os.path.basename(path))
        
        # Validate each name against filesystem real
        for name in names:
            # Validate empty name
            if not name or name.strip() == "":
                return False, "No se permiten nombres vacíos"
            
            # Validate invalid characters
            invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            for char in invalid_chars:
                if char in name:
                    return False, f"El nombre contiene caracteres inválidos: {char}"
            
            # Validate against filesystem real (exclude files being renamed)
            dest_path = os.path.join(base_dir, name)
            if os.path.exists(dest_path):
                # Only error if the existing file is NOT one being renamed
                if name not in original_names:
                    return False, f"El archivo '{name}' ya existe en el directorio"
        
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

