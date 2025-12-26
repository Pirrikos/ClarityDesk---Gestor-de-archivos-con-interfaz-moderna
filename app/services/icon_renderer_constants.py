"""
IconRendererConstants - Constants for icon rendering.

SVG icon mapping and color definitions.
"""

import os
from pathlib import Path

from PySide6.QtGui import QColor

# Poppler path
POPPLER_PATH = Path(__file__).parent.parent.parent / "assets" / "poppler" / "bin"

# SVG icon mapping
SVG_ICON_MAP = {
    # Documentos
    ".doc": "doc.svg", ".docx": "doc.svg", ".rtf": "doc.svg", ".odt": "doc.svg", ".pdf": "doc.svg",
    # Hojas de cálculo
    ".xls": "sheet.svg", ".xlsx": "sheet.svg", ".csv": "sheet.svg", ".ods": "sheet.svg",
    # Presentaciones
    ".ppt": "slide.svg", ".pptx": "slide.svg", ".odp": "slide.svg",
    # Archivos comprimidos
    ".zip": "archive.svg", ".rar": "archive.svg", ".7z": "archive.svg", 
    ".tar": "archive.svg", ".gz": "archive.svg", ".bz2": "archive.svg", ".xz": "archive.svg",
    # Media (audio/video)
    ".mp3": "media.svg", ".wav": "media.svg", ".flac": "media.svg", ".ogg": "media.svg", 
    ".aac": "media.svg", ".wma": "media.svg",
    ".mp4": "media.svg", ".mov": "media.svg", ".avi": "media.svg", ".mkv": "media.svg", 
    ".wmv": "media.svg", ".flv": "media.svg", ".webm": "media.svg",
    # Código
    ".py": "code.svg", ".js": "code.svg", ".ts": "code.svg", ".tsx": "code.svg", ".jsx": "code.svg",
    ".html": "code.svg", ".css": "code.svg", ".scss": "code.svg", ".less": "code.svg",
    ".java": "code.svg", ".c": "code.svg", ".cpp": "code.svg", ".h": "code.svg", ".cs": "code.svg",
    ".php": "code.svg", ".rb": "code.svg", ".go": "code.svg", ".rs": "code.svg", ".swift": "code.svg",
    ".sql": "code.svg", ".vue": "code.svg", ".svelte": "code.svg",
    # Ejecutables y scripts
    ".exe": "exe.svg", ".lnk": "exe.svg", ".msi": "exe.svg", 
    ".bat": "exe.svg", ".cmd": "exe.svg", ".ps1": "exe.svg", ".sh": "exe.svg",
    # Texto plano
    ".txt": "text.svg", ".ini": "text.svg", ".log": "text.svg", ".md": "text.svg",
    ".cfg": "text.svg", ".conf": "text.svg", ".nfo": "text.svg",
    # Configuración estructurada
    ".json": "config.svg", ".xml": "config.svg", ".yaml": "config.svg", ".yml": "config.svg",
    ".toml": "config.svg", ".env": "config.svg", ".properties": "config.svg",
}

# Color mapping for SVG types (colores saturados para buen contraste)
SVG_COLOR_MAP = {
    "doc.svg": QColor(41, 128, 185),      # Azul Word
    "sheet.svg": QColor(39, 174, 96),      # Verde Excel
    "slide.svg": QColor(211, 84, 0),       # Naranja PowerPoint
    "archive.svg": QColor(192, 57, 43),    # Rojo archivo
    "media.svg": QColor(142, 68, 173),     # Púrpura media
    "code.svg": QColor(44, 62, 80),        # Azul oscuro código
    "exe.svg": QColor(52, 73, 94),         # Gris azulado exe
    "text.svg": QColor(127, 140, 141),     # Gris texto
    "config.svg": QColor(243, 156, 18),    # Amarillo/naranja config
    "generic.svg": QColor(52, 73, 94),     # Azul oscuro genérico (más visible)
}

