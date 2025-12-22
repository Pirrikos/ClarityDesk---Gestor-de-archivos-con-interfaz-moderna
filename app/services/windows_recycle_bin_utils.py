"""
WindowsRecycleBinUtils - Shared utilities for Windows Recycle Bin operations.

Centralizes Windows Shell API code to avoid duplication.
"""

from ctypes import Structure, byref, windll, wintypes


def prepare_file_path_for_recycle_bin(abs_path: str) -> str:
    """
    Prepare file path with double-null termination for Windows API.
    
    Args:
        abs_path: Absolute file path.
        
    Returns:
        Path formatted for Windows Shell API (backslashes, double-null terminated).
    """
    return abs_path.replace('/', '\\') + '\0\0'


def create_fileop_structure(file_path_unicode: str):
    """
    Create and configure SHFILEOPSTRUCTW structure for recycle bin operation.
    
    Args:
        file_path_unicode: File path prepared with prepare_file_path_for_recycle_bin().
        
    Returns:
        Configured SHFILEOPSTRUCTW structure instance.
    """
    FO_DELETE = 0x0003
    FOF_ALLOWUNDO = 0x0040
    FOF_SILENT = 0x0004
    FOF_NOCONFIRMATION = 0x0010
    
    class SHFILEOPSTRUCTW(Structure):
        _fields_ = [
            ("hWnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", wintypes.WORD),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", wintypes.LPVOID),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]
    
    fileop = SHFILEOPSTRUCTW()
    fileop.hWnd = None
    fileop.wFunc = FO_DELETE
    fileop.pFrom = file_path_unicode
    fileop.pTo = None
    fileop.fFlags = FOF_ALLOWUNDO | FOF_SILENT | FOF_NOCONFIRMATION
    fileop.fAnyOperationsAborted = wintypes.BOOL(False)
    fileop.hNameMappings = None
    fileop.lpszProgressTitle = None
    return fileop


def move_to_recycle_bin_via_api(file_path_unicode: str) -> tuple[int, bool]:
    """
    Execute Windows Shell API operation to move file to recycle bin.
    
    Args:
        file_path_unicode: File path prepared with prepare_file_path_for_recycle_bin().
        
    Returns:
        Tuple of (result_code, was_aborted).
    """
    fileop = create_fileop_structure(file_path_unicode)
    shell32 = windll.shell32
    result = shell32.SHFileOperationW(byref(fileop))
    return result, bool(fileop.fAnyOperationsAborted)

