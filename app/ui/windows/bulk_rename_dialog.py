"""
BulkRenameDialog - Dialog for bulk file renaming.

Minimal dialog with pattern input and live preview.
Visual style: File Box elevated panel.
"""

import os
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal, QPoint, QEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import (
    APP_HEADER_BG,
    APP_HEADER_BORDER,
    BUTTON_BG_DARK,
    BUTTON_BORDER_DARK,
    BUTTON_BG_DARK_HOVER,
    BUTTON_BORDER_DARK_HOVER,
    CENTRAL_AREA_BG,
    CHECKBOX_BORDER,
    CHECKBOX_BORDER_HOVER,
    CHECKBOX_BG_CHECKED,
    CHECKBOX_BG_CHECKED_HOVER,
    FILE_BOX_BORDER,
    FILE_BOX_BUTTON_PRIMARY,
    FILE_BOX_BUTTON_PRIMARY_HOVER,
    FILE_BOX_BUTTON_PRIMARY_PRESSED,
    FILE_BOX_HEADER_BG,
    FILE_BOX_HOVER_BG,
    FILE_BOX_LIST_BG,
    FILE_BOX_TEXT,
)
from app.services.file_box_utils import FILE_BOX_SCROLLBAR_STYLES
from app.services.rename_service import RenameService
from app.ui.windows.error_dialog import ErrorDialog


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
        
        # Configurar ventana frameless con bordes redondeados
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        self._file_paths = list(file_paths)
        self._rename_service = RenameService()
        self._base_dir = os.path.dirname(self._file_paths[0]) if self._file_paths else ""
        self._is_single_file = len(self._file_paths) == 1
        self._drag_start: Optional[QPoint] = None
        self._header_widget: Optional[QWidget] = None
        self._modify_existing_mode = True  # Predeterminada: Modificar existente
        self._current_name_label: Optional[QLabel] = None
        self._number_at_end = True  # Predeterminada: número al final
        
        self._setup_ui()
        self._load_templates()
        self._update_preview()
    
    def _setup_ui(self) -> None:
        """Build the dialog UI with File Box elevated panel style."""
        file_count = len(self._file_paths)
        title_text = f"Renombrar archivo" if file_count == 1 else f"Renombrar {file_count} archivos"
        self.setWindowTitle(title_text)
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        
        # 1. Estilo del QDialog (contenedor externo) - transparente
        self.setStyleSheet(f"""
            QDialog {{
                background-color: transparent;
                border: none;
            }}
        """)
        
        # Layout principal sin márgenes (todo va dentro del panel)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 2. Header del diálogo con botón cerrar y arrastre
        self._header_widget = QWidget()
        self._header_widget.setFixedHeight(48)
        self._header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {APP_HEADER_BG};
                border-bottom: 1px solid {APP_HEADER_BORDER};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)
        header_layout = QHBoxLayout(self._header_widget)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(0)
        
        title_label = QLabel(title_text)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {FILE_BOX_TEXT};
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Botón cerrar
        close_button = QPushButton("✕")
        close_button.setFixedSize(32, 28)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: {FILE_BOX_TEXT};
                font-size: 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
        """)
        close_button.clicked.connect(self.reject)
        header_layout.addWidget(close_button)
        
        main_layout.addWidget(self._header_widget)
        
        # 3. Panel interno elevado (encapsula TODO el contenido)
        content_panel = QWidget()
        content_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {CENTRAL_AREA_BG};
                border-radius: 10px;
            }}
        """)
        
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)
        
        # Margen interno del panel respecto al contenedor externo
        main_layout.addWidget(content_panel)
        main_layout.setContentsMargins(4, 0, 4, 4)  # Pequeño margen para efecto elevado
        
        # Layout horizontal para opciones en dos columnas
        options_layout = QHBoxLayout()
        options_layout.setSpacing(20)
        
        # Columna izquierda de opciones
        left_column = QVBoxLayout()
        left_column.setSpacing(16)
        
        # Columna derecha de opciones
        right_column = QVBoxLayout()
        right_column.setSpacing(16)
        
        # Templates bar (ocupa todo el ancho)
        self._setup_templates_bar(content_layout)
        
        # Selector de modo: Nuevo o Modificar existente
        self._setup_mode_selector(left_column)
        
        pattern_label = QLabel("Patrón:")
        pattern_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                color: {FILE_BOX_TEXT};
            }}
        """)
        left_column.addWidget(pattern_label)
        
        # Label para mostrar nombre actual cuando se modifica existente
        self._current_name_label = QLabel()
        self._current_name_label.setStyleSheet(f"""
            QLabel {{
                color: #9AA0A6;
                font-size: 13px;
                padding: 4px 8px;
                background-color: {FILE_BOX_LIST_BG};
                border: 1px solid {FILE_BOX_BORDER};
                border-radius: 6px;
            }}
        """)
        self._current_name_label.setWordWrap(True)
        self._current_name_label.hide()  # Oculto por defecto
        left_column.addWidget(self._current_name_label)
        
        self._pattern_input = QLineEdit()
        if self._is_single_file:
            self._pattern_input.setPlaceholderText("Ejemplo: {name}_{date}")
            help_text = "Usa {name} para nombre original, {date} para fecha. {n} se ignora automáticamente."
        else:
            self._pattern_input.setPlaceholderText("Ejemplo: {name}_{date}")
            help_text = "Usa {name} para nombre original, {date} para fecha. El número {n} se añade automáticamente al final (01, 02, 03...)"
        
        self._pattern_input.setStyleSheet(self._get_input_stylesheet())
        self._pattern_input.textChanged.connect(self._update_preview)
        self._pattern_input.returnPressed.connect(self._on_apply)
        
        # Pre-llenar con nombre actual si es modo modificar existente (solo para un archivo)
        if self._modify_existing_mode and self._is_single_file:
            current_name = os.path.basename(self._file_paths[0])
            self._current_name_label.setText(f"Archivo actual: {current_name}")
            self._current_name_label.show()
            name_without_ext = os.path.splitext(current_name)[0]
            self._pattern_input.setText(name_without_ext)
        
        left_column.addWidget(self._pattern_input)
        
        help_label = QLabel(help_text)
        help_label.setStyleSheet(f"""
            QLabel {{
                color: #9AA0A6;
            }}
        """)
        left_column.addWidget(help_label)
        
        # Opción de posición del número (solo para múltiples archivos) - va a la columna derecha
        if not self._is_single_file:
            self._setup_number_position_option(right_column)
        
        # Búsqueda y reemplazo - va a la columna derecha
        self._setup_search_replace(right_column)
        
        # Opciones de formato - va a la columna derecha
        self._setup_format_options(right_column)
        
        # Separador vertical entre las dos columnas
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"""
            QFrame {{
                border-left: 1px solid {FILE_BOX_BORDER};
                max-width: 1px;
            }}
        """)
        
        # Añadir las dos columnas y el separador al layout horizontal
        options_layout.addLayout(left_column, 1)
        options_layout.addWidget(separator)
        options_layout.addLayout(right_column, 1)
        
        # Añadir el layout de opciones al layout principal
        content_layout.addLayout(options_layout)
        
        # Preview abajo ocupando todo el ancho
        preview_label = QLabel("Vista previa:")
        preview_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                color: {FILE_BOX_TEXT};
                margin-top: 8px;
            }}
        """)
        content_layout.addWidget(preview_label)
        
        self._preview_table = QTableWidget()
        self._preview_table.setColumnCount(2)
        self._preview_table.setHorizontalHeaderLabels(["antes", "después"])
        self._preview_table.horizontalHeader().setFixedHeight(28)
        self._preview_table.horizontalHeader().setStretchLastSection(True)
        self._preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._preview_table.verticalHeader().setVisible(False)  # Ocultar columna de números de fila
        self._preview_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._preview_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._preview_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._preview_table.setStyleSheet(self._get_preview_table_stylesheet())
        content_layout.addWidget(self._preview_table, 2)  # Mayor stretch para ocupar más espacio
        
        # Footer con botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.setSpacing(8)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.setStyleSheet(self._get_cancel_button_stylesheet())
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Aplicar")
        apply_button.setStyleSheet(self._get_apply_button_stylesheet())
        apply_button.clicked.connect(self._on_apply)
        apply_button.setDefault(False)
        apply_button.setAutoDefault(False)
        buttons_layout.addWidget(apply_button)
        
        content_layout.addLayout(buttons_layout)
    
    def _get_input_stylesheet(self) -> str:
        """Get stylesheet for QLineEdit inputs."""
        return f"""
            QLineEdit {{
                background-color: {FILE_BOX_LIST_BG};
                color: {FILE_BOX_TEXT};
                border: 1px solid {FILE_BOX_BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border-color: {FILE_BOX_BUTTON_PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: #9AA0A6;
            }}
        """
    
    def _get_combo_stylesheet(self) -> str:
        """Get stylesheet for QComboBox."""
        return f"""
            QComboBox {{
                background-color: {FILE_BOX_LIST_BG};
                color: {FILE_BOX_TEXT};
                border: 1px solid {FILE_BOX_BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            QComboBox:hover {{
                border-color: {FILE_BOX_BUTTON_PRIMARY};
            }}
            QComboBox:focus {{
                border-color: {FILE_BOX_BUTTON_PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {FILE_BOX_LIST_BG};
                border: 1px solid {FILE_BOX_BORDER};
                border-radius: 6px;
                selection-background-color: {FILE_BOX_HOVER_BG};
                color: {FILE_BOX_TEXT};
                padding: 4px;
            }}
        """
    
    def _get_preview_table_stylesheet(self) -> str:
        """Get stylesheet for preview QTableWidget."""
        return f"""
            QTableWidget {{
                border: 1px solid {FILE_BOX_BORDER};
                border-radius: 8px;
                background-color: {FILE_BOX_LIST_BG};
                color: {FILE_BOX_TEXT};
                outline: none;
                gridline-color: {FILE_BOX_BORDER};
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                border: none;
                color: {FILE_BOX_TEXT};
                background-color: transparent;
            }}
            QTableWidget::item:hover {{
                background-color: {FILE_BOX_HOVER_BG};
            }}
            QHeaderView::section {{
                background-color: {FILE_BOX_HEADER_BG};
                color: {FILE_BOX_TEXT};
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid {FILE_BOX_BORDER};
                font-weight: 500;
                font-size: 11px;
            }}
            QHeaderView::section:first {{
                background-color: {FILE_BOX_HEADER_BG};
                border-top-left-radius: 8px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: 8px;
            }}
            {FILE_BOX_SCROLLBAR_STYLES}
        """
    
    def _get_cancel_button_stylesheet(self) -> str:
        """Get stylesheet for cancel button (dark button style)."""
        return f"""
            QPushButton {{
                background-color: {BUTTON_BG_DARK};
                border: 1px solid {BUTTON_BORDER_DARK};
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.88);
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_BG_DARK_HOVER};
                border-color: {BUTTON_BORDER_DARK_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {BUTTON_BG_DARK_HOVER};
                border-color: {BUTTON_BORDER_DARK_HOVER};
            }}
        """
    
    def _get_apply_button_stylesheet(self) -> str:
        """Get stylesheet for apply button (primary button style)."""
        return f"""
            QPushButton {{
                background-color: {FILE_BOX_BUTTON_PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {FILE_BOX_BUTTON_PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {FILE_BOX_BUTTON_PRIMARY_PRESSED};
            }}
        """
    
    def _setup_search_replace(self, layout: QVBoxLayout) -> None:
        """Setup search and replace section."""
        search_replace_label = QLabel("Buscar y reemplazar:")
        search_replace_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                color: {FILE_BOX_TEXT};
                margin-top: 8px;
            }}
        """)
        layout.addWidget(search_replace_label)
        
        search_replace_layout = QHBoxLayout()
        search_replace_layout.setSpacing(8)
        
        # Crear ambos campos primero
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Texto a buscar")
        self._search_input.setStyleSheet(self._get_input_stylesheet())
        self._search_input.textChanged.connect(self._update_preview)
        
        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText("Texto de reemplazo")
        self._replace_input.setStyleSheet(self._get_input_stylesheet())
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
        
        search_label = QLabel("Buscar:")
        search_label.setStyleSheet(f"color: {FILE_BOX_TEXT};")
        search_replace_layout.addWidget(search_label)
        search_replace_layout.addWidget(self._search_input, 1)
        
        replace_label = QLabel("Reemplazar:")
        replace_label.setStyleSheet(f"color: {FILE_BOX_TEXT};")
        search_replace_layout.addWidget(replace_label)
        search_replace_layout.addWidget(self._replace_input, 1)
        
        layout.addLayout(search_replace_layout)
    
    def _setup_number_position_option(self, layout: QVBoxLayout) -> None:
        """Setup number position option: al principio or al final."""
        position_label = QLabel("Posición del número:")
        position_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                color: {FILE_BOX_TEXT};
                margin-top: 8px;
            }}
        """)
        layout.addWidget(position_label)
        
        position_layout = QHBoxLayout()
        position_layout.setSpacing(16)
        
        radio_stylesheet = self._get_radio_stylesheet()
        
        self._number_at_start_radio = QRadioButton("Al principio")
        self._number_at_start_radio.setStyleSheet(radio_stylesheet)
        self._number_at_start_radio.toggled.connect(self._on_number_position_changed)
        position_layout.addWidget(self._number_at_start_radio)
        
        self._number_at_end_radio = QRadioButton("Al final")
        self._number_at_end_radio.setStyleSheet(radio_stylesheet)
        self._number_at_end_radio.setChecked(True)  # Predeterminada: al final
        self._number_at_end_radio.toggled.connect(self._on_number_position_changed)
        position_layout.addWidget(self._number_at_end_radio)
        
        position_layout.addStretch()
        layout.addLayout(position_layout)
    
    def _on_number_position_changed(self) -> None:
        """Handle number position change."""
        self._number_at_end = self._number_at_end_radio.isChecked()
        self._update_preview()
    
    def _setup_format_options(self, layout: QVBoxLayout) -> None:
        """Setup format options checkboxes."""
        format_label = QLabel("Formato:")
        format_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                color: {FILE_BOX_TEXT};
                margin-top: 8px;
            }}
        """)
        layout.addWidget(format_label)
        
        format_layout = QHBoxLayout()
        format_layout.setSpacing(16)
        
        checkbox_stylesheet = self._get_checkbox_stylesheet()
        
        self._uppercase_check = QCheckBox("Mayúsculas")
        self._uppercase_check.setStyleSheet(checkbox_stylesheet)
        self._uppercase_check.stateChanged.connect(self._on_format_changed)
        format_layout.addWidget(self._uppercase_check)
        
        self._lowercase_check = QCheckBox("Minúsculas")
        self._lowercase_check.setStyleSheet(checkbox_stylesheet)
        self._lowercase_check.stateChanged.connect(self._on_format_changed)
        format_layout.addWidget(self._lowercase_check)
        
        self._title_case_check = QCheckBox("Capitalizar palabras")
        self._title_case_check.setStyleSheet(checkbox_stylesheet)
        self._title_case_check.stateChanged.connect(self._on_format_changed)
        format_layout.addWidget(self._title_case_check)
        
        format_layout.addStretch()
        layout.addLayout(format_layout)
    
    def _setup_mode_selector(self, layout: QVBoxLayout) -> None:
        """Setup mode selector: Nuevo or Modificar existente."""
        mode_label = QLabel("Modo:")
        mode_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                color: {FILE_BOX_TEXT};
            }}
        """)
        layout.addWidget(mode_label)
        
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(16)
        
        radio_stylesheet = self._get_radio_stylesheet()
        
        self._new_mode_radio = QRadioButton("Nuevo")
        self._new_mode_radio.setStyleSheet(radio_stylesheet)
        self._new_mode_radio.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self._new_mode_radio)
        
        self._modify_mode_radio = QRadioButton("Modificar existente")
        self._modify_mode_radio.setStyleSheet(radio_stylesheet)
        
        # Si hay múltiples archivos, deshabilitar "Modificar existente" y forzar "Nuevo"
        if self._is_single_file:
            self._modify_mode_radio.setChecked(True)  # Predeterminada solo para un archivo
            self._modify_existing_mode = True
        else:
            # Múltiples archivos: deshabilitar "Modificar existente" y forzar "Nuevo"
            self._modify_mode_radio.setEnabled(False)
            self._modify_mode_radio.setToolTip("No disponible para múltiples archivos")
            self._new_mode_radio.setChecked(True)  # Forzar "Nuevo"
            self._modify_existing_mode = False
        
        self._modify_mode_radio.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self._modify_mode_radio)
        
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
    
    def _get_radio_stylesheet(self) -> str:
        """Get stylesheet for radio buttons."""
        return f"""
            QRadioButton {{
                color: {FILE_BOX_TEXT};
                spacing: 6px;
            }}
            QRadioButton::indicator {{
                width: 11px;
                height: 11px;
                border: 1px solid {CHECKBOX_BORDER};
                border-radius: 6px;
                background-color: transparent;
            }}
            QRadioButton::indicator:hover {{
                border-color: {CHECKBOX_BORDER_HOVER};
            }}
            QRadioButton::indicator:checked {{
                background-color: {CHECKBOX_BG_CHECKED};
                border-color: {CHECKBOX_BG_CHECKED};
            }}
            QRadioButton::indicator:checked:hover {{
                background-color: {CHECKBOX_BG_CHECKED_HOVER};
                border-color: {CHECKBOX_BG_CHECKED_HOVER};
            }}
        """
    
    def _on_mode_changed(self) -> None:
        """Handle mode change between Nuevo and Modificar existente."""
        # Solo permitir cambiar modo si es un solo archivo
        if not self._is_single_file:
            return
        
        self._modify_existing_mode = self._modify_mode_radio.isChecked()
        
        if self._modify_existing_mode:
            # Modo: Modificar existente (solo disponible para un archivo)
            current_name = os.path.basename(self._file_paths[0])
            self._current_name_label.setText(f"Archivo actual: {current_name}")
            self._current_name_label.show()
            
            # Pre-llenar con nombre sin extensión
            name_without_ext = os.path.splitext(current_name)[0]
            self._pattern_input.setText(name_without_ext)
        else:
            # Modo: Nuevo
            self._current_name_label.hide()
            self._pattern_input.clear()
        
        self._update_preview()
    
    def _get_checkbox_stylesheet(self) -> str:
        """Get stylesheet for checkboxes."""
        return f"""
            QCheckBox {{
                color: {FILE_BOX_TEXT};
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 11px;
                height: 11px;
                border: 1px solid {CHECKBOX_BORDER};
                border-radius: 2px;
                background-color: transparent;
            }}
            QCheckBox::indicator:hover {{
                border-color: {CHECKBOX_BORDER_HOVER};
            }}
            QCheckBox::indicator:checked {{
                background-color: {CHECKBOX_BG_CHECKED};
                border-color: {CHECKBOX_BG_CHECKED};
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: {CHECKBOX_BG_CHECKED_HOVER};
                border-color: {CHECKBOX_BG_CHECKED_HOVER};
            }}
        """
    
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
        """Update preview table with generated names."""
        if not hasattr(self, '_preview_table'):
            return  # Aún no está inicializado
        
        pattern = self._pattern_input.text() or "{name}"
        
        # Ajustar patrón según posición del número (solo para múltiples archivos)
        if not self._is_single_file:
            # Si el patrón no tiene {n}, añadirlo según la posición elegida
            if "{n}" not in pattern:
                if self._number_at_end:
                    pattern = pattern + " {n}"  # Al final
                else:
                    pattern = "{n} " + pattern  # Al principio
            else:
                # Si ya tiene {n}, moverlo según la posición elegida
                # Remover {n} y espacios circundantes
                pattern_parts = pattern.split("{n}")
                pattern_without_n = " ".join(part.strip() for part in pattern_parts if part.strip())
                # Limpiar espacios dobles
                pattern_without_n = " ".join(pattern_without_n.split())
                if self._number_at_end:
                    pattern = pattern_without_n + " {n}" if pattern_without_n else "{n}"
                else:
                    pattern = "{n} " + pattern_without_n if pattern_without_n else "{n}"
        
        search_text = self._search_input.text() if hasattr(self, '_search_input') else ""
        replace_text = self._replace_input.text() if hasattr(self, '_replace_input') else ""
        use_uppercase = self._uppercase_check.isChecked() if hasattr(self, '_uppercase_check') else False
        use_lowercase = self._lowercase_check.isChecked() if hasattr(self, '_lowercase_check') else False
        use_title_case = self._title_case_check.isChecked() if hasattr(self, '_title_case_check') else False
        
        # Determinar posición del número para el servicio
        number_position = "suffix" if self._number_at_end else "prefix"
        
        preview_names = self._rename_service.generate_preview(
            self._file_paths,
            pattern,
            search_text=search_text,
            replace_text=replace_text,
            use_uppercase=use_uppercase,
            use_lowercase=use_lowercase,
            use_title_case=use_title_case,
            number_position=number_position
        )
        
        self._preview_table.setRowCount(len(self._file_paths))
        for i, (old_path, new_name) in enumerate(zip(self._file_paths, preview_names)):
            old_name = os.path.basename(old_path)
            
            # Columna ANTES
            before_item = QTableWidgetItem(old_name)
            before_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._preview_table.setItem(i, 0, before_item)
            
            # Columna DESPUÉS
            after_item = QTableWidgetItem(new_name)
            after_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._preview_table.setItem(i, 1, after_item)
    
    def _on_apply(self) -> None:
        """Handle apply button click."""
        pattern = self._pattern_input.text() or "{name}"
        
        # Ajustar patrón según posición del número (solo para múltiples archivos)
        if not self._is_single_file:
            # Si el patrón no tiene {n}, añadirlo según la posición elegida
            if "{n}" not in pattern:
                if self._number_at_end:
                    pattern = pattern + " {n}"  # Al final
                else:
                    pattern = "{n} " + pattern  # Al principio
            else:
                # Si ya tiene {n}, moverlo según la posición elegida
                # Remover {n} y espacios circundantes
                pattern_parts = pattern.split("{n}")
                pattern_without_n = " ".join(part.strip() for part in pattern_parts if part.strip())
                # Limpiar espacios dobles
                pattern_without_n = " ".join(pattern_without_n.split())
                if self._number_at_end:
                    pattern = pattern_without_n + " {n}" if pattern_without_n else "{n}"
                else:
                    pattern = "{n} " + pattern_without_n if pattern_without_n else "{n}"
        
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
        
        is_valid, error_msg = self._rename_service.validate_names(
            new_names, 
            self._base_dir, 
            original_paths=self._file_paths
        )
        if not is_valid:
            user_friendly_msg = (
                f"No se pueden renombrar los archivos:\n\n{error_msg}\n\n"
                "Por favor, verifica los nombres e intenta nuevamente."
            )
            error_dialog = ErrorDialog(
                parent=self,
                title="Error al renombrar",
                message=user_friendly_msg,
                is_warning=True
            )
            error_dialog.exec()
            return
        
        self.rename_applied.emit(self._file_paths, new_names)
        self.accept()
    
    def _setup_templates_bar(self, layout: QVBoxLayout) -> None:
        """Setup templates bar with combo and buttons."""
        templates_layout = QHBoxLayout()
        templates_layout.setSpacing(8)
        
        template_label = QLabel("Plantilla:")
        template_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                color: {FILE_BOX_TEXT};
            }}
        """)
        templates_layout.addWidget(template_label)
        
        self._templates_combo = QComboBox()
        self._templates_combo.setStyleSheet(self._get_combo_stylesheet())
        self._templates_combo.currentTextChanged.connect(self._on_template_selected)
        templates_layout.addWidget(self._templates_combo, 1)
        
        self._save_button = QPushButton("+ Guardar")
        self._save_button.setFixedHeight(32)
        self._save_button.setStyleSheet(self._get_apply_button_stylesheet())
        self._save_button.clicked.connect(self._on_save_template)
        templates_layout.addWidget(self._save_button)
        
        self._delete_button = QPushButton("🗑 Borrar")
        self._delete_button.setFixedHeight(32)
        self._delete_button.setStyleSheet(self._get_cancel_button_stylesheet())
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
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Verificar si el clic es en el header
            if self._header_widget:
                header_pos = self._header_widget.mapFromGlobal(event.globalPos())
                if self._header_widget.rect().contains(header_pos):
                    child = self._header_widget.childAt(header_pos)
                    # No arrastrar si se hace clic en un botón
                    if isinstance(child, QPushButton):
                        super().mousePressEvent(event)
                        return
                    self._drag_start = event.globalPos()
                    event.accept()
                    return
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for window dragging."""
        if self._drag_start is not None:
            delta = event.globalPos() - self._drag_start
            self.move(self.pos() + delta)
            self._drag_start = event.globalPos()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def showEvent(self, event: QEvent) -> None:
        """Center dialog on screen when shown."""
        super().showEvent(event)
        # Centrar en la pantalla
        screen = self.screen()
        if not screen:
            screen = QApplication.primaryScreen()
        
        if screen:
            screen_geometry = screen.availableGeometry()
            dialog_geometry = self.frameGeometry()
            self.move(
                screen_geometry.left() + (screen_geometry.width() - dialog_geometry.width()) // 2,
                screen_geometry.top() + (screen_geometry.height() - dialog_geometry.height()) // 2
            )

