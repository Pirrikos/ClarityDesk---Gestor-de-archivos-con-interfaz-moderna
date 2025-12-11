"""
WindowsIconExtractor - Windows API icon extraction methods.

Handles extraction of icons using various Windows Shell APIs.
"""

import ctypes

import win32api
import win32gui
from PySide6.QtGui import QPixmap

from app.services.icon_extraction_fallbacks import (
    get_icon_via_extracticon,
    get_icon_via_qicon,
    get_icon_via_shgetfileinfo,
)


def get_icon_via_imagelist(path: str, size: int, converter_func) -> QPixmap:
    """Get icon using SHGetImageList for maximum resolution (256px)."""
    try:
        shell32 = ctypes.windll.shell32
        shell32_dll = _load_shell32_dll()
        if not shell32_dll:
            return QPixmap()
        
        try:
            SHGetImageList = _create_shgetimagelist_function(shell32_dll)
            if not SHGetImageList:
                return QPixmap()
            
            icon_index = _get_icon_index_from_path(path, shell32)
            if icon_index is None:
                return QPixmap()
            
            return _try_get_icon_from_imagelists(icon_index, size, converter_func, SHGetImageList)
        finally:
            _free_shell32_dll(shell32_dll)
    except Exception:
        return QPixmap()


def _load_shell32_dll():
    """Load shell32.dll and return handle."""
    try:
        return win32api.LoadLibrary("shell32.dll")
    except Exception:
        return None


def _create_shgetimagelist_function(shell32_dll):
    """Create SHGetImageList function from DLL."""
    ordinal = 727
    proc = win32api.GetProcAddress(shell32_dll, ordinal)
    if not proc:
        return None
    
    proc_addr = proc.value if hasattr(proc, 'value') else int(proc)
    if not proc_addr:
        return None
    
    return ctypes.WINFUNCTYPE(
        ctypes.c_long,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_ubyte * 16),
        ctypes.POINTER(ctypes.c_void_p)
    )(proc_addr)


def _get_icon_index_from_path(path: str, shell32):
    """Get icon index from file path."""
    import os
    SHGFI_SYSICONINDEX = 0x000004000
    SHGFI_USEFILEATTRIBUTES = 0x000000010
    FILE_ATTRIBUTE_NORMAL = 0x80
    FILE_ATTRIBUTE_DIRECTORY = 0x10
    
    class SHFILEINFO(ctypes.Structure):
        _fields_ = [
            ("hIcon", ctypes.c_void_p),
            ("iIcon", ctypes.c_int),
            ("dwAttributes", ctypes.c_ulong),
            ("szDisplayName", ctypes.c_wchar * 260),
            ("szTypeName", ctypes.c_wchar * 80)
        ]
    
    # Use correct file attribute based on whether it's a folder or file
    file_attributes = FILE_ATTRIBUTE_DIRECTORY if os.path.isdir(path) else FILE_ATTRIBUTE_NORMAL
    
    file_info = SHFILEINFO()
    result = shell32.SHGetFileInfoW(
        path, file_attributes, ctypes.byref(file_info),
        ctypes.sizeof(file_info), SHGFI_SYSICONINDEX | SHGFI_USEFILEATTRIBUTES
    )
    return file_info.iIcon if result != 0 else None


def _try_get_icon_from_imagelists(icon_index, size, converter_func, SHGetImageList):
    """Try to get icon from image lists (JUMBO and EXTRALARGE)."""
    SHIL_JUMBO = 0x4
    SHIL_EXTRALARGE = 0x2
    ILD_NORMAL = 0x0000
    
    for image_list_size in [SHIL_JUMBO, SHIL_EXTRALARGE]:
        pixmap = _try_single_imagelist(image_list_size, icon_index, size, converter_func, SHGetImageList, ILD_NORMAL)
        if not pixmap.isNull():
            return pixmap
    return QPixmap()


def _try_single_imagelist(image_list_size, icon_index, size, converter_func, SHGetImageList, ILD_NORMAL):
    """Try to get icon from a single image list size."""
    try:
        IID_IImageList_bytes = bytes([0x26, 0x59, 0xEB, 0x46, 0x2E, 0x58, 0x17, 0x40, 0x9F, 0xDF, 0xE8, 0x99, 0x8D, 0xAA, 0x09, 0x50])
        IID_IImageList = (ctypes.c_ubyte * 16)(*IID_IImageList_bytes)
        
        image_list_ptr = ctypes.c_void_p()
        hres = SHGetImageList(image_list_size, ctypes.byref(IID_IImageList), ctypes.byref(image_list_ptr))
        if hres != 0 or not image_list_ptr.value:
            return QPixmap()
        
        comctl32 = ctypes.windll.comctl32
        ImageList_GetIcon = comctl32.ImageList_GetIcon
        ImageList_GetIcon.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint]
        ImageList_GetIcon.restype = ctypes.c_void_p
        
        hicon = ImageList_GetIcon(image_list_ptr.value, icon_index, ILD_NORMAL)
        if not hicon:
            return QPixmap()
        
        pixmap = converter_func(hicon, size)
        win32gui.DestroyIcon(hicon)
        return pixmap
    except Exception:
        return QPixmap()


def _free_shell32_dll(shell32_dll):
    """Free shell32.dll handle."""
    if shell32_dll:
        try:
            win32api.FreeLibrary(shell32_dll)
        except:
            pass

