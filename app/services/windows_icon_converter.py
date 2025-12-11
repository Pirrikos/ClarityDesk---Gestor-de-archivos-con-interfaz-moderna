"""
WindowsIconConverter - Convert Windows HICON/HBITMAP to QPixmap.

Handles conversion of Windows icon handles to Qt pixmaps.
"""

import array
import ctypes
from typing import Optional

import win32gui
import win32ui
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPixmap


def hicon_to_qpixmap_at_size(hicon: int, size: int) -> QPixmap:
    """Convert Windows HICON to QPixmap at specific size."""
    try:
        hdc = win32gui.CreateCompatibleDC(0)
        if hdc == 0:
            return QPixmap()
        
        try:
            from app.services.icon_conversion_helper import try_convert_from_color_bitmap, draw_icon_to_bitmap
            
            pixmap = try_convert_from_color_bitmap(hicon, size)
            if pixmap:
                return pixmap
            
            hbmp_handle = draw_icon_to_bitmap(hicon, hdc, size)
            if hbmp_handle:
                return hbitmap_to_qpixmap(hbmp_handle, QSize(size, size))
            
            return QPixmap()
        finally:
            win32gui.DeleteDC(hdc)
    except Exception:
        return QPixmap()


def hbitmap_to_qpixmap(hbitmap: int, size: QSize) -> QPixmap:
    """Convert Windows HBITMAP to QPixmap."""
    try:
        bmp = win32ui.CreateBitmapFromHandle(hbitmap)
        bmp_info = bmp.GetInfo()
        width = bmp_info['bmWidth']
        height = bmp_info['bmHeight']
        bits_per_pixel = bmp_info['bmBitsPixel']
        
        bmp_str = bmp.GetBitmapBits(True)
        if not bmp_str:
            return QPixmap()
        
        if bits_per_pixel == 32:
            argb_data = array.array('I', [0] * (width * height))
            for i in range(width * height):
                idx = i * 4
                if idx + 3 < len(bmp_str):
                    b = bmp_str[idx]
                    g = bmp_str[idx + 1]
                    r = bmp_str[idx + 2]
                    a = bmp_str[idx + 3]
                    argb_data[i] = (a << 24) | (r << 16) | (g << 8) | b
            image = QImage(argb_data.tobytes(), width, height, QImage.Format.Format_ARGB32)
        elif bits_per_pixel == 24:
            image = QImage(bmp_str, width, height, QImage.Format.Format_RGB888)
            image = image.rgbSwapped()
        else:
            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(Qt.transparent)
        
        if image.isNull():
            return QPixmap()
        
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return QPixmap()
        
        if pixmap.width() != size.width() or pixmap.height() != size.height():
            pixmap = pixmap.scaled(
                size.width(), size.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
        
        return pixmap
    except Exception:
        return QPixmap()

