"""
Preview File Extensions - File extension constants for preview system.

Centralized definition of file extensions that support preview functionality.

R11: All extensions are normalized to lowercase in a single entry point.
R12: Hard file size limits prevent preview of oversized files.
R13: Early existence validation before any rendering.
R14: Pixmap validation before use.
"""

import os
from pathlib import Path

PREVIEW_IMAGE_EXTENSIONS = frozenset({
    '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.ico', '.svg'
})

PREVIEW_TEXT_EXTENSIONS = frozenset({
    '.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml',
    '.yaml', '.yml', '.ini', '.log', '.csv', '.rtf'
})

# Nota: .doc (formato antiguo) NO está soportado porque docx2pdf solo acepta .docx
PREVIEW_PDF_DOCX_EXTENSIONS = frozenset({'.pdf', '.docx'})

PREVIEWABLE_EXTENSIONS = (
    PREVIEW_IMAGE_EXTENSIONS | 
    PREVIEW_TEXT_EXTENSIONS | 
    PREVIEW_PDF_DOCX_EXTENSIONS
)


def normalize_extension(path: str) -> str:
    """
    Extract and normalize file extension to lowercase.
    
    R11: Single entry point for extension normalization.
    All other code assumes extensions are already normalized.
    
    Args:
        path: File path.
    
    Returns:
        Normalized extension in lowercase (e.g., '.pdf', '.jpg').
        Returns empty string if no extension.
    
    Examples:
        "DOCUMENTO.PDF" → ".pdf"
        "Foto.JpG" → ".jpg"
        "file.txt" → ".txt"
    """
    try:
        return Path(path).suffix.lower()
    except Exception:
        return ""


def is_previewable_image(ext: str) -> bool:
    """
    Check if extension is a previewable image.
    
    Args:
        ext: Extension (must be already normalized via normalize_extension).
    """
    return ext in PREVIEW_IMAGE_EXTENSIONS


def is_previewable_text(ext: str) -> bool:
    """
    Check if extension is a previewable text file.
    
    Args:
        ext: Extension (must be already normalized via normalize_extension).
    """
    return ext in PREVIEW_TEXT_EXTENSIONS


def is_previewable_pdf_docx(ext: str) -> bool:
    """
    Check if extension is PDF or DOCX.
    
    Args:
        ext: Extension (must be already normalized via normalize_extension).
    """
    return ext in PREVIEW_PDF_DOCX_EXTENSIONS


def is_previewable(ext: str) -> bool:
    """
    Check if extension is previewable.
    
    Args:
        ext: Extension (must be already normalized via normalize_extension).
    """
    return ext in PREVIEWABLE_EXTENSIONS


# R12: Hard file size limits (in bytes)
MAX_PDF_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_DOCX_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_IMAGE_SIZE = 200 * 1024 * 1024  # 200 MB
MAX_TEXT_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_GENERIC_SIZE = 50 * 1024 * 1024  # 50 MB default


def validate_file_for_preview(path: str) -> tuple[bool, str]:
    """
    Validate file for preview rendering.
    
    R13: Early existence and type validation.
    R12: Hard size limit check.
    
    Args:
        path: File path to validate.
    
    Returns:
        Tuple of (is_valid, error_message).
        is_valid=True if file can be previewed, False otherwise.
        error_message is empty if valid, otherwise contains reason.
    """
    try:
        if not path or not os.path.exists(path):
            return False, "File does not exist"
    except (OSError, ValueError):
        return False, "Cannot access file"
    
    try:
        if not os.path.isfile(path):
            return False, "Not a regular file"
    except (OSError, ValueError):
        return False, "Cannot determine file type"
    
    try:
        file_size = os.path.getsize(path)
        ext = normalize_extension(path)
        
        if ext == ".pdf":
            if file_size > MAX_PDF_SIZE:
                return False, f"PDF too large ({file_size / (1024*1024):.1f} MB > {MAX_PDF_SIZE / (1024*1024)} MB)"
        elif ext == ".docx":
            if file_size > MAX_DOCX_SIZE:
                return False, f"DOCX too large ({file_size / (1024*1024):.1f} MB > {MAX_DOCX_SIZE / (1024*1024)} MB)"
        elif ext in PREVIEW_IMAGE_EXTENSIONS:
            if file_size > MAX_IMAGE_SIZE:
                return False, f"Image too large ({file_size / (1024*1024):.1f} MB > {MAX_IMAGE_SIZE / (1024*1024)} MB)"
        elif ext in PREVIEW_TEXT_EXTENSIONS:
            if file_size > MAX_TEXT_SIZE:
                return False, f"Text file too large ({file_size / (1024*1024):.1f} MB > {MAX_TEXT_SIZE / (1024*1024)} MB)"
        else:
            if file_size > MAX_GENERIC_SIZE:
                return False, f"File too large ({file_size / (1024*1024):.1f} MB > {MAX_GENERIC_SIZE / (1024*1024)} MB)"
    except (OSError, ValueError) as e:
        return False, f"Cannot read file size: {e}"
    
    return True, ""


def validate_pixmap(pixmap) -> bool:
    """
    Validate pixmap before use.
    
    R14: Check pixmap is not null, has minimum size, and basic coherence.
    
    Args:
        pixmap: QPixmap to validate.
    
    Returns:
        True if pixmap is valid and usable, False otherwise.
    """
    if pixmap is None:
        return False
    
    try:
        if pixmap.isNull():
            return False
        
        if pixmap.width() <= 0 or pixmap.height() <= 0:
            return False
        
        MAX_REASONABLE_SIZE = 50000
        if pixmap.width() > MAX_REASONABLE_SIZE or pixmap.height() > MAX_REASONABLE_SIZE:
            return False
        
        MAX_REASONABLE_AREA = 2_500_000_000
        area = pixmap.width() * pixmap.height()
        if area > MAX_REASONABLE_AREA:
            return False
        
        return True
    except Exception:
        return False

