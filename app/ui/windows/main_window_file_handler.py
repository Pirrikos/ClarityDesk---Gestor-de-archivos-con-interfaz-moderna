"""
MainWindowFileHandler - File opening and preview logic for MainWindow.

Handles file opening and preview filtering logic extracted from MainWindow.
"""

import os
import platform
import subprocess
from pathlib import Path

from app.services.preview_file_extensions import (
    PREVIEW_IMAGE_EXTENSIONS,
    PREVIEW_TEXT_EXTENSIONS,
    PREVIEW_PDF_DOCX_EXTENSIONS,
    normalize_extension
)


def open_file_with_system(file_path: str) -> None:
    """
    Open file with default system application.
    
    Args:
        file_path: Path to file to open.
    """
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', file_path])
        else:  # Linux
            subprocess.run(['xdg-open', file_path])
    except Exception:
        pass  # Silently fail if file cannot be opened


def filter_previewable_files(file_paths: list[str]) -> list[str]:
    """
    Filter files to only include previewable files (images, text, PDF, DOCX).
    
    Args:
        file_paths: List of file paths to filter.
        
    Returns:
        Filtered list of previewable file paths.
    """
    previewable_extensions = (
        PREVIEW_IMAGE_EXTENSIONS | 
        PREVIEW_TEXT_EXTENSIONS | 
        PREVIEW_PDF_DOCX_EXTENSIONS
    )
    
    allowed = []
    for file_path in file_paths:
        # R11: Normalize extension in single entry point
        ext = normalize_extension(file_path)
        if ext in previewable_extensions:
            allowed.append(file_path)
    
    return allowed

