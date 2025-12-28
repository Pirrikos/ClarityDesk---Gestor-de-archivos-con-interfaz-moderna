"""
AppSettings - Global application settings manager.

Manages application-wide settings with QSettings persistence.
Uses Qt signals to notify components of setting changes.
"""

from typing import Optional

from PySide6.QtCore import QObject, QSettings, Signal


class AppSettings(QObject):
    """Global application settings manager with QSettings persistence and signal-based notifications."""
    
    dock_background_opacity_changed = Signal(float)  # Emitted when opacity changes
    dock_anchor_changed = Signal(str)  # Emitted when anchor changes ("top" or "bottom")
    central_area_color_changed = Signal(str)  # Emitted when central area color changes ("dark" or "light")
    
    # QSettings keys
    KEY_DOCK_OPACITY = "dock/background_opacity"
    KEY_DOCK_ANCHOR = "dock/anchor"
    KEY_CENTRAL_AREA_COLOR = "app/central_area_color"
    
    # Default values
    DEFAULT_OPACITY = 1.0
    DEFAULT_ANCHOR = "bottom"
    DEFAULT_CENTRAL_AREA_COLOR = "dark"
    
    def __init__(self):
        """Initialize AppSettings and load values from QSettings."""
        super().__init__()
        self._settings = QSettings("ClarityDesk", "ClarityDesk Pro")
        
        # Load values from QSettings or use defaults
        self._dock_background_opacity = self._settings.value(
            self.KEY_DOCK_OPACITY,
            self.DEFAULT_OPACITY,
            type=float
        )
        self._dock_anchor = self._settings.value(
            self.KEY_DOCK_ANCHOR,
            self.DEFAULT_ANCHOR,
            type=str
        )
        
        # Load central area color
        self._central_area_color = self._settings.value(
            self.KEY_CENTRAL_AREA_COLOR,
            self.DEFAULT_CENTRAL_AREA_COLOR,
            type=str
        )
        
        # Validate loaded values
        self._dock_background_opacity = max(0.0, min(1.0, float(self._dock_background_opacity)))
        if self._dock_anchor not in ("top", "bottom"):
            self._dock_anchor = self.DEFAULT_ANCHOR
        if self._central_area_color not in ("dark", "light"):
            self._central_area_color = self.DEFAULT_CENTRAL_AREA_COLOR
    
    @property
    def dock_background_opacity(self) -> float:
        """Get current dock background opacity (0.0-1.0)."""
        return self._dock_background_opacity
    
    def set_dock_background_opacity(self, value: float) -> None:
        """
        Set dock background opacity and emit signal if changed.
        Saves to QSettings immediately.
        
        Args:
            value: Opacity value (0.0-1.0), will be clamped to valid range.
        """
        value = max(0.0, min(1.0, value))  # Clamp to valid range
        if value != self._dock_background_opacity:
            self._dock_background_opacity = value
            # Save to QSettings
            self._settings.setValue(self.KEY_DOCK_OPACITY, value)
            self._settings.sync()
            # Emit signal
            self.dock_background_opacity_changed.emit(value)
    
    @property
    def dock_anchor(self) -> str:
        """Get current dock anchor position ("top" or "bottom")."""
        return self._dock_anchor
    
    def set_dock_anchor(self, value: str) -> None:
        """
        Set dock anchor position and emit signal if changed.
        Saves to QSettings immediately.
        
        Args:
            value: Anchor position ("top" or "bottom").
        """
        if value not in ("top", "bottom"):
            return  # Invalid value, ignore
        if value != self._dock_anchor:
            self._dock_anchor = value
            # Save to QSettings
            self._settings.setValue(self.KEY_DOCK_ANCHOR, value)
            self._settings.sync()
            # Emit signal
            self.dock_anchor_changed.emit(value)
    
    @property
    def central_area_color(self) -> str:
        """Get current central area color theme ("dark" or "light")."""
        return self._central_area_color
    
    def set_central_area_color(self, value: str) -> None:
        """
        Set central area color theme and emit signal if changed.
        Saves to QSettings immediately.
        
        Args:
            value: Color theme ("dark" or "light").
        """
        if value not in ("dark", "light"):
            return  # Invalid value, ignore
        if value != self._central_area_color:
            self._central_area_color = value
            # Save to QSettings
            self._settings.setValue(self.KEY_CENTRAL_AREA_COLOR, value)
            self._settings.sync()
            # Emit signal
            self.central_area_color_changed.emit(value)


# Global instance - will be initialized in main.py before creating windows
app_settings: Optional[AppSettings] = None

