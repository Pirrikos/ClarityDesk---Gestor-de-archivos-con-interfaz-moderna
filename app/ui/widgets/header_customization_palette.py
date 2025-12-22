"""
HeaderCustomizationPalette - Floating palette with draggable header controls.

Shows all available header controls that can be added to the header via drag & drop.
"""

import json
from typing import Dict, Optional

from PySide6.QtCore import Qt, QMimeData, QPoint
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
)

from app.services.header_customization_service import HeaderCustomizationService


class HeaderCustomizationPalette(QWidget):
    """Floating palette with draggable header controls."""
    
    # MIME type único para drag & drop
    MIME_TYPE = "application/x-header-control"
    
    # Información de controles disponibles
    CONTROL_INFO = {
        # Navegación
        "back": ("←", "Atrás"),
        "forward": ("→", "Adelante"),
        # Vista y organización
        "view": ("📊", "Vista (Grid/Lista)"),
        "sort": ("🔀", "Ordenar"),
        "group": ("📁", "Agrupar"),
        # Búsqueda
        "search": ("🔍", "Búsqueda"),
        # Selección / acciones
        "states": ("🏷️", "Estados"),
        "rename": ("✏️", "Renombrar"),
        "duplicate": ("📋", "Duplicar"),
        "delete": ("🗑️", "Eliminar"),
        "info": ("ℹ️", "Obtener información"),
        "share": ("📤", "Compartir"),
        # Creación
        "new_folder": ("📁", "Nueva carpeta"),
        # Paneles
        "breadcrumb": ("📍", "Mostrar ruta"),
        "preview_panel": ("👁️", "Panel de vista previa"),
        # Estructura
        "separator": ("│", "Separador"),
        "flexible_space": ("⤢", "Espacio flexible"),
    }
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize customization palette."""
        super().__init__(parent)
        self._service = HeaderCustomizationService()
        self._setup_ui()
        self._setup_drag()
    
    def _setup_ui(self) -> None:
        """Build palette UI."""
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        self.setFixedWidth(200)
        self.setMinimumHeight(300)
        
        # Estilo Finder (fondo claro, bordes sutiles)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e5e5e7;
                border-radius: 8px;
            }
            QLabel {
                color: #1f1f1f;
                /* font-size: establecido explícitamente */
                font-weight: 600;
                padding: 8px 12px 4px 12px;
            }
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 6px 12px;
                text-align: left;
                color: #1f1f1f;
                /* font-size: establecido explícitamente */
            }
            QPushButton:hover {
                background-color: #f0f0f3;
                border-color: #d0d0d3;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Título
        title = QLabel("Controles disponibles")
        layout.addWidget(title)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e5e5e7; max-height: 1px;")
        layout.addWidget(separator)
        
        # Controles organizados por categorías
        categories = [
            ("Navegación", ["back", "forward"]),
            ("Vista", ["view", "sort", "group"]),
            ("Búsqueda", ["search"]),
            ("Acciones", ["states", "rename", "duplicate", "delete", "info", "share"]),
            ("Creación", ["new_folder"]),
            ("Paneles", ["breadcrumb", "preview_panel"]),
            ("Estructura", ["separator", "flexible_space"]),
        ]
        
        for category_name, control_ids in categories:
            # Etiqueta de categoría
            cat_label = QLabel(category_name)
            cat_label.setStyleSheet("color: #6e7681; /* font-size: establecido explícitamente */ font-weight: normal; padding-top: 8px;")
            layout.addWidget(cat_label)
            
            # Botones de controles
            for control_id in control_ids:
                if control_id in self.CONTROL_INFO:
                    icon, name = self.CONTROL_INFO[control_id]
                    btn = self._create_control_button(control_id, f"{icon} {name}")
                    layout.addWidget(btn)
        
        layout.addStretch()
    
    def _create_control_button(self, control_id: str, label: str) -> QPushButton:
        """
        Create draggable control button.
        
        Args:
            control_id: ID del control.
            label: Etiqueta visual del botón.
        
        Returns:
            QPushButton configurado para drag & drop.
        """
        btn = QPushButton(label, self)
        btn.setProperty("control_id", control_id)
        btn.setCursor(Qt.CursorShape.OpenHandCursor)
        return btn
    
    def _setup_drag(self) -> None:
        """Configure drag & drop for all control buttons."""
        for widget in self.findChildren(QPushButton):
            if widget.property("control_id"):
                widget.mousePressEvent = lambda event, btn=widget: self._on_button_press(event, btn)
    
    def _on_button_press(self, event, button: QPushButton) -> None:
        """
        Handle mouse press on control button to start drag.
        
        Args:
            event: Mouse event.
            button: Button that was pressed.
        """
        if event.button() != Qt.MouseButton.LeftButton:
            return
        
        control_id = button.property("control_id")
        if not control_id:
            return
        
        # Crear datos MIME
        mime_data = QMimeData()
        drag_data = {
            "type": control_id,
            "source": "palette"
        }
        mime_data.setData(self.MIME_TYPE, json.dumps(drag_data).encode('utf-8'))
        
        # Crear drag
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(button.grab())
        drag.setHotSpot(event.pos())
        
        # Ejecutar drag
        drag.exec(Qt.DropAction.MoveAction)

