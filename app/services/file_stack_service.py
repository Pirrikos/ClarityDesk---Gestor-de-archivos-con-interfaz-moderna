"""
FileStackService - File stacking operations.

Handles grouping files into stacks by family/type.
"""

import os
import re
from collections import defaultdict
from typing import List

from app.models.file_stack import FileStack


# Mapeo de extensiones a familias de stacks
EXTENSION_TO_FAMILY = {
    # PDF (familia separada)
    '.pdf': 'pdf',
    
    # Documents
    '.doc': 'documents',
    '.docx': 'documents',
    '.odt': 'documents',
    '.rtf': 'documents',
    '.txt': 'documents',
    '.json': 'documents',
    
    # Sheets
    '.xls': 'sheets',
    '.xlsx': 'sheets',
    '.csv': 'sheets',
    
    # Slides
    '.ppt': 'slides',
    '.pptx': 'slides',
    
    # Images
    '.jpg': 'images',
    '.jpeg': 'images',
    '.png': 'images',
    '.gif': 'images',
    '.webp': 'images',
    '.svg': 'images',
    
    # Video
    '.mp4': 'video',
    '.avi': 'video',
    '.mkv': 'video',
    '.mov': 'video',
    
    # Audio
    '.mp3': 'audio',
    '.wav': 'audio',
    '.flac': 'audio',
    
    # Archives
    '.zip': 'archives',
    '.rar': 'archives',
    '.7z': 'archives',
    
    # Executables
    '.exe': 'executables',
    '.msi': 'executables',
    '.bat': 'executables',
    '.cmd': 'executables',
    '.com': 'executables',
    '.scr': 'executables',
    '.ps1': 'executables',
    '.lnk': 'executables',  # Windows shortcuts/accessos directos
}

# Orden visual constante de familias
FAMILY_ORDER = [
    'folder',
    'pdf',
    'documents',
    'sheets',
    'slides',
    'images',
    'video',
    'audio',
    'archives',
    'executables',
    'others',
]


def get_file_family(file_path: str, is_executable_func) -> str:
    """
    Get the family name for a file based on its extension.
    
    Args:
        file_path: Path to the file.
        is_executable_func: Function to check if file is executable.
        
    Returns:
        Family name (e.g., 'pdf', 'documents', 'images', etc.).
    """
    if os.path.isdir(file_path):
        return 'folder'
    
    ext = os.path.splitext(file_path)[1].lower()
    
    # Para accesos directos (.lnk), verificar si apuntan a una carpeta
    if ext == '.lnk':
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(file_path)
            target_path = shortcut.Targetpath
            if target_path and os.path.exists(target_path) and os.path.isdir(target_path):
                return 'folder'
        except Exception:
            pass  # Si falla la resolución, continuar con la lógica normal
    
    # Check if extension is in mapping
    if ext in EXTENSION_TO_FAMILY:
        return EXTENSION_TO_FAMILY[ext]
    
    # Check if it's an executable (with or without extension)
    if is_executable_func(file_path):
        return 'executables'
    
    # Default: others (includes files without extension and unknown extensions)
    return 'others'


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


def create_file_stacks(files: List[str], is_executable_func) -> List[FileStack]:
    """
    Group files into stacks by FAMILY (not individual extension).
    
    Uses fixed families: folder, pdf, documents, sheets, slides, images,
    video, audio, archives, executables, others.
    
    Args:
        files: List of file paths.
        is_executable_func: Function to check if file is executable.
        
    Returns:
        List of FileStack objects, ordered by FAMILY_ORDER, only including non-empty stacks.
    """
    # Group files by family
    stacks_dict = defaultdict(list)
    
    for file_path in files:
        family = get_file_family(file_path, is_executable_func)
        stacks_dict[family].append(file_path)
    
    # Create FileStack objects in fixed order, only for non-empty families
    stacks = []
    for family in FAMILY_ORDER:
        if family in stacks_dict and stacks_dict[family]:
            file_list = sorted(stacks_dict[family], key=_natural_sort_key)
            stacks.append(FileStack(stack_type=family, files=file_list))
    
    return stacks

