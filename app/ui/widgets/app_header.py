"""AppHeader - Header simple y profesional estilo Finder.

Header compacto con navegación, vista, búsqueda y ajustes.
Completamente fijo - no personalizable.
"""

from typing import Optional, Callable
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QMenu, QFrame,
    QColorDialog
)

from app.core.constants import DEBUG_LAYOUT
from app.ui.widgets.toolbar_navigation_buttons import create_navigation_buttons
from app.services.settings_service import SettingsService

try:
    from app.ui.widgets.state_badge_widget import (
        STATE_CORRECTED, STATE_DELIVERED, STATE_PENDING, STATE_REVIEW
    )
except ImportError:
    STATE_CORRECTED = None
    STATE_DELIVERED = None
    STATE_PENDING = None
    STATE_REVIEW = None


class AppHeader(QWidget):
    """Header simple y profesional con controles esenciales."""

    _HEADER_STYLESHEET = """
        QWidget#AppHeader {
            background-color: #F5F5F7;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }
        QLineEdit {
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-radius: 8px;
            padding: 8px 12px 8px 36px;
            color: rgba(0, 0, 0, 0.85);
            /* font-size: establecido explícitamente */
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

    _NAV_BUTTON_STYLESHEET = """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 8px;
            color: rgba(0, 0, 0, 0.65);
            /* font-size: establecido explícitamente */
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: rgba(0, 0, 0, 0.08);
            color: rgba(0, 0, 0, 0.85);
        }
        QPushButton:pressed {
            background-color: rgba(0, 0, 0, 0.12);
        }
        QPushButton:disabled {
            color: rgba(0, 0, 0, 0.3);
        }
    """

    _VIEW_CONTAINER_STYLESHEET = """
        QWidget#ViewContainer {
            background-color: rgba(0, 0, 0, 0.05);
            border-radius: 8px;
        }
        QPushButton#ViewGridButton, QPushButton#ViewListButton {
            background-color: transparent;
            border: none;
            border-radius: 6px;
            color: rgba(0, 0, 0, 0.65);
            /* font-size: establecido explícitamente */
            font-weight: 500;
        }
        QPushButton#ViewGridButton:hover, QPushButton#ViewListButton:hover {
            background-color: rgba(0, 0, 0, 0.08);
            color: rgba(0, 0, 0, 0.85);
        }
        QPushButton#ViewGridButton:checked, QPushButton#ViewListButton:checked {
            background-color: rgba(0, 0, 0, 0.12);
            color: rgba(0, 0, 0, 0.85);
            font-weight: 600;
        }
    """

    _SEARCH_ICON_STYLESHEET = """
        QLabel#SearchIcon {
            color: rgba(0, 0, 0, 0.5);
            /* font-size: establecido explícitamente */
            padding: 0px;
            background-color: transparent;
        }
    """

    _MENU_BUTTON_STYLESHEET = """
        QPushButton#StateButton, QPushButton#SettingsButton {
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-radius: 8px;
            color: rgba(0, 0, 0, 0.85);
            /* font-size: establecido explícitamente */
            font-weight: 400;
            padding: 8px 12px;
        }
        QPushButton#StateButton:hover, QPushButton#SettingsButton:hover {
            background-color: rgba(255, 255, 255, 0.95);
            border-color: rgba(0, 0, 0, 0.2);
            color: rgba(0, 0, 0, 0.95);
        }
        QPushButton#StateButton:pressed, QPushButton#SettingsButton:pressed {
            background-color: rgba(255, 255, 255, 1.0);
        }
        QPushButton#StateButton::menu-indicator, QPushButton#SettingsButton::menu-indicator {
            image: none;
            width: 0px;
        }
    """

    _SEPARATOR_STYLESHEET = """
        QFrame#AppHeaderSeparator {
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

    navigation_back = Signal()
    navigation_forward = Signal()
    state_button_clicked = Signal(str)
    search_changed = Signal(str)
    search_submitted = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("AppHeader")
        self.setStyleSheet(self._HEADER_STYLESHEET)
        
        self._back_button: Optional[QPushButton] = None
        self._forward_button: Optional[QPushButton] = None
        self._grid_button: Optional[QPushButton] = None
        self._list_button: Optional[QPushButton] = None
        self._search: Optional[QLineEdit] = None
        self._state_button: Optional[QPushButton] = None
        self._settings_button: Optional[QPushButton] = None
        self._workspace_label: Optional[QLabel] = None
        self._search_icon: Optional[QLabel] = None
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._setup_base_configuration()
        layout = self._create_main_layout()
        self._setup_navigation_buttons(layout)
        self._setup_view_controls(layout)
        self._setup_search_field(layout)
        self._setup_menu_buttons(layout)

    def _setup_base_configuration(self) -> None:
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(False)

    def _create_main_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        return layout

    def _setup_navigation_buttons(self, layout: QHBoxLayout) -> None:
        self._back_button, self._forward_button = create_navigation_buttons(
            self, size=(36, 36), use_default_style=False
        )
        self._back_button.clicked.connect(self.navigation_back.emit)
        self._forward_button.clicked.connect(self.navigation_forward.emit)
        self._back_button.setStyleSheet(self._NAV_BUTTON_STYLESHEET)
        self._forward_button.setStyleSheet(self._NAV_BUTTON_STYLESHEET)
        
        layout.addWidget(self._back_button, 0)
        layout.addWidget(self._forward_button, 0)
        layout.addSpacing(4)
        self._add_separator(layout)

    def _setup_view_controls(self, layout: QHBoxLayout) -> None:
        view_container = QWidget(self)
        view_container.setObjectName("ViewContainer")
        view_container.setFixedSize(134, 36)
        
        view_layout = QHBoxLayout(view_container)
        view_layout.setContentsMargins(3, 0, 3, 0)
        view_layout.setSpacing(0)
        view_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self._grid_button = QPushButton("Grid", view_container)
        self._grid_button.setCheckable(True)
        self._grid_button.setChecked(True)
        self._grid_button.setFixedSize(64, 36)
        self._grid_button.setObjectName("ViewGridButton")
        
        self._list_button = QPushButton("List", view_container)
        self._list_button.setCheckable(True)
        self._list_button.setFixedSize(64, 36)
        self._list_button.setObjectName("ViewListButton")
        
        view_container.setStyleSheet(self._VIEW_CONTAINER_STYLESHEET)
        view_layout.addWidget(self._grid_button, 0)
        view_layout.addWidget(self._list_button, 0)
        layout.addWidget(view_container, 0)
        self._add_separator(layout)

    def _setup_search_field(self, layout: QHBoxLayout) -> None:
        search_container = QWidget(self)
        search_container.setObjectName("SearchContainer")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        search_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self._search = QLineEdit(search_container)
        self._search.setObjectName("SearchField")
        self._search.setPlaceholderText("Buscar (Ctrl+K)")
        self._search.setMinimumWidth(240)
        self._search.setMaximumWidth(500)
        self._search.setFixedHeight(36)
        self._search.returnPressed.connect(lambda: self.search_submitted.emit(self._search.text()))
        self._search.textChanged.connect(lambda text: self.search_changed.emit(text))
        
        self._search_icon = QLabel("🔍", self._search)
        self._search_icon.setObjectName("SearchIcon")
        self._search_icon.setFixedSize(20, 20)
        self._search_icon.setStyleSheet(self._SEARCH_ICON_STYLESHEET)
        self._search_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._search_icon.move(12, 8)
        
        search_layout.addWidget(self._search, 1)
        layout.addWidget(search_container, 1)
        self._add_separator(layout)

    def _setup_menu_buttons(self, layout: QHBoxLayout) -> None:
        self._state_button = QPushButton("Estados ▼", self)
        self._state_button.setFixedSize(100, 36)
        self._state_button.setObjectName("StateButton")
        self._state_button.setStyleSheet(self._MENU_BUTTON_STYLESHEET)
        self._attach_state_menu(self._state_button)
        layout.addWidget(self._state_button, 0)
        
        self._add_separator(layout)

        self._settings_button = QPushButton("Ajustes ▼", self)
        self._settings_button.setFixedSize(100, 36)
        self._settings_button.setObjectName("SettingsButton")
        self._settings_button.setStyleSheet(self._MENU_BUTTON_STYLESHEET)
        self._create_settings_menu()
        layout.addWidget(self._settings_button, 0)

        self._workspace_label = QLabel("", self)
        self._workspace_label.setVisible(False)

    def _add_separator(self, layout: QHBoxLayout) -> None:
        separator = QFrame(self)
        separator.setObjectName("AppHeaderSeparator")
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedWidth(1)
        separator.setFixedHeight(24)
        separator.setStyleSheet(self._SEPARATOR_STYLESHEET)
        layout.addWidget(separator, 0)

    def _attach_state_menu(self, button: QPushButton) -> None:
        menu = QMenu(button)
        menu.setStyleSheet(self._MENU_STYLESHEET)
        
        if STATE_PENDING and STATE_DELIVERED and STATE_CORRECTED and STATE_REVIEW:
            menu.addAction("Pendiente").triggered.connect(
                lambda: self.state_button_clicked.emit(STATE_PENDING)
            )
            menu.addAction("Entregado").triggered.connect(
                lambda: self.state_button_clicked.emit(STATE_DELIVERED)
            )
            menu.addAction("Corregido").triggered.connect(
                lambda: self.state_button_clicked.emit(STATE_CORRECTED)
            )
            menu.addAction("Revisar").triggered.connect(
                lambda: self.state_button_clicked.emit(STATE_REVIEW)
            )
            menu.addSeparator()
            menu.addAction("Quitar estado").triggered.connect(
                lambda: self.state_button_clicked.emit(None)
            )
        
        button.setMenu(menu)

    def _create_settings_menu(self) -> None:
        menu = QMenu(self._settings_button)
        menu.setStyleSheet(self._MENU_STYLESHEET)
        
        menu.addAction("Tema").triggered.connect(self._on_theme_clicked)
        menu.addAction("Idioma").triggered.connect(self._on_language_clicked)
        menu.addAction("Tamaño de Iconos").triggered.connect(self._on_icon_size_clicked)
        menu.addSeparator()
        
        autosave_action = menu.addAction("Autoguardado")
        autosave_action.setCheckable(True)
        autosave_action.triggered.connect(self._on_autosave_toggled)
        
        startup_action = menu.addAction("Inicio Automático")
        startup_action.setCheckable(True)
        startup_action.triggered.connect(self._on_startup_toggled)
        
        taskbar_action = menu.addAction("Ocultar Barra de Tareas")
        taskbar_action.setCheckable(True)
        taskbar_action.triggered.connect(self._on_taskbar_toggled)
        menu.addSeparator()
        
        # Placeholder para futura implementación
        menu.addAction("Recuperar Focus").triggered.connect(self._on_recover_focus_clicked)
        menu.addAction("Limpiar Focus").triggered.connect(self._on_clean_focus_clicked)
        menu.addSeparator()
        
        menu.addAction("Color de Fondo").triggered.connect(self._on_bg_color_clicked)
        menu.addAction("Color del Título").triggered.connect(self._on_title_color_clicked)
        menu.addAction("Color del Borde").triggered.connect(self._on_border_color_clicked)
        menu.addSeparator()
        
        # Placeholder para futura implementación
        menu.addAction("Restaurar y Salir").triggered.connect(self._on_restore_exit_clicked)
        
        self._settings_button.setMenu(menu)
        self._menu_autosave_action = autosave_action
        self._menu_startup_action = startup_action
        self._menu_taskbar_action = taskbar_action

    def update_workspace(self, workspace_name_or_path: Optional[str]) -> None:
        if not self._workspace_label:
            return
        if not workspace_name_or_path:
            self._workspace_label.setText("")
            return
        if os.sep in workspace_name_or_path or (os.altsep and os.altsep in workspace_name_or_path):
            workspace_name = os.path.basename(workspace_name_or_path) or workspace_name_or_path.rstrip(os.sep)
        else:
            workspace_name = workspace_name_or_path
        self._workspace_label.setText(workspace_name)

    def get_grid_button(self) -> QPushButton:
        return self._grid_button

    def get_list_button(self) -> QPushButton:
        return self._list_button

    def set_nav_enabled(self, can_back: bool, can_forward: bool) -> None:
        if self._back_button:
            self._back_button.setEnabled(can_back)
        if self._forward_button:
            self._forward_button.setEnabled(can_forward)

    def update_button_styles(self, grid_checked: bool) -> None:
        if self._grid_button and self._list_button:
            self._grid_button.setChecked(grid_checked)
            self._list_button.setChecked(not grid_checked)

    def paintEvent(self, event):
        if DEBUG_LAYOUT:
            super().paintEvent(event)
            return
        
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        p.fillRect(rect, QColor("#F5F5F7"))
        p.setPen(QColor(0, 0, 0, 26))
        p.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
        p.end()
        super().paintEvent(event)

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

