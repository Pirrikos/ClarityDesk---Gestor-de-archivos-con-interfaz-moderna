"""
FileCategoryService - File categorization by type.

Groups files into fixed categories for organized grid display.
"""

import os
import re
from typing import Dict, List, Tuple


# Definición de categorías con orden fijo
CATEGORY_ORDER = [
    "folder",
    "pdf",
    "documents",
    "sheets",
    "slides",
    "images",
    "video",
    "audio",
    "archives",
    "executables",
    "others"
]

CATEGORY_LABELS = {
    "folder": "Carpetas",
    "pdf": "PDFs",
    "documents": "Documentos",
    "sheets": "Hojas de cálculo",
    "slides": "Presentaciones",
    "images": "Imágenes",
    "video": "Videos",
    "audio": "Audio",
    "archives": "Archivos comprimidos",
    "executables": "Ejecutables",
    "others": "Otros"
}

# Extensiones por categoría
CATEGORY_EXTENSIONS = {
    "pdf": {".pdf"},
    "documents": {".doc", ".docx", ".odt", ".rtf", ".txt"},
    "sheets": {".xls", ".xlsx", ".csv"},
    "slides": {".ppt", ".pptx"},
    "images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"},
    "video": {".mp4", ".avi", ".mkv", ".mov"},
    "audio": {".mp3", ".wav", ".flac"},
    "archives": {".zip", ".rar", ".7z"},
    "executables": {".exe", ".msi", ".bat", ".cmd", ".com", ".scr", ".ps1", ".lnk"}
}


def categorize_file(file_path: str) -> str:
    """
    Categorize a single file by its extension or type.
    
    Args:
        file_path: Path to the file or folder.
    
    Returns:
        Category key (e.g., "pdf", "documents", "others").
    """
    if os.path.isdir(file_path):
        return "folder"
    
    _, ext = os.path.splitext(file_path)
    ext_lower = ext.lower()
    
    # Buscar en cada categoría
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if ext_lower in extensions:
            return category
    
    # Si no coincide con ninguna categoría, va a "others"
    return "others"


def group_files_by_category(file_list: List[str]) -> Dict[str, List[str]]:
    """
    Group files into categories maintaining fixed order.
    
    Args:
        file_list: List of file/folder paths.
    
    Returns:
        Dictionary mapping category keys to lists of file paths.
        Categories are in fixed order and only include non-empty groups.
    """
    categorized: Dict[str, List[str]] = {cat: [] for cat in CATEGORY_ORDER}
    
    for file_path in file_list:
        category = categorize_file(file_path)
        categorized[category].append(file_path)
    
    # Ordenar archivos dentro de cada categoría con ordenamiento natural
    for category in categorized:
        categorized[category].sort(key=_natural_sort_key)
    
    # Retornar solo categorías con archivos, manteniendo el orden
    return {
        cat: categorized[cat]
        for cat in CATEGORY_ORDER 
        if categorized[cat]  # Solo incluir si tiene archivos
    }


def _natural_sort_key(path: str) -> tuple:
    """
    Generate sort key for natural (human-like) sorting.
    
    Converts numbers in path to integers for proper numeric ordering.
    Example: "1. PLATON" < "2. ARISTOTELES" < "10. NIETZSCHE"
    
    Args:
        path: File path to generate key for.
        
    Returns:
        Tuple of (string parts, int parts) for comparison.
    """
    filename = os.path.basename(path).lower()
    # Split into text and number parts
    parts = []
    for part in re.split(r'(\d+)', filename):
        if part.isdigit():
            parts.append((0, int(part)))  # Number: sort as integer
        else:
            parts.append((1, part))  # Text: sort as string
    return tuple(parts)


def get_category_label(category_key: str) -> str:
    """
    Get display label for a category.
    
    Args:
        category_key: Category key (e.g., "pdf", "documents").
    
    Returns:
        Display label (e.g., "PDFs", "Documentos").
    """
    return CATEGORY_LABELS.get(category_key, "Otros")


def get_categorized_files_with_labels(file_list: List[str]) -> List[Tuple[str, List[str]]]:
    """
    Group files by category and return as list of (label, files) tuples.
    
    Args:
        file_list: List of file/folder paths.
    
    Returns:
        List of tuples (category_label, file_paths) in fixed order.
    """
    categorized = group_files_by_category(file_list)
    return [
        (get_category_label(cat), categorized[cat])
        for cat in CATEGORY_ORDER
        if cat in categorized
    ]

