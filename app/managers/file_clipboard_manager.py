"""
FileClipboardManager - Clipboard manager for copy/cut/paste operations.

Manages clipboard state (paths and mode) internally and integrates with Windows clipboard.
Supports interoperability with Windows Explorer using standard clipboard formats.
"""

import os
from typing import Optional

from PySide6.QtCore import QUrl, QMimeData
from PySide6.QtWidgets import QApplication

from app.core.logger import get_logger

logger = get_logger(__name__)

# Windows DropEffect values (4 bytes little-endian)
DROP_EFFECT_COPY = (1).to_bytes(4, byteorder='little')
DROP_EFFECT_MOVE = (2).to_bytes(4, byteorder='little')

# Windows clipboard format for Preferred DropEffect
PREFERRED_DROP_EFFECT_FORMAT = 'application/x-qt-windows-mime;value="Preferred DropEffect"'


class FileClipboardManager:
    """
    Manager for internal clipboard state (copy/cut operations).
    
    Singleton pattern - single instance shared across the application.
    """
    
    _instance: Optional['FileClipboardManager'] = None
    
    def __new__(cls):
        """Singleton pattern - return existing instance or create new one."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize clipboard state (only called once due to singleton)."""
        if self._initialized:
            return
        
        self._paths: list[str] = []
        self._mode: Optional[str] = None  # "copy" | "cut" | None
        self._initialized = True
    
    def set_copy(self, paths: list[str]) -> None:
        """
        Set clipboard to copy mode with given paths.
        
        Also writes to Windows clipboard for interoperability with Explorer.
        
        Args:
            paths: List of file/folder paths to copy.
        """
        if not paths:
            self.clear()
            return
        
        self._paths = paths.copy()
        self._mode = "copy"
        logger.debug(f"Clipboard set to COPY mode with {len(paths)} path(s)")
        
        # Escribir también en el clipboard del sistema
        self._write_to_system_clipboard(paths, "copy")
    
    def set_cut(self, paths: list[str]) -> None:
        """
        Set clipboard to cut mode with given paths.
        
        Also writes to Windows clipboard with MOVE DropEffect for real cut operation.
        
        Args:
            paths: List of file/folder paths to cut.
        """
        if not paths:
            self.clear()
            return
        
        self._paths = paths.copy()
        self._mode = "cut"
        logger.debug(f"Clipboard set to CUT mode with {len(paths)} path(s)")
        
        # Escribir también en el clipboard del sistema con MOVE
        self._write_to_system_clipboard(paths, "cut")
    
    def has_data(self) -> bool:
        """
        Check if clipboard has data (internal or system).
        
        Returns:
            True if clipboard contains paths, False otherwise.
        """
        # Verificar clipboard interno primero
        if len(self._paths) > 0 and self._mode is not None:
            return True
        
        # Si interno está vacío, verificar sistema
        system_data = self._read_from_system_clipboard()
        return system_data is not None
    
    def get_paths(self) -> list[str]:
        """
        Get paths stored in clipboard.
        
        Returns:
            List of paths (empty list if no data).
        """
        return self._paths.copy()
    
    def get_mode(self) -> Optional[str]:
        """
        Get clipboard mode.
        
        Returns:
            "copy", "cut", or None if clipboard is empty.
        """
        return self._mode
    
    def clear(self) -> None:
        """Clear clipboard state (both internal and system)."""
        self._paths = []
        self._mode = None
        
        # Limpiar también el clipboard del sistema
        try:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.clear()
        except Exception as e:
            logger.warning(f"Error clearing system clipboard: {e}")
        
        logger.debug("Clipboard cleared")
    
    def _write_to_system_clipboard(self, paths: list[str], mode: str) -> None:
        """
        Write paths to Windows clipboard with proper format.
        
        Args:
            paths: List of file/folder paths.
            mode: "copy" or "cut" to set DropEffect.
        """
        try:
            clipboard = QApplication.clipboard()
            if not clipboard:
                logger.warning("QApplication.clipboard() returned None")
                return
            
            mime_data = QMimeData()
            
            # Convertir paths a URLs locales
            urls = [QUrl.fromLocalFile(path) for path in paths if os.path.exists(path)]
            if not urls:
                logger.warning("No valid paths to write to clipboard")
                return
            
            mime_data.setUrls(urls)
            
            # Añadir Preferred DropEffect según modo
            if mode == "cut":
                mime_data.setData(PREFERRED_DROP_EFFECT_FORMAT, DROP_EFFECT_MOVE)
            elif mode == "copy":
                mime_data.setData(PREFERRED_DROP_EFFECT_FORMAT, DROP_EFFECT_COPY)
            
            clipboard.setMimeData(mime_data)
            logger.debug(f"Written {len(urls)} path(s) to system clipboard with mode {mode}")
            
        except Exception as e:
            logger.error(f"Error writing to system clipboard: {e}", exc_info=True)
    
    def _read_from_system_clipboard(self) -> tuple[list[str], str]:
        """
        Read paths from Windows clipboard.
        
        Returns:
            Tuple of (paths, mode).
            If no valid data, returns ([], "copy").
            mode is always "copy" or "cut".
        """
        try:
            clipboard = QApplication.clipboard()
            if not clipboard:
                return [], "copy"
            
            mime_data = clipboard.mimeData()
            if not mime_data:
                return [], "copy"
            
            # Verificar si tiene URLs
            if not mime_data.hasUrls():
                return [], "copy"
            
            # Extraer rutas locales válidas
            urls = mime_data.urls()
            paths = []
            for url in urls:
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if os.path.exists(path):
                        paths.append(path)
            
            if not paths:
                return [], "copy"
            
            # Detectar modo leyendo Preferred DropEffect
            mode = "copy"
            if mime_data.hasFormat(PREFERRED_DROP_EFFECT_FORMAT):
                drop_effect_data = mime_data.data(PREFERRED_DROP_EFFECT_FORMAT)
                if drop_effect_data == DROP_EFFECT_MOVE:
                    mode = "cut"
                elif drop_effect_data == DROP_EFFECT_COPY:
                    mode = "copy"
            
            logger.debug(f"Read {len(paths)} path(s) from system clipboard with mode {mode}")
            return paths, mode
            
        except Exception as e:
            logger.error(f"Error reading from system clipboard: {e}", exc_info=True)
            return [], "copy"
    
    def get_system_clipboard_data(self) -> tuple[list[str], str]:
        """
        Get paths and mode from system clipboard.
        
        Returns:
            Tuple of (paths, mode).
            If no valid data, returns ([], "copy").
            mode is always "copy" or "cut".
        """
        return self._read_from_system_clipboard()

