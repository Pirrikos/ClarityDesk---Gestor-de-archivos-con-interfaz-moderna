"""
DOCX Converter - Converts DOCX files to PDF using docx2pdf.

Handles conversion and caching of DOCX to PDF for preview rendering.
Includes cache size management and auto-cleanup.
"""

import os
import hashlib
import tempfile
from pathlib import Path

from app.core.logger import get_logger

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
    
    def get_cached_pdf_path(self, docx_path: str) -> Path:
        """Get cached PDF path for a DOCX file."""
        file_hash = hashlib.md5(docx_path.encode()).hexdigest()
        return self._cache_dir / f"{file_hash}.pdf"
    
    def convert_to_pdf(self, docx_path: str) -> str:
        """Convert DOCX to PDF using docx2pdf.
        
        R5: All external access (docx2pdf, file system) is encapsulated in try/except.
        R6: Validates file exists and mtime before/after conversion.
        """
        if not docx_path:
            return ""
        
        try:
            if not os.path.exists(docx_path):
                return ""
        except (OSError, ValueError):
            return ""
        
        if not docx_path.lower().endswith('.docx'):
            return ""
        
        try:
            from docx2pdf import convert
        except ImportError:
            return ""
        
        try:
            self._cleanup_cache_if_needed()
            
            pdf_path = self.get_cached_pdf_path(docx_path)
            
            if pdf_path.exists():
                try:
                    docx_mtime = os.path.getmtime(docx_path)
                    pdf_mtime = os.path.getmtime(str(pdf_path))
                    if pdf_mtime >= docx_mtime:
                        return str(pdf_path)
                except (OSError, ValueError):
                    pass  # Continue to regenerate
            
            try:
                convert(docx_path, str(pdf_path))
            except Exception as e:
                logger.warning(f"DOCX conversion failed: {e}")
                return ""
            
            try:
                if pdf_path.exists():
                    return str(pdf_path)
            except (OSError, ValueError):
                pass
            
            return ""
        except Exception as e:
            logger.error(f"Exception in convert_to_pdf: {e}", exc_info=True)
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

