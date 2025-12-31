"""
SettingsWindow - Settings window for Dock transparency adjustment.

Frameless dialog following official visual contract.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSlider,
    QVBoxLayout,
)

from app.core.constants import (
    CENTRAL_AREA_BG,
    CENTRAL_AREA_BG_LIGHT,
    FILE_BOX_TEXT,
)
from app.managers import app_settings as app_settings_module
from app.ui.windows.base_frameless_dialog import BaseFramelessDialog


# Singleton instance
_settings_window_instance: Optional['SettingsWindow'] = None


def get_settings_window() -> 'SettingsWindow':
    """Get or create SettingsWindow singleton instance."""
    global _settings_window_instance
    
    if _settings_window_instance is None:
        _settings_window_instance = SettingsWindow()
    
    # Mostrar la ventana si no está visible
    if not _settings_window_instance.isVisible():
        _settings_window_instance.show()
    
    # Bring window to front
    _settings_window_instance.raise_()
    _settings_window_instance.activateWindow()
    
    return _settings_window_instance


class SettingsWindow(BaseFramelessDialog):
    """Settings window for adjusting dock background opacity."""
    
    def __init__(self, parent=None):
        """Initialize settings window."""
        super().__init__("Ajustes", parent, modal=False)
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
            
            # Central area color
            initial_color = app_settings_module.app_settings.central_area_color
            if initial_color == "light":
                self._color_light_radio.setChecked(True)
            else:
                self._color_dark_radio.setChecked(True)
        
        # Set window size (aumentado para incluir nueva sección de color)
        self.setFixedSize(360, 360)
    
    def _setup_ui(self) -> None:
        """Build window UI."""
        content_layout = self.get_content_layout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Obtener el panel de contenido y aplicar estilos para eliminar líneas blancas
        content_panel = self._content_panel
        if content_panel:
            # Obtener el estilo base y añadir estilos adicionales
            base_style = content_panel.styleSheet()
            additional_style = f"""
                QWidget {{
                    border: none;
                }}
                QLabel {{
                    background-color: transparent;
                    border: none;
                    padding: 0;
                    margin: 0;
                }}
                QSlider {{
                    background-color: transparent;
                    border: none;
                }}
                QRadioButton {{
                    background-color: transparent;
                    border: none;
                    padding: 0;
                    margin: 0;
                }}
            """
            content_panel.setStyleSheet(base_style + additional_style)
        
        # Title label for opacity section
        opacity_title_label = QLabel("Transparencia del fondo del Dock")
        opacity_title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {FILE_BOX_TEXT};
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
        """)
        content_layout.addWidget(opacity_title_label)
        
        # Slider container with labels
        slider_container_layout = QVBoxLayout()
        slider_container_layout.setContentsMargins(0, 0, 0, 0)
        slider_container_layout.setSpacing(5)
        
        # Slider
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setMinimum(0)
        self._opacity_slider.setMaximum(100)
        self._opacity_slider.setValue(100)
        self._opacity_slider.setStyleSheet(f"""
            QSlider {{
                background-color: transparent;
                border: none;
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 16px;
                height: 16px;
                background: {FILE_BOX_TEXT};
                border: none;
                border-radius: 8px;
                margin: -6px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: #ffffff;
            }}
            QSlider::sub-page:horizontal {{
                background: {FILE_BOX_TEXT};
                border: none;
                border-radius: 2px;
            }}
            QSlider::add-page:horizontal {{
                background: transparent;
                border: none;
            }}
        """)
        self._opacity_slider.valueChanged.connect(self._on_slider_changed)
        slider_container_layout.addWidget(self._opacity_slider)
        
        # Labels for min/max
        labels_row = QHBoxLayout()
        labels_row.setContentsMargins(0, 0, 0, 0)
        labels_row.setSpacing(0)
        
        min_label = QLabel("0%")
        min_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: #9AA0A6;
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
        """)
        
        max_label = QLabel("100%")
        max_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: #9AA0A6;
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
        """)
        max_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        labels_row.addWidget(min_label)
        labels_row.addStretch()
        labels_row.addWidget(max_label)
        slider_container_layout.addLayout(labels_row)
        
        content_layout.addLayout(slider_container_layout)
        
        # Anchor position section
        anchor_title_label = QLabel("Posición del Dock")
        anchor_title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {FILE_BOX_TEXT};
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
        """)
        content_layout.addWidget(anchor_title_label)
        
        # Checkboxes for anchor (mutually exclusive) - en dos columnas
        anchor_container_layout = QHBoxLayout()
        anchor_container_layout.setContentsMargins(0, 4, 0, 0)
        anchor_container_layout.setSpacing(16)
        
        self._anchor_top_radio = QCheckBox("Dock arriba")
        self._anchor_bottom_radio = QCheckBox("Dock abajo")
        
        checkbox_style = f"""
            QCheckBox {{
                font-size: 13px;
                color: {FILE_BOX_TEXT};
                background-color: transparent;
                border: none;
                padding: 6px 0px;
                margin: 0;
                spacing: 10px;
                min-width: 140px;
                min-height: 24px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1.5px solid rgba(255, 255, 255, 0.5);
                border-radius: 3px;
                background-color: #808080;
            }}
            QCheckBox::indicator:hover {{
                border-color: rgba(255, 255, 255, 0.7);
                background-color: #909090;
            }}
            QCheckBox::indicator:checked {{
                border-color: rgba(255, 255, 255, 0.5);
                background-color: #D0D0D0;
            }}
            QCheckBox::indicator:checked:hover {{
                border-color: rgba(255, 255, 255, 0.7);
                background-color: #E0E0E0;
            }}
        """
        self._anchor_top_radio.setStyleSheet(checkbox_style)
        self._anchor_bottom_radio.setStyleSheet(checkbox_style)
        
        # Hacer que sean mutuamente exclusivos
        self._anchor_top_radio.toggled.connect(lambda checked: self._on_anchor_toggled("top", checked))
        self._anchor_bottom_radio.toggled.connect(lambda checked: self._on_anchor_toggled("bottom", checked))
        
        anchor_container_layout.addWidget(self._anchor_top_radio)
        anchor_container_layout.addWidget(self._anchor_bottom_radio)
        content_layout.addLayout(anchor_container_layout)
        
        # Central area color section
        color_title_label = QLabel("Tema")
        color_title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {FILE_BOX_TEXT};
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
        """)
        content_layout.addWidget(color_title_label)
        
        # Radio buttons for color (mutually exclusive) - en dos columnas
        color_container_layout = QHBoxLayout()
        color_container_layout.setContentsMargins(0, 4, 0, 0)
        color_container_layout.setSpacing(16)
        
        self._color_dark_radio = QCheckBox("Oscuro")
        self._color_light_radio = QCheckBox("Claro")
        
        self._color_dark_radio.setStyleSheet(checkbox_style)
        self._color_light_radio.setStyleSheet(checkbox_style)
        
        # Hacer que sean mutuamente exclusivos
        self._color_dark_radio.toggled.connect(lambda checked: self._on_color_toggled("dark", checked))
        self._color_light_radio.toggled.connect(lambda checked: self._on_color_toggled("light", checked))
        
        color_container_layout.addWidget(self._color_dark_radio)
        color_container_layout.addWidget(self._color_light_radio)
        content_layout.addLayout(color_container_layout)

        # Ocultar temporalmente la opción de tema en Ajustes (sin eliminar lógica)
        # Deja conectadas las señales pero oculta los controles para evitar interacción.
        color_title_label.setVisible(False)
        self._color_dark_radio.setVisible(False)
        self._color_light_radio.setVisible(False)
        
        content_layout.addStretch()
    
    def _on_slider_changed(self, value: int) -> None:
        """Handle slider value change."""
        if app_settings_module.app_settings is not None:
            # Convert 0-100 to 0.0-1.0
            opacity = value / 100.0
            app_settings_module.app_settings.set_dock_background_opacity(opacity)
    
    def _on_anchor_toggled(self, anchor: str, checked: bool) -> None:
        """Handle anchor checkbox toggle (mutually exclusive)."""
        if not checked or app_settings_module.app_settings is None:
            return
        
        # Desmarcar el otro checkbox
        if anchor == "top":
            self._anchor_bottom_radio.setChecked(False)
            app_settings_module.app_settings.set_dock_anchor("top")
        elif anchor == "bottom":
            self._anchor_top_radio.setChecked(False)
            app_settings_module.app_settings.set_dock_anchor("bottom")
    
    def _on_color_toggled(self, color: str, checked: bool) -> None:
        """Handle color checkbox toggle (mutually exclusive)."""
        if not checked or app_settings_module.app_settings is None:
            return
        
        # Desmarcar el otro checkbox
        if color == "dark":
            self._color_light_radio.setChecked(False)
            app_settings_module.app_settings.set_central_area_color("dark")
        elif color == "light":
            self._color_dark_radio.setChecked(False)
            app_settings_module.app_settings.set_central_area_color("light")
