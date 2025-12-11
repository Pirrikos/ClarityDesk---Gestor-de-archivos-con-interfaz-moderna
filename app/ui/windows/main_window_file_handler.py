"""
MainWindowFileHandler - File opening and preview logic for MainWindow.

Handles file opening and preview filtering logic extracted from MainWindow.
"""

import os
import platform
import subprocess
from pathlib import Path


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
    Filter files to only include text and image files.
    
    Args:
        file_paths: List of file paths to filter.
        
    Returns:
        Filtered list of previewable file paths.
    """
    image_extensions = {
        '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.ico', '.svg'
    }
    text_extensions = {
        '.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml',
        '.yaml', '.yml', '.ini', '.log', '.csv', '.pdf', '.docx', '.rtf'
    }
    
    allowed = []
    for file_path in file_paths:
        ext = Path(file_path).suffix.lower()
        if ext in image_extensions or ext in text_extensions:
            allowed.append(file_path)
    
    return allowed

