"""
PathUtils (Model) - Utilidades puras de normalización de rutas.

Funciones libres de dependencias para normalizar rutas y detectar rutas virtuales.
"""

import os
from typing import Optional


def is_virtual_path(path: str) -> bool:
    """
    Comprobar si una ruta es virtual (no existe en el sistema de archivos).
    
    Las rutas virtuales incluyen contextos de estado (@state://...), y marcadores internos
    como Escritorio/Trash lógicos. No verifica si una ruta real es Escritorio del sistema.
    
    Args:
        path: Ruta a comprobar.
        
    Returns:
        True si es una ruta virtual conocida, False en caso contrario.
    """
    if not path or not isinstance(path, str):
        return False
    
    if path.startswith("@state://"):
        return True
    
    # Marcadores lógicos internos usados por la aplicación
    if path == "__CLARITY_DESKTOP__" or path == "__CLARITY_TRASH__":
        return True
    
    return False


def normalize_path(path: str) -> str:
    """
    Normalizar rutas usando normcase y normpath.
    
    Garantiza comparaciones consistentes independientemente de mayúsculas/minúsculas o barras finales.
    Las rutas virtuales no se normalizan y se devuelven tal cual.
    
    Args:
        path: Cadena de ruta a normalizar.
        
    Returns:
        Cadena de ruta normalizada, o cadena vacía si la entrada es vacía/inválida.
    """
    if not path:
        return ""
    
    if is_virtual_path(path):
        return path
    
    return os.path.normcase(os.path.normpath(path))

