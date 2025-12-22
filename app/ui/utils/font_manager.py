"""
FontManager - Centralized font management utility.

Provides safe font creation and application using setPixelSize() to avoid
Qt's automatic px to pt conversion issues during widget initialization.
"""

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget


class FontManager:
    """
    Stateless font management utility.
    
    Provides constants and methods for creating and applying fonts safely
    using setPixelSize() instead of setPointSize() to avoid conversion errors.
    """
    
    # Standard font size constants (in pixels)
    SIZE_SMALL = 9
    SIZE_NORMAL = 11
    SIZE_MEDIUM = 13
    SIZE_LARGE = 14
    SIZE_XLARGE = 16
    
    @staticmethod
    def create_font(
        family: str,
        pixel_size: int,
        weight: QFont.Weight = QFont.Weight.Normal
    ) -> QFont:
        """
        Create a QFont safely using setPixelSize().
        
        Args:
            family: Font family name (e.g., 'Segoe UI')
            pixel_size: Font size in pixels (must be > 0)
            weight: Font weight (default: Normal)
            
        Returns:
            QFont instance with pixel size set
            
        Raises:
            ValueError: If pixel_size <= 0
        """
        if pixel_size <= 0:
            raise ValueError(f"Font pixel size must be > 0, got {pixel_size}")
        
        font = QFont(family)
        font.setPixelSize(pixel_size)
        font.setWeight(weight)
        return font
    
    @staticmethod
    def safe_set_font(
        widget: QWidget,
        family: str,
        pixel_size: int,
        weight: QFont.Weight = QFont.Weight.Normal
    ) -> None:
        """
        Safely set font on a widget using setPixelSize().
        
        Args:
            widget: QWidget instance to apply font to
            family: Font family name (e.g., 'Segoe UI')
            pixel_size: Font size in pixels (must be > 0)
            weight: Font weight (default: Normal)
            
        Raises:
            ValueError: If pixel_size <= 0
        """
        if pixel_size <= 0:
            raise ValueError(f"Font pixel size must be > 0, got {pixel_size}")
        
        font = QFont(family)
        font.setPixelSize(pixel_size)
        font.setWeight(weight)
        widget.setFont(font)

