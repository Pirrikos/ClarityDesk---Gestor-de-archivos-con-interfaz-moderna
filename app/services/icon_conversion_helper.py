"""
IconConversionHelper - Helper functions for Windows icon conversion.

Extracted from windows_icon_converter to reduce method size.
"""

import array

import win32gui
import win32ui
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPixmap


def try_convert_from_color_bitmap(hicon, size):
    """Try to convert icon from color bitmap if available."""
    try:
        icon_info = win32gui.GetIconInfo(hicon)
        if icon_info is None:
            return None
        
        hbm_color = icon_info[4]
        if not hbm_color or hbm_color == 0:
            return None
        
        from app.services.windows_icon_converter import hbitmap_to_qpixmap
        
        color_bmp = win32ui.CreateBitmapFromHandle(hbm_color)
        bmp_info = color_bmp.GetInfo()
        native_width = bmp_info['bmWidth']
        native_height = bmp_info['bmHeight']
        bmp_bpp = bmp_info['bmBitsPixel']
        
        if native_width >= 16 and native_height >= 16 and bmp_bpp >= 24:
            pixmap = hbitmap_to_qpixmap(hbm_color, QSize(native_width, native_height))
            if not pixmap.isNull():
                return _scale_if_needed(pixmap, size)
        return None
    except Exception:
        return None


def _scale_if_needed(pixmap: QPixmap, size: int) -> QPixmap:
    """Scale pixmap if size difference is significant."""
    scale_factor = min(size / pixmap.width(), size / pixmap.height())
    scaled_width = int(pixmap.width() * scale_factor)
    scaled_height = int(pixmap.height() * scale_factor)
    
    if abs(pixmap.width() - scaled_width) > 2 or abs(pixmap.height() - scaled_height) > 2:
        return pixmap.scaled(
            scaled_width, scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    return pixmap


def draw_icon_to_bitmap(hicon, hdc, size):
    """Draw icon to bitmap using Windows API."""
    screen_dc_handle = win32gui.GetDC(0)
    try:
        screen_dc = win32ui.CreateDCFromHandle(screen_dc_handle)
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(screen_dc, size, size)
        
        bmp_info = hbmp.GetInfo()
        if bmp_info['bmBitsPixel'] != 32:
            return None
        
        hbmp_handle = hbmp.GetHandle()
        mem_dc = win32ui.CreateDCFromHandle(hdc)
        old_bmp = mem_dc.SelectObject(hbmp)
        mem_dc.FillSolidRect((0, 0, size, size), 0x00000000)
        
        hdc_handle = mem_dc.GetHandleOutput()
        result = win32gui.DrawIcon(hdc_handle, 0, 0, hicon)
        
        if not result:
            win32gui.DrawIconEx(
                hdc_handle, 0, 0, hicon, size, size, 0, None, 0x0003
            )
        
        mem_dc.SelectObject(old_bmp)
        return hbmp_handle
    finally:
        win32gui.ReleaseDC(0, screen_dc_handle)

