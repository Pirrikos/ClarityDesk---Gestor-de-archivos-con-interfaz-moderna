"""
Preview File Extensions - File extension constants for preview system.

Centralized definition of file extensions that support preview functionality.
"""

PREVIEW_IMAGE_EXTENSIONS = frozenset({
    '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.ico', '.svg'
})

PREVIEW_TEXT_EXTENSIONS = frozenset({
    '.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml',
    '.yaml', '.yml', '.ini', '.log', '.csv', '.rtf'
})

PREVIEW_PDF_DOCX_EXTENSIONS = frozenset({'.pdf', '.docx'})

PREVIEWABLE_EXTENSIONS = (
    PREVIEW_IMAGE_EXTENSIONS | 
    PREVIEW_TEXT_EXTENSIONS | 
    PREVIEW_PDF_DOCX_EXTENSIONS
)


def is_previewable_image(ext: str) -> bool:
    """Check if extension is a previewable image."""
    return ext.lower() in PREVIEW_IMAGE_EXTENSIONS


def is_previewable_text(ext: str) -> bool:
    """Check if extension is a previewable text file."""
    return ext.lower() in PREVIEW_TEXT_EXTENSIONS


def is_previewable_pdf_docx(ext: str) -> bool:
    """Check if extension is PDF or DOCX."""
    return ext.lower() in PREVIEW_PDF_DOCX_EXTENSIONS


def is_previewable(ext: str) -> bool:
    """Check if extension is previewable."""
    return ext.lower() in PREVIEWABLE_EXTENSIONS

