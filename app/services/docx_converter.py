"""
DOCX Converter - Converts DOCX files to PDF using docx2pdf.

Handles conversion and caching of DOCX to PDF for preview rendering.
Includes cache size management and auto-cleanup.

Note: .doc (formato antiguo) NO está soportado porque docx2pdf solo acepta .docx.
"""

import os
import hashlib
import tempfile
import shutil
from pathlib import Path

from app.core.logger import get_logger
from app.services.preview_file_extensions import normalize_extension

logger = get_logger(__name__)


class DocxConverter:
    """Converts DOCX files to PDF for preview rendering."""
    
    # Maximum cache size: 500MB
    MAX_CACHE_SIZE_MB = 500
    MAX_CACHE_SIZE_BYTES = MAX_CACHE_SIZE_MB * 1024 * 1024
    
    def __init__(self):
        """Initialize converter with temporary cache directory."""
        self._cache_dir = Path(tempfile.gettempdir()) / "claritydesk_previews"
        self._cache_dir.mkdir(exist_ok=True)
        # Directory for temporary copies with normalized extensions
        self._temp_dir = self._cache_dir / "temp_docx"
        self._temp_dir.mkdir(exist_ok=True)
    
    def get_cached_pdf_path(self, docx_path: str) -> Path:
        """Get cached PDF path for a DOCX file."""
        file_hash = hashlib.md5(docx_path.encode()).hexdigest()
        return self._cache_dir / f"{file_hash}.pdf"
    
    def _get_normalized_temp_path(self, original_path: str) -> str:
        """
        Get a temporary copy of the file with normalized extension for docx2pdf.

        CRITICAL: Always creates a temp copy to prevent docx2pdf from creating
        auxiliary files in the user's workspace directory.

        Args:
            original_path: Original file path with potentially uppercase extension.

        Returns:
            Path to temporary copy with normalized extension.
        """
        try:
            path_obj = Path(original_path)
            if path_obj.suffix.lower() != '.docx':
                return original_path

            # ALWAYS create temp copy (never use original path)
            # This prevents docx2pdf/Word from creating auxiliary files in user workspace
            file_hash = hashlib.md5(original_path.encode()).hexdigest()
            temp_name = f"{file_hash}.docx"
            temp_path = self._temp_dir / temp_name

            # Check if temp file exists and is newer than original
            if temp_path.exists():
                try:
                    original_mtime = os.path.getmtime(original_path)
                    temp_mtime = os.path.getmtime(str(temp_path))
                    if temp_mtime >= original_mtime:
                        logger.debug(f"Using cached temp copy: {temp_path}")
                        return str(temp_path)
                except (OSError, ValueError) as e:
                    logger.debug(f"Error checking temp file mtime: {e}")
                    pass

            # Create temp copy with normalized extension
            shutil.copy2(original_path, temp_path)
            logger.debug(f"Created temp copy: {original_path} -> {temp_path}")
            return str(temp_path)
        except Exception as e:
            logger.error(f"Failed to create temp copy for DOCX: {e}", exc_info=True)
            # Fallback: return original path (will likely fail with docx2pdf)
            return original_path
    
    def _normalize_path_extension(self, path: str) -> str:
        """
        Normalize file extension to lowercase in path.
        
        Note: This may not work with docx2pdf's Path.resolve() which returns
        the actual filename from filesystem. Use _create_normalized_symlink() instead.
        
        Args:
            path: File path with potentially uppercase extension.
        
        Returns:
            Path with normalized extension (lowercase).
        """
        # Find the last dot to get the extension
        last_dot_index = path.rfind('.')
        if last_dot_index != -1:
            extension = path[last_dot_index:]
            extension_lower = extension.lower()
            # If extension is .docx (case-insensitive) but not exactly .docx, normalize it
            if extension_lower == '.docx' and extension != '.docx':
                base_path = path[:last_dot_index]
                normalized_path = base_path + '.docx'
                logger.debug(f"Normalizing extension: '{path}' -> '{normalized_path}'")
                return normalized_path
        return path
    
    def convert_to_pdf(self, docx_path: str) -> str:
        """Convert DOCX to PDF using docx2pdf.

        R5: All external access (docx2pdf, file system) is encapsulated in try/except.
        R6: Validates file exists and mtime before/after conversion.
        """
        if not docx_path:
            return ""

        try:
            if not os.path.exists(docx_path):
                logger.debug(f"DOCX file does not exist: {docx_path}")
                return ""
        except (OSError, ValueError) as e:
            logger.warning(f"Cannot check DOCX file existence: {docx_path}, error: {e}")
            return ""

        # R11: Normalize extension in single entry point
        ext = normalize_extension(docx_path)
        if ext != '.docx':
            return ""

        try:
            from docx2pdf import convert
        except ImportError as e:
            logger.error(f"Failed to import docx2pdf: {e}")
            return ""

        try:
            self._cleanup_cache_if_needed()

            pdf_path = self.get_cached_pdf_path(docx_path)

            if pdf_path.exists():
                try:
                    docx_mtime = os.path.getmtime(docx_path)
                    pdf_mtime = os.path.getmtime(str(pdf_path))
                    if pdf_mtime >= docx_mtime:
                        logger.debug(f"Using cached PDF for: {docx_path}")
                        return str(pdf_path)
                except (OSError, ValueError) as e:
                    logger.debug(f"Error checking PDF cache mtime: {e}")
                    pass  # Continue to regenerate

            try:
                # docx2pdf's Path.resolve() returns the actual filename from filesystem,
                # which may have uppercase extension. Create a temp copy with normalized extension.
                normalized_docx_path = self._get_normalized_temp_path(docx_path)

                logger.debug(f"Converting DOCX to PDF: {docx_path}")
                convert(normalized_docx_path, str(pdf_path))
                logger.debug(f"DOCX conversion completed: {pdf_path}")
            except Exception as e:
                logger.error(f"DOCX conversion failed: {type(e).__name__}: {e}", exc_info=True)
                return ""

            try:
                if pdf_path.exists():
                    return str(pdf_path)
                else:
                    logger.warning(f"PDF does not exist after conversion: {docx_path}")
            except (OSError, ValueError) as e:
                logger.warning(f"Error checking PDF existence: {e}")
                pass

            return ""
        except Exception as e:
            logger.error(f"DOCX converter exception: {e}", exc_info=True)
            return ""
    
    def _get_cache_size(self) -> int:
        """Calculate total size of cache directory in bytes."""
        total_size = 0
        try:
            for file_path in self._cache_dir.iterdir():
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception:
            pass
        return total_size
    
    def _cleanup_cache_if_needed(self) -> None:
        """Cleanup cache if it exceeds maximum size limit."""
        cache_size = self._get_cache_size()
        
        if cache_size <= self.MAX_CACHE_SIZE_BYTES:
            return
        
        # Sort files by modification time (oldest first)
        try:
            files_with_mtime = []
            for file_path in self._cache_dir.iterdir():
                if file_path.is_file():
                    files_with_mtime.append((file_path, file_path.stat().st_mtime))
            
            # Sort by mtime (oldest first)
            files_with_mtime.sort(key=lambda x: x[1])
            
            # Delete oldest files until under limit
            for file_path, _ in files_with_mtime:
                if cache_size <= self.MAX_CACHE_SIZE_BYTES:
                    break
                
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    cache_size -= file_size
                except Exception:
                    pass
        except Exception:
            pass
    
    def clear_cache(self) -> None:
        """Clear temporary PDF cache directory."""
        try:
            import shutil
            if self._cache_dir.exists():
                shutil.rmtree(self._cache_dir)
                self._cache_dir.mkdir(exist_ok=True)
        except Exception:
            pass

