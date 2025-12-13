"""
FileExtensions - Supported file extensions constants.

Centralized definition of supported file extensions for TabManager.
"""

# Supported file extensions (extensible)
SUPPORTED_EXTENSIONS = {
    # Documents
    '.docx', '.pdf', '.xlsx',
    '.doc', '.xls', '.ppt', '.pptx', '.rtf', '.csv',
    # Archives
    '.zip', '.rar', '.7z',
    # Media
    '.mp3', '.wav', '.mp4', '.mov', '.mkv', '.flac',
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.ico', '.svg', '.webp',
    # Books
    '.epub', '.mobi', '.azw3',
    # Code & Text
    '.py', '.js', '.ts', '.html', '.css',
    '.txt', '.md', '.json', '.xml', '.yaml', '.yml', '.ini', '.log',
    # Executables & Shortcuts
    '.exe', '.msi', '.bat', '.cmd',
    '.lnk'  # Windows shortcuts
}

