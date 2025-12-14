"""AppHeader - Minimal header widget showing active workspace name."""

from typing import Optional
import os

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class AppHeader(QWidget):
    """Minimal header showing active workspace name (placeholder for future Finder-style header)."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build minimal header with workspace name."""
        self.setFixedHeight(32)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.02);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 12px;
                padding: 0px 12px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._workspace_label = QLabel("", self)
        layout.addWidget(self._workspace_label, 0)

    def update_workspace(self, workspace_name_or_path: Optional[str]) -> None:
        """
        Update displayed workspace name.
        
        Accepts either a workspace name (string) or a folder path.
        If it's a path, extracts the folder name.
        """
        if not workspace_name_or_path:
            self._workspace_label.setText("")
            return

        # Si parece un path (contiene separadores de directorio), extraer nombre
        if os.sep in workspace_name_or_path or (os.altsep and os.altsep in workspace_name_or_path):
            workspace_name = os.path.basename(workspace_name_or_path)
            if not workspace_name:
                # Si es raíz de unidad (ej: C:\), usar el path completo
                workspace_name = workspace_name_or_path.rstrip(os.sep)
        else:
            # Es un nombre de workspace directamente
            workspace_name = workspace_name_or_path
        
        self._workspace_label.setText(workspace_name)

