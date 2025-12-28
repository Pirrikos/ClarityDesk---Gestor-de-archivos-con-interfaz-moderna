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


def open_containing_folder(file_path: str) -> bool:
    """Abrir carpeta contenedora en el explorador y seleccionar el archivo. Devuelve True si tuvo éxito."""
    try:
        if not os.path.exists(file_path):
            return False
        
        system = platform.system()
        if system == 'Windows':
            try:
                # Windows: explorer /select,<ruta> abre la carpeta y selecciona el archivo
                subprocess.Popen(['explorer', '/select,', os.path.normpath(file_path)])
                return True
            except Exception:
                return False
        elif system == 'Darwin':  # macOS
            try:
                # macOS: open -R abre Finder y selecciona el archivo
                subprocess.run(['open', '-R', file_path], check=False)
                return True
            except Exception:
                return False
        else:  # Linux / otros
            try:
                # Linux: abrir carpeta padre con xdg-open
                folder_path = os.path.dirname(file_path)
                result = subprocess.run(['xdg-open', folder_path], check=False)
                return result.returncode == 0
            except Exception:
                return False
    except Exception:
        return False
