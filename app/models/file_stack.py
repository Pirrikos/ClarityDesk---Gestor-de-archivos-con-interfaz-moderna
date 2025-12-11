"""
FileStack - Model for grouping files by type.

Represents a stack of files grouped by extension or type.
"""

from dataclasses import dataclass
from typing import List


# Nombres amigables para FAMILIAS de archivos en español
FRIENDLY_NAMES = {
    # Familias fijas (agrupación por familia, no por extensión)
    'folder': "Carpetas",
    'pdf': "PDFs",
    'documents': "Documentos",
    'sheets': "Hojas de cálculo",
    'slides': "Presentaciones",
    'images': "Imágenes",
    'video': "Videos",
    'audio': "Audio",
    'archives': "Archivos comprimidos",
    'executables': "Ejecutables",
    'others': "Otros",
}


@dataclass
class FileStack:
    """Stack of files grouped by type."""
    
    stack_type: str  # File extension or type (e.g., '.pdf', '.docx', 'folder')
    files: List[str]  # List of file paths in this stack
    
    def get_display_name(self) -> str:
        """Get friendly display name for the stack in Spanish."""
        # Buscar nombre amigable por familia
        if self.stack_type in FRIENDLY_NAMES:
            return FRIENDLY_NAMES[self.stack_type]
        
        # Fallback: usar el tipo directamente (no debería ocurrir con familias)
        return self.stack_type.title()
    
    def get_count(self) -> int:
        """Get number of files in stack."""
        return len(self.files)
    
    def is_single_file(self) -> bool:
        """Check if stack contains only one file."""
        return len(self.files) == 1
    
    def get_single_file_path(self) -> str:
        """Get the single file path if stack has only one file."""
        if self.is_single_file():
            return self.files[0]
        return None

