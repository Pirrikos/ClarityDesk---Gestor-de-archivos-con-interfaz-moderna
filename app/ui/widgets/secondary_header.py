"""SecondaryHeader - Header secundario debajo del AppHeader.

Header visual igual al AppHeader con búsqueda y ajustes.
"""

from typing import Optional, Callable

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPaintEvent
from PySide6.QtWidgets import (
    QHBoxLayout, QWidget, QSizePolicy, QLabel, QLineEdit, QPushButton, QMenu, QFrame,
    QColorDialog
)

from app.core.constants import DEBUG_LAYOUT
from app.services.settings_service import SettingsService


class SecondaryHeader(QWidget):
    """Header secundario con búsqueda y ajustes."""

    _HEADER_STYLESHEET = """
        QWidget#SecondaryHeader {
            background-color: #1A1D22;
            border-bottom: 1px solid #2A2E36;
        }
        QLineEdit {
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-radius: 8px;
            padding: 8px 32px 8px 8px;
            color: rgba(0, 0, 0, 0.85);
            font-weight: 400;
        }
        QLineEdit:focus {
            background-color: #FFFFFF;
            border: 1px solid rgba(0, 0, 0, 0.25);
            color: rgba(0, 0, 0, 0.95);
        }
        QLineEdit::placeholder {
            color: rgba(0, 0, 0, 0.5);
        }
    """

    _SEARCH_ICON_STYLESHEET = """
        QLabel#SearchIcon {
            color: rgba(0, 0, 0, 0.5);
            padding: 0px;
            background-color: transparent;
        }
    """

    _MENU_BUTTON_STYLESHEET = """
        QPushButton#SettingsButton {
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-radius: 8px;
            color: rgba(0, 0, 0, 0.85);
            font-weight: 400;
            padding: 8px 12px;
        }
        QPushButton#SettingsButton:hover {
            background-color: rgba(255, 255, 255, 0.95);
            border-color: rgba(0, 0, 0, 0.2);
            color: rgba(0, 0, 0, 0.95);
        }
        QPushButton#SettingsButton:pressed {
            background-color: rgba(255, 255, 255, 1.0);
        }
        QPushButton#SettingsButton::menu-indicator {
            image: none;
            width: 0px;
        }
    """

    _SEPARATOR_STYLESHEET = """
        QFrame#SecondaryHeaderSeparator {
            background-color: rgba(0, 0, 0, 0.1);
            border: none;
        }
    """

    _MENU_STYLESHEET = """
        QMenu {
            background-color: #FFFFFF;
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-radius: 6px;
            padding: 4px;
        }
        QMenu::item {
            padding: 8px 20px;
            border-radius: 4px;
            color: rgba(0, 0, 0, 0.85);
        }
        QMenu::item:selected {
            background-color: rgba(0, 0, 0, 0.08);
        }
        QMenu::separator {
            height: 1px;
            background-color: rgba(255, 255, 255, 0.1);
            margin: 4px 8px;
        }
    """

    search_changed = Signal(str)
    search_submitted = Signal(str)
    history_panel_toggle_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("SecondaryHeader")
        self.setStyleSheet(self._HEADER_STYLESHEET)
        
        self._search: Optional[QLineEdit] = None
        self._settings_button: Optional[QPushButton] = None
        self._search_icon: Optional[QLabel] = None
        self._workspace_button: Optional[QPushButton] = None
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        self._setup_base_configuration()
        layout = self._create_main_layout()
        # El workspace button se agregará después mediante set_workspace_button
        layout.addStretch(1)  # Empuja todo a la derecha
        self._setup_menu_buttons(layout)
        self._setup_search_field(layout)
    
    def set_workspace_button(self, workspace_button: QPushButton) -> None:
        """Set workspace button from WorkspaceSelector to display in this header."""
        if self._workspace_button:
            return  # Ya está configurado
        
        self._workspace_button = workspace_button
        layout = self.layout()
        if layout and workspace_button:
            # Insertar al inicio del layout (posición 0, antes del stretch)
            # El stretch está en la posición 0 después de crear el layout
            layout.insertWidget(0, workspace_button, 0)

    def _setup_base_configuration(self) -> None:
        """Configure base header properties."""
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(False)

    def _create_main_layout(self) -> QHBoxLayout:
        """Create main horizontal layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        return layout

    def clear_search_text(self) -> None:
        """Limpiar el texto del campo de búsqueda sin disparar señales."""
        if self._search:
            # Desconectar temporalmente la señal para evitar que se reactive la búsqueda
            self._search.blockSignals(True)
            self._search.clear()
            self._search.blockSignals(False)
    
    def _setup_search_field(self, layout: QHBoxLayout) -> None:
        search_container = QWidget(self)
        search_container.setObjectName("SearchContainer")
        search_container.setFixedHeight(36)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        search_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self._search = QLineEdit(search_container)
        self._search.setObjectName("SearchField")
        self._search.setPlaceholderText("Buscar (Ctrl+K)")
        self._search.setMinimumWidth(120)
        self._search.setMaximumWidth(200)
        self._search.setFixedHeight(36)
        self._search.returnPressed.connect(lambda: self.search_submitted.emit(self._search.text()))
        self._search.textChanged.connect(lambda text: self.search_changed.emit(text))
        
        search_layout.addWidget(self._search, 1)
        
        # Icono de búsqueda como widget hijo del QLineEdit, posicionado a la derecha
        self._search_icon = QLabel("🔍", self._search)
        self._search_icon.setObjectName("SearchIcon")
        self._search_icon.setFixedSize(20, 20)
        self._search_icon.setStyleSheet(self._SEARCH_ICON_STYLESHEET)
        self._search_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._search_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Función para actualizar posición del icono cuando cambie el tamaño
        def update_icon_position():
            if self._search and self._search_icon:
                search_width = self._search.width()
                icon_x = search_width - 28  # 8px de margen + 20px de icono
                icon_y = (self._search.height() - 20) // 2  # Centrado vertical
                self._search_icon.move(icon_x, icon_y)
        
        # Sobrescribir resizeEvent del campo de búsqueda para reposicionar el icono
        original_resize = self._search.resizeEvent
        def resize_with_icon(event):
            original_resize(event)
            update_icon_position()
        self._search.resizeEvent = resize_with_icon
        
        # Posicionar inicialmente después de que se muestre
        QTimer.singleShot(0, update_icon_position)
        
        layout.addWidget(search_container, 0)

    def _setup_menu_buttons(self, layout: QHBoxLayout) -> None:
        self._settings_button = QPushButton("Ajustes ▼", self)
        self._settings_button.setFixedSize(100, 36)
        self._settings_button.setObjectName("SettingsButton")
        self._settings_button.setStyleSheet(self._MENU_BUTTON_STYLESHEET)
        self._create_settings_menu()
        layout.addWidget(self._settings_button, 0)

    def _add_separator(self, layout: QHBoxLayout) -> None:
        separator = QFrame(self)
        separator.setObjectName("SecondaryHeaderSeparator")
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedWidth(1)
        separator.setFixedHeight(24)
        separator.setStyleSheet(self._SEPARATOR_STYLESHEET)
        layout.addWidget(separator, 0)

    def _create_settings_menu(self) -> None:
        menu = QMenu(self._settings_button)
        menu.setStyleSheet(self._MENU_STYLESHEET)
        
        menu.addAction("Tema").triggered.connect(self._on_theme_clicked)
        menu.addAction("Mostrar historial").triggered.connect(self._on_history_panel_toggle)
        
        self._settings_button.setMenu(menu)

    def _on_theme_clicked(self) -> None:
        settings = SettingsService()
        current = settings.get_setting("ui.theme", "dark")
        settings.set_setting("ui.theme", "light" if current == "dark" else "dark")

    def _create_selection_menu(self, items: list[tuple[str, Callable[[], None]]]) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(self._MENU_STYLESHEET)
        for label, callback in items:
            menu.addAction(label).triggered.connect(callback)
        menu.exec(self._settings_button.mapToGlobal(self._settings_button.rect().bottomLeft()))

    def _on_language_clicked(self) -> None:
        self._create_selection_menu([
            ("Español", lambda: self._set_language("es")),
            ("English", lambda: self._set_language("en"))
        ])

    def _set_language(self, lang: str) -> None:
        SettingsService().set_setting("ui.language", lang)

    def _on_icon_size_clicked(self) -> None:
        self._create_selection_menu([
            ("Pequeño (64px)", lambda: self._set_icon_size(64)),
            ("Mediano (96px)", lambda: self._set_icon_size(96)),
            ("Grande (128px)", lambda: self._set_icon_size(128))
        ])

    def _set_icon_size(self, size: int) -> None:
        SettingsService().set_setting("ui.icon_size", size)

    def _toggle_setting(self, setting_key: str, action_attr: str) -> None:
        settings = SettingsService()
        current = settings.get_setting(setting_key, False)
        new_value = not current
        settings.set_setting(setting_key, new_value)
        if hasattr(self, action_attr):
            action = getattr(self, action_attr)
            if action:
                action.setChecked(new_value)

    def _on_autosave_toggled(self) -> None:
        self._toggle_setting("ui.autosave", "_menu_autosave_action")

    def _on_startup_toggled(self) -> None:
        self._toggle_setting("ui.startup", "_menu_startup_action")

    def _on_taskbar_toggled(self) -> None:
        self._toggle_setting("ui.taskbar_autohide", "_menu_taskbar_action")

    def _set_color_setting(self, setting_key: str) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            SettingsService().set_setting(setting_key, color.name())

    def _on_bg_color_clicked(self) -> None:
        self._set_color_setting("appearance.background_color")

    def _on_title_color_clicked(self) -> None:
        self._set_color_setting("appearance.title_color")

    def _on_border_color_clicked(self) -> None:
        self._set_color_setting("appearance.border_color")

    def _on_recover_focus_clicked(self) -> None:
        # Placeholder para futura implementación
        pass

    def _on_clean_focus_clicked(self) -> None:
        # Placeholder para futura implementación
        pass

    def _on_restore_exit_clicked(self) -> None:
        # Placeholder para futura implementación
        pass
    
    def _on_history_panel_toggle(self) -> None:
        """Handle history panel toggle request."""
        self.history_panel_toggle_requested.emit()
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint header background and border."""
        if DEBUG_LAYOUT:
            super().paintEvent(event)
            return
        
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        p.fillRect(rect, QColor("#1A1D22"))
        # Línea inferior acorde al estilo del AppHeader
        p.setPen(QColor("#2A2E36"))
        p.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
        p.end()
        super().paintEvent(event)

