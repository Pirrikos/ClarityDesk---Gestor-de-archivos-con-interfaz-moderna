"""
BulkRenameDialog - Dialog for bulk file renaming.

Minimal dialog with pattern input and live preview.
"""

import os
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.services.rename_service import RenameService


class BulkRenameDialog(QDialog):
    """Dialog for bulk file renaming with pattern and preview."""
    
    rename_applied = Signal(list, list)  # Emitted with (old_paths, new_paths)
    
    def __init__(self, file_paths: list[str], parent=None):
        """
        Initialize bulk rename dialog.
        
        Args:
            file_paths: List of file paths to rename.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._file_paths = file_paths
        self._rename_service = RenameService()
        self._base_dir = os.path.dirname(file_paths[0]) if file_paths else ""
        self._setup_ui()
        self._load_templates()
        self._update_preview()
    
    def _setup_ui(self) -> None:
        """Build the dialog UI."""
        self.setWindowTitle("Renombrar archivos")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self._setup_templates_bar(layout)
        
        pattern_label = QLabel("Patrón:")
        pattern_label.setStyleSheet("font-weight: 600; /* font-size: establecido explícitamente */")
        layout.addWidget(pattern_label)
        
        self._pattern_input = QLineEdit()
        self._pattern_input.setPlaceholderText("Ejemplo: {name}_{date}_{n}")
        self._pattern_input.textChanged.connect(self._update_preview)
        layout.addWidget(self._pattern_input)
        
        help_label = QLabel("Usa {n} para numeración, {name} para nombre original, {date} para fecha")
        help_label.setStyleSheet("color: #8e8e93; /* font-size: establecido explícitamente */")
        layout.addWidget(help_label)
        
        preview_label = QLabel("Vista previa:")
        preview_label.setStyleSheet("font-weight: 600; /* font-size: establecido explícitamente */ margin-top: 8px;")
        layout.addWidget(preview_label)
        
        self._preview_list = QListWidget()
        self._preview_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e5e7;
                border-radius: 8px;
                padding: 4px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 6px;
                border: none;
            }
        """)
        layout.addWidget(self._preview_list, 1)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_apply)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        layout.addWidget(buttons)
    
    def _update_preview(self) -> None:
        """Update preview list with generated names."""
        pattern = self._pattern_input.text() or "{name}"
        preview_names = self._rename_service.generate_preview(self._file_paths, pattern)
        
        self._preview_list.clear()
        for i, (old_path, new_name) in enumerate(zip(self._file_paths, preview_names)):
            old_name = os.path.basename(old_path)
            item_text = f"{old_name} → {new_name}"
            item = QListWidgetItem(item_text)
            self._preview_list.addItem(item)
    
    def _on_apply(self) -> None:
        """Handle apply button click."""
        pattern = self._pattern_input.text() or "{name}"
        new_names = self._rename_service.generate_preview(self._file_paths, pattern)
        
        is_valid, error_msg = self._rename_service.validate_names(new_names, self._base_dir)
        if not is_valid:
            user_friendly_msg = (
                f"No se pueden renombrar los archivos:\n\n{error_msg}\n\n"
                "Por favor, verifica los nombres e intenta nuevamente."
            )
            QMessageBox.warning(self, "Error al renombrar", user_friendly_msg)
            return
        
        self.rename_applied.emit(self._file_paths, new_names)
        self.accept()
    
    def _setup_templates_bar(self, layout: QVBoxLayout) -> None:
        """Setup templates bar with combo and buttons."""
        templates_layout = QHBoxLayout()
        templates_layout.setSpacing(8)
        
        template_label = QLabel("Plantilla:")
        template_label.setStyleSheet("font-weight: 600; /* font-size: establecido explícitamente */")
        templates_layout.addWidget(template_label)
        
        self._templates_combo = QComboBox()
        self._templates_combo.currentTextChanged.connect(self._on_template_selected)
        templates_layout.addWidget(self._templates_combo, 1)
        
        self._save_button = QPushButton("+ Guardar")
        self._save_button.setFixedHeight(32)
        self._save_button.setStyleSheet("background-color: #0078d4; color: #ffffff; border: none; border-radius: 6px; padding: 6px 12px; /* font-size: establecido explícitamente */")
        self._save_button.clicked.connect(self._on_save_template)
        templates_layout.addWidget(self._save_button)
        
        self._delete_button = QPushButton("🗑 Borrar")
        self._delete_button.setFixedHeight(32)
        self._delete_button.setStyleSheet("background-color: #d13438; color: #ffffff; border: none; border-radius: 6px; padding: 6px 12px; /* font-size: establecido explícitamente */")
        self._delete_button.clicked.connect(self._on_delete_template)
        templates_layout.addWidget(self._delete_button)
        
        layout.addLayout(templates_layout)
    
    def _load_templates(self) -> None:
        """Load templates into combo box."""
        templates = self._rename_service.load_templates()
        self._templates_combo.clear()
        self._templates_combo.addItems(templates)
    
    def _on_template_selected(self, pattern: str) -> None:
        """Handle template selection from combo."""
        if pattern:
            self._pattern_input.setText(pattern)
            self._update_preview()
    
    def _on_save_template(self) -> None:
        """Handle save template button click."""
        pattern = self._pattern_input.text().strip()
        if not pattern:
            return
        
        self._rename_service.save_template(pattern)
        self._load_templates()
        self._templates_combo.setCurrentText(pattern)
    
    def _on_delete_template(self) -> None:
        """Handle delete template button click."""
        pattern = self._templates_combo.currentText()
        if not pattern:
            return
        
        self._rename_service.delete_template(pattern)
        self._load_templates()
        self._templates_combo.setCurrentIndex(-1)

