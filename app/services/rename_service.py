"""
RenameService - Service for bulk file renaming.

Handles pattern-based renaming with preview, validation,
and safe application of rename operations.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional


class RenameService:
    """Service for generating and applying bulk file renames."""

    def __init__(self):
        self._templates_file = (
            Path(__file__).parent.parent / "data" / "rename_templates.json"
        )
        self._templates_file.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # PREVIEW
    # ------------------------------------------------------------------


    def generate_preview(
        self,
        paths: list[str],
        pattern: str,
        search_text: str = "",
        replace_text: str = "",
        use_uppercase: bool = False,
        use_lowercase: bool = False,
        use_title_case: bool = False,
        number_position: str = "suffix",
    ) -> list[str]:
        print("PREVIEW PATHS:", paths)
        print("TOTAL PATHS:", len(paths))
        print("UNIQUE PATHS:", len(set(paths)))
        is_single_file = len(paths) == 1

        if not is_single_file and "{n}" not in pattern:
            pattern = (
                "{n} " + pattern
                if number_position == "prefix"
                else pattern + " {n}"
            )

        preview: list[str] = []

        for i, path in enumerate(paths):
            _, original_ext = os.path.splitext(path)

            new_name = self._apply_pattern(
                path,
                pattern,
                index=i + 1,
                is_single_file=is_single_file,
            )

            if search_text:
                new_name = new_name.replace(search_text, replace_text)

            if use_uppercase:
                new_name = new_name.upper()
            elif use_lowercase:
                new_name = new_name.lower()
            elif use_title_case:
                new_name = new_name.title()

            preview.append(new_name + original_ext)

        return preview

    def _apply_pattern(
        self,
        path: str,
        pattern: str,
        index: int,
        is_single_file: bool = False,
    ) -> str:
        filename = os.path.basename(path)
        name, _ = os.path.splitext(filename)

        try:
            mtime = os.path.getmtime(path)
            date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        except (OSError, ValueError):
            date_str = datetime.now().strftime("%Y-%m-%d")

        new_name = (
            pattern.replace("{name}", name)
                   .replace("{date}", date_str)
        )

        if not is_single_file:
            new_name = new_name.replace("{n}", f"{index:02d}")
        else:
            new_name = new_name.replace("{n}", "")

        return " ".join(new_name.split())

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def validate_names(
        self,
        names: list[str],
        base_dir: str,
        original_paths: Optional[list[str]] = None,
    ) -> tuple[bool, Optional[str]]:

        original_paths = original_paths or []

        normalized_originals = {
            os.path.normcase(os.path.abspath(p))
            for p in original_paths
        }

        for path, name in zip(original_paths, names):
            if not name or not name.strip():
                return False, "No se permiten nombres vacíos"

            invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            for char in invalid_chars:
                if char in name:
                    return False, f"El nombre contiene caracteres inválidos: {char}"

            dest_path = os.path.join(os.path.dirname(path), name)
            normalized_dest = os.path.normcase(os.path.abspath(dest_path))

            if os.path.exists(dest_path) and normalized_dest not in normalized_originals:
                return False, f"El archivo '{name}' ya existe en el directorio"

        return True, None

    # ------------------------------------------------------------------
    # APPLY
    # ------------------------------------------------------------------

    def apply_rename(
        self,
        paths: list[str],
        names: list[str],
        on_progress: Optional[Callable[[int, int], None]] = None,
        watcher: Optional[object] = None,
    ) -> None:

        if watcher and hasattr(watcher, "ignore_events"):
            watcher.ignore_events(True)

        try:
            for i, (path, name) in enumerate(zip(paths, names)):
                new_path = os.path.join(os.path.dirname(path), name)

                # permitir no-op (renombrar a sí mismo)
                if os.path.normcase(path) == os.path.normcase(new_path):
                    if on_progress:
                        on_progress(i + 1, len(paths))
                    continue

                os.rename(path, new_path)

                if on_progress:
                    on_progress(i + 1, len(paths))

        finally:
            if watcher and hasattr(watcher, "ignore_events"):
                watcher.ignore_events(False)

    # ------------------------------------------------------------------
    # TEMPLATES
    # ------------------------------------------------------------------

    def load_templates(self) -> list[str]:
        try:
            if self._templates_file.exists():
                with open(self._templates_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            pass
        return []

    def save_template(self, pattern: str) -> None:
        if not pattern or not pattern.strip():
            return

        templates = self.load_templates()
        if pattern not in templates:
            templates.append(pattern)
            self._save_templates(templates)

    def delete_template(self, pattern: str) -> None:
        templates = self.load_templates()
        if pattern in templates:
            templates.remove(pattern)
            self._save_templates(templates)

    def _save_templates(self, templates: list[str]) -> None:
        try:
            with open(self._templates_file, "w", encoding="utf-8") as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

