"""
FileOpenService - File opening operations.

Handles opening files with default system application.
"""

import os
import platform
import subprocess


def open_file_with_system(file_path: str) -> bool:
    """Abrir archivo con la aplicación predeterminada del sistema. Devuelve True si tuvo éxito."""
    try:
        if not os.path.exists(file_path):
            return False
        system = platform.system()
        if system == 'Windows':
            try:
                os.startfile(file_path)  # type: ignore[attr-defined]  # Windows: usa asociación por extensión/MIME
                return True
            except Exception:
                return False
        elif system == 'Darwin':  # macOS
            result = subprocess.run(['open', file_path], check=False)  # macOS: comando 'open' delega al Finder
            return result.returncode == 0
        else:  # Linux / otros
            result = subprocess.run(['xdg-open', file_path], check=False)  # Linux: 'xdg-open' usa asociaciones del entorno
            return result.returncode == 0
    except Exception:
        return False

