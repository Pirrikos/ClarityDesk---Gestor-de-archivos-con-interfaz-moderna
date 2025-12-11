"""
IconExtractionFallbacks - Fallback icon extraction methods.

Extracted from windows_icon_extractor to reduce file size.
"""

import ctypes
import os

import win32com.client
import win32gui
from PySide6.QtCore import QFileInfo, QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileIconProvider


def get_icon_via_extracticon(path: str, size: QSize, converter_func) -> QPixmap:
    """Get icon using ExtractIconEx for executables."""
    try:
        path = _resolve_shortcut(path)
        if not path or not (path.lower().endswith(('.exe', '.dll', '.ico', '.lnk'))):
            return QPixmap()
        
        shell32 = ctypes.windll.shell32
        ExtractIconEx = shell32.ExtractIconExW
        ExtractIconEx.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint]
        ExtractIconEx.restype = ctypes.c_uint
        
        hicon_large = ctypes.c_void_p()
        hicon_small = ctypes.c_void_p()
        result = ExtractIconEx(path, 0, ctypes.byref(hicon_large), ctypes.byref(hicon_small), 1)
        
        if result == 0 or not hicon_large.value:
            return QPixmap()
        
        icon_size = max(size.width(), size.height())
        pixmap = converter_func(hicon_large.value, icon_size)
        
        win32gui.DestroyIcon(hicon_large.value)
        if hicon_small.value:
            win32gui.DestroyIcon(hicon_small.value)
        
        return pixmap
    except Exception:
        return QPixmap()


def get_icon_via_qicon(path: str, size: QSize, icon_provider: QFileIconProvider) -> QPixmap:
    """Get icon using QIcon/QFileIconProvider."""
    try:
        path = _resolve_shortcut(path)
        qfile_info = QFileInfo(path)
        icon = icon_provider.icon(qfile_info)
        
        if icon.isNull():
            return QPixmap()
        
        pixmap = _get_best_pixmap_from_icon(icon, size)
        if pixmap.isNull():
            return QPixmap()
        
        return _scale_to_size(pixmap, size)
    except Exception:
        return QPixmap()


def get_icon_via_shgetfileinfo(path: str, size: QSize, converter_func) -> QPixmap:
    """Fallback: Get icon using SHGetFileInfo (48px max)."""
    try:
        shell32 = ctypes.windll.shell32
        SHGFI_ICON = 0x000000100
        SHGFI_LARGEICON = 0x000000000
        flags = SHGFI_ICON | SHGFI_LARGEICON
        
        class SHFILEINFO(ctypes.Structure):
            _fields_ = [
                ("hIcon", ctypes.c_void_p),
                ("iIcon", ctypes.c_int),
                ("dwAttributes", ctypes.c_ulong),
                ("szDisplayName", ctypes.c_char * 260),
                ("szTypeName", ctypes.c_char * 80)
            ]
        
        file_info = SHFILEINFO()
        result = shell32.SHGetFileInfoW(
            path, 0, ctypes.byref(file_info), ctypes.sizeof(file_info), flags
        )
        
        if result == 0 or file_info.hIcon == 0:
            return QPixmap()
        
        hicon = file_info.hIcon
        icon_size = max(size.width(), size.height())
        pixmap = converter_func(hicon, icon_size)
        win32gui.DestroyIcon(hicon)
        
        return _scale_to_size(pixmap, size)
    except Exception:
        return QPixmap()


def _resolve_shortcut(path: str) -> str:
    """Resolve .lnk shortcut to target path."""
    if path.lower().endswith('.lnk'):
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(path)
            target_path = shortcut.Targetpath
            if target_path and os.path.exists(target_path):
                return target_path
        except Exception:
            pass
    return path


def _get_best_pixmap_from_icon(icon, size: QSize) -> QPixmap:
    """Get best available pixmap from icon."""
    available_sizes = icon.availableSizes()
    if available_sizes:
        best_size = max(available_sizes, key=lambda s: s.width() * s.height())
        return icon.pixmap(best_size)
    
    for test_size in [QSize(256, 256), QSize(128, 128), QSize(64, 64), QSize(48, 48)]:
        pixmap = icon.pixmap(test_size)
        if not pixmap.isNull():
            return pixmap
    
    return icon.pixmap(QSize(size.width() * 2, size.height() * 2))


def _scale_to_size(pixmap: QPixmap, size: QSize) -> QPixmap:
    """Scale pixmap to target size if needed."""
    if pixmap.width() != size.width() or pixmap.height() != size.height():
        return pixmap.scaled(
            size.width(), size.height(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    return pixmap

