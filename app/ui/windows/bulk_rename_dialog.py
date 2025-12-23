"""
BulkRenameDialog - Dialog for bulk file renaming.

Minimal dialog with pattern input and live preview.
"""

import os
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
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
        self._is_single_file = len(file_paths) == 1
        self._setup_ui()
        self._load_templates()
        self._update_preview()
    
    def _setup_ui(self) -> None:
        """Build the dialog UI."""
        file_count = len(self._file_paths)
        title = f"Renombrar archivo" if file_count == 1 else f"Renombrar {file_count} archivos"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self._setup_templates_bar(layout)
        
        pattern_label = QLabel("Patrón:")
        pattern_label.setStyleSheet("font-weight: 600; /* font-size: establecido explícitamente */")
        layout.addWidget(pattern_label)
        
        self._pattern_input = QLineEdit()
        if self._is_single_file:
            self._pattern_input.setPlaceholderText("Ejemplo: {name}_{date}")
            help_text = "Usa {name} para nombre original, {date} para fecha. {n} se ignora automáticamente."
        else:
            self._pattern_input.setPlaceholderText("Ejemplo: {name}_{date}_{n}")
            help_text = "Usa {n} para numeración, {name} para nombre original, {date} para fecha"
        
        self._pattern_input.textChanged.connect(self._update_preview)
        # Enter en "Patrón" → aplicar cambios
        self._pattern_input.returnPressed.connect(self._on_apply)
        layout.addWidget(self._pattern_input)
        
        help_label = QLabel(help_text)
        help_label.setStyleSheet("color: #8e8e93; /* font-size: establecido explícitamente */")
        layout.addWidget(help_label)
        
        # Búsqueda y reemplazo
        self._setup_search_replace(layout)
        
        # Opciones de formato
        self._setup_format_options(layout)
        
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
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Aplicar")
        ok_button.setDefault(False)  # Desactivar comportamiento por defecto
        ok_button.setAutoDefault(False)  # Desactivar auto-default
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        layout.addWidget(buttons)
    
    def _setup_search_replace(self, layout: QVBoxLayout) -> None:
        """Setup search and replace section."""
        search_replace_label = QLabel("Buscar y reemplazar:")
        search_replace_label.setStyleSheet("font-weight: 600; /* font-size: establecido explícitamente */ margin-top: 8px;")
        layout.addWidget(search_replace_label)
        
        search_replace_layout = QHBoxLayout()
        search_replace_layout.setSpacing(8)
        
        # Crear ambos campos primero
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Texto a buscar")
        self._search_input.textChanged.connect(self._update_preview)
        
        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText("Texto de reemplazo")
        self._replace_input.textChanged.connect(self._update_preview)
        
        # Conectar señales con funciones intermedias para evitar conflictos
        # Enter en "Buscar" → mover foco a "Reemplazar"
        def _on_search_enter():
            self._replace_input.setFocus()
        self._search_input.returnPressed.connect(_on_search_enter)
        
        # Enter en "Reemplazar" → mover foco a "Patrón"
        def _on_replace_enter():
            self._pattern_input.setFocus()
        self._replace_input.returnPressed.connect(_on_replace_enter)
        
        search_replace_layout.addWidget(QLabel("Buscar:"))
        search_replace_layout.addWidget(self._search_input, 1)
        search_replace_layout.addWidget(QLabel("Reemplazar:"))
        search_replace_layout.addWidget(self._replace_input, 1)
        
        layout.addLayout(search_replace_layout)
    
    def _setup_format_options(self, layout: QVBoxLayout) -> None:
        """Setup format options checkboxes."""
        format_label = QLabel("Formato:")
        format_label.setStyleSheet("font-weight: 600; /* font-size: establecido explícitamente */ margin-top: 8px;")
        layout.addWidget(format_label)
        
        format_layout = QHBoxLayout()
        format_layout.setSpacing(16)
        
        self._uppercase_check = QCheckBox("Mayúsculas")
        self._uppercase_check.stateChanged.connect(self._on_format_changed)
        format_layout.addWidget(self._uppercase_check)
        
        self._lowercase_check = QCheckBox("Minúsculas")
        self._lowercase_check.stateChanged.connect(self._on_format_changed)
        format_layout.addWidget(self._lowercase_check)
        
        self._title_case_check = QCheckBox("Capitalizar palabras")
        self._title_case_check.stateChanged.connect(self._on_format_changed)
        format_layout.addWidget(self._title_case_check)
        
        format_layout.addStretch()
        layout.addLayout(format_layout)
    
    def _on_format_changed(self) -> None:
        """Handle format checkbox changes - ensure only one is selected."""
        sender = self.sender()
        
        if sender == self._uppercase_check and self._uppercase_check.isChecked():
            self._lowercase_check.setChecked(False)
            self._title_case_check.setChecked(False)
        elif sender == self._lowercase_check and self._lowercase_check.isChecked():
            self._uppercase_check.setChecked(False)
            self._title_case_check.setChecked(False)
        elif sender == self._title_case_check and self._title_case_check.isChecked():
            self._uppercase_check.setChecked(False)
            self._lowercase_check.setChecked(False)
        
        self._update_preview()
    
    def _update_preview(self) -> None:
        """Update preview list with generated names."""
        pattern = self._pattern_input.text() or "{name}"
        search_text = self._search_input.text() if hasattr(self, '_search_input') else ""
        replace_text = self._replace_input.text() if hasattr(self, '_replace_input') else ""
        use_uppercase = self._uppercase_check.isChecked() if hasattr(self, '_uppercase_check') else False
        use_lowercase = self._lowercase_check.isChecked() if hasattr(self, '_lowercase_check') else False
        use_title_case = self._title_case_check.isChecked() if hasattr(self, '_title_case_check') else False
        
        preview_names = self._rename_service.generate_preview(
            self._file_paths,
            pattern,
            search_text=search_text,
            replace_text=replace_text,
            use_uppercase=use_uppercase,
            use_lowercase=use_lowercase,
            use_title_case=use_title_case
        )
        
        self._preview_list.clear()
        for i, (old_path, new_name) in enumerate(zip(self._file_paths, preview_names)):
            old_name = os.path.basename(old_path)
            item_text = f"{old_name} → {new_name}"
            item = QListWidgetItem(item_text)
            self._preview_list.addItem(item)
    
    def _on_apply(self) -> None:
        """Handle apply button click."""
        pattern = self._pattern_input.text() or "{name}"
        search_text = self._search_input.text() if hasattr(self, '_search_input') else ""
        replace_text = self._replace_input.text() if hasattr(self, '_replace_input') else ""
        use_uppercase = self._uppercase_check.isChecked() if hasattr(self, '_uppercase_check') else False
        use_lowercase = self._lowercase_check.isChecked() if hasattr(self, '_lowercase_check') else False
        use_title_case = self._title_case_check.isChecked() if hasattr(self, '_title_case_check') else False
        
        new_names = self._rename_service.generate_preview(
            self._file_paths,
            pattern,
            search_text=search_text,
            replace_text=replace_text,
            use_uppercase=use_uppercase,
            use_lowercase=use_lowercase,
            use_title_case=use_title_case
        )
        
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

