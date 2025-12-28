"""
SettingsWindow - Settings window for Dock transparency adjustment.

Simple non-modal window with a slider to adjust dock background opacity.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.managers import app_settings as app_settings_module


# Singleton instance
_settings_window_instance: Optional['SettingsWindow'] = None


def get_settings_window() -> 'SettingsWindow':
    """Get or create SettingsWindow singleton instance."""
    global _settings_window_instance
    
    if _settings_window_instance is None:
        _settings_window_instance = SettingsWindow()
    
    # Bring window to front
    _settings_window_instance.raise_()
    _settings_window_instance.activateWindow()
    
    return _settings_window_instance


class SettingsWindow(QWidget):
    """Settings window for adjusting dock background opacity."""
    
    def __init__(self, parent=None):
        """Initialize settings window."""
        super().__init__(parent)
        self.setWindowTitle("Ajustes - ClarityDesk")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self._setup_ui()
        
        # Load initial values from AppSettings
        if app_settings_module.app_settings is not None:
            # Opacity
            initial_opacity = app_settings_module.app_settings.dock_background_opacity
            slider_value = int(initial_opacity * 100)
            self._opacity_slider.setValue(slider_value)
            
            # Anchor
            initial_anchor = app_settings_module.app_settings.dock_anchor
            if initial_anchor == "top":
                self._anchor_top_radio.setChecked(True)
            else:
                self._anchor_bottom_radio.setChecked(True)
    
    def _setup_ui(self) -> None:
        """Build window UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title label
        title_label = QLabel("Transparencia del fondo del Dock", self)
        title_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            font-weight: 600;
            color: #ffffff;
        """)
        layout.addWidget(title_label)
        
        # Slider container with labels
        slider_container = QWidget(self)
        slider_layout = QVBoxLayout(slider_container)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(5)
        
        # Slider
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        self._opacity_slider.setMinimum(0)
        self._opacity_slider.setMaximum(100)
        self._opacity_slider.setValue(100)  # Default: fully opaque
        self._opacity_slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self._opacity_slider)
        
        # Labels for min/max
        labels_container = QWidget(self)
        labels_layout = QVBoxLayout(labels_container)
        labels_layout.setContentsMargins(0, 0, 0, 0)
        labels_layout.setSpacing(0)
        
        min_max_layout = QVBoxLayout()
        min_max_layout.setContentsMargins(0, 0, 0, 0)
        min_max_layout.setSpacing(0)
        
        min_label = QLabel("0%", self)
        min_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
            color: #aaaaaa;
        """)
        
        max_label = QLabel("100%", self)
        max_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
            color: #aaaaaa;
        """)
        max_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        from PySide6.QtWidgets import QHBoxLayout
        labels_row = QHBoxLayout()
        labels_row.setContentsMargins(0, 0, 0, 0)
        labels_row.addWidget(min_label)
        labels_row.addStretch()
        labels_row.addWidget(max_label)
        labels_layout.addLayout(labels_row)
        
        slider_layout.addWidget(labels_container)
        layout.addWidget(slider_container)
        
        # Anchor position section
        anchor_label = QLabel("Posición del Dock", self)
        anchor_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            font-weight: 600;
            color: #ffffff;
        """)
        layout.addWidget(anchor_label)
        
        # Radio buttons for anchor
        anchor_container = QWidget(self)
        anchor_layout = QVBoxLayout(anchor_container)
        anchor_layout.setContentsMargins(0, 0, 0, 0)
        anchor_layout.setSpacing(8)
        
        self._anchor_top_radio = QRadioButton("Dock arriba", self)
        self._anchor_bottom_radio = QRadioButton("Dock abajo", self)
        
        self._anchor_top_radio.setStyleSheet("""
            QRadioButton {
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                color: #ffffff;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self._anchor_bottom_radio.setStyleSheet("""
            QRadioButton {
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                color: #ffffff;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        
        self._anchor_group = QButtonGroup(self)
        self._anchor_group.addButton(self._anchor_top_radio, 0)
        self._anchor_group.addButton(self._anchor_bottom_radio, 1)
        
        self._anchor_top_radio.toggled.connect(self._on_anchor_changed)
        self._anchor_bottom_radio.toggled.connect(self._on_anchor_changed)
        
        anchor_layout.addWidget(self._anchor_top_radio)
        anchor_layout.addWidget(self._anchor_bottom_radio)
        layout.addWidget(anchor_container)
        
        # Set window size (increased for new controls)
        self.setFixedSize(300, 200)
        
        # Set window style (dark theme)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
        """)
    
    def _on_slider_changed(self, value: int) -> None:
        """Handle slider value change."""
        if app_settings_module.app_settings is not None:
            # Convert 0-100 to 0.0-1.0
            opacity = value / 100.0
            app_settings_module.app_settings.set_dock_background_opacity(opacity)
    
    def _on_anchor_changed(self, checked: bool) -> None:
        """Handle anchor radio button change."""
        if not checked or app_settings_module.app_settings is None:
            return
        
        if self._anchor_top_radio.isChecked():
            app_settings_module.app_settings.set_dock_anchor("top")
        elif self._anchor_bottom_radio.isChecked():
            app_settings_module.app_settings.set_dock_anchor("bottom")

