"""
WorkspaceSelector - Workspace selection widget.

Horizontal compact bar for selecting and managing workspaces.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, Signal, QPoint, QSize, QTimer
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
    QMenu,
    QFileDialog,
    QDialog
)

from app.core.constants import (
    SIDEBAR_BG, ROUNDED_BG_TOP_OFFSET, ROUNDED_BG_RADIUS, SEPARATOR_LINE_COLOR,
    WORKSPACE_HEADER_HEIGHT, WORKSPACE_BUTTON_HEIGHT, CENTRAL_AREA_BG, CENTRAL_AREA_BG_LIGHT,
    CONTENT_LEFT_MARGIN, SIDEBAR_DEFAULT_WIDTH
)
from app.core.logger import get_logger
from app.ui.widgets.folder_tree_icon_utils import load_folder_icon_with_fallback
from app.ui.widgets.toolbar_navigation_buttons import create_navigation_buttons
from app.ui.utils.rounded_background_painter import paint_rounded_background
from app.ui.widgets.view_icon_utils import load_view_icon
from app.ui.windows.input_dialog import InputDialog
from app.ui.windows.error_dialog import ErrorDialog
from app.ui.windows.confirmation_dialog import ConfirmationDialog
from app.ui.widgets.workspace_selector_styles import (
    get_base_stylesheet,
    get_workspace_menu_stylesheet,
    get_state_menu_stylesheet,
    get_view_toggle_button_style,
    get_workspace_button_dark_stylesheet,
    get_file_box_button_active_stylesheet
)

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.managers.workspace_manager import WorkspaceManager

# Constantes para truncamiento de nombres de workspace
MAX_WORKSPACE_NAME_DISPLAY_LENGTH = 15
TRUNCATE_TO_LENGTH = 12

# Constantes de layout
LAYOUT_LEFT_MARGIN = 12
LAYOUT_SPACING = 6
NAV_VISUAL_OFFSET = 27  # Ajuste visual adicional para botones de navegación


class WorkspaceSelector(QWidget):
    """Horizontal compact bar for workspace selection."""
    
    workspace_selected = Signal(str)  # Emitted when workspace is selected (workspace_id)
    new_focus_requested = Signal(str)  # Emitted when new focus is requested (folder_path)
    navigation_back = Signal()  # Emitted when back button is clicked
    navigation_forward = Signal()  # Emitted when forward button is clicked
    view_grid_requested = Signal()  # Emitted when grid button is clicked
    view_list_requested = Signal()  # Emitted when list button is clicked
    file_box_requested = Signal()  # Emitted when file box button is clicked
    state_button_clicked = Signal(str)  # Emitted when state menu item is clicked (state constant or None)
    rename_clicked = Signal()  # Emitted when rename button is clicked
    rename_state_requested = Signal()  # Emitted when rename state label is requested
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize WorkspaceSelector.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setObjectName("WorkspaceSelector")
        self.setAutoFillBackground(False)
        self._workspace_manager = None
        self._state_label_manager = None
        self._tab_manager = None
        self._sidebar = None
        self._signal_controller = None
        self._workspace_button = None
        self._focus_button = None
        self._back_button = None
        self._forward_button = None
        self._grid_button = None
        self._list_button = None
        self._file_box_button = None
        self._state_button = None
        self._rename_button = None
        self._state_menu = None
        
        # Inicializar color del tema desde AppSettings
        from app.managers import app_settings as app_settings_module
        if app_settings_module.app_settings is not None:
            color_theme = app_settings_module.app_settings.central_area_color
            self._theme_color = CENTRAL_AREA_BG_LIGHT if color_theme == "light" else CENTRAL_AREA_BG
        else:
            self._theme_color = CENTRAL_AREA_BG
        
        self._setup_ui()
        self._apply_styling()
        
        # Conectar señal de cambio de tema después de setup_ui
        if app_settings_module.app_settings is not None:
            app_settings_module.app_settings.central_area_color_changed.connect(self._on_theme_changed)
    
    def set_workspace_manager(self, workspace_manager: Optional['WorkspaceManager']) -> None:
        """
        Set WorkspaceManager instance.
        
        Args:
            workspace_manager: WorkspaceManager instance.
        """
        self._workspace_manager = workspace_manager
        self._refresh_workspaces()
        
        if workspace_manager:
            workspace_manager.workspace_created.connect(self._refresh_workspaces)
            workspace_manager.workspace_deleted.connect(self._refresh_workspaces)
            workspace_manager.workspace_changed.connect(self._on_workspace_changed)
    
    def set_state_label_manager(self, state_label_manager) -> None:
        """
        Set StateLabelManager instance.
        
        Args:
            state_label_manager: StateLabelManager instance.
        """
        self._state_label_manager = state_label_manager
        if state_label_manager:
            state_label_manager.labels_changed.connect(self._refresh_state_menu)
            self._refresh_state_menu()
    
    def set_tab_manager(self, tab_manager) -> None:
        """
        Set TabManager instance for workspace operations.
        
        Args:
            tab_manager: TabManager instance.
        """
        self._tab_manager = tab_manager
    
    def set_sidebar(self, sidebar) -> None:
        """
        Set FolderTreeSidebar instance for workspace operations.
        
        Args:
            sidebar: FolderTreeSidebar instance.
        """
        self._sidebar = sidebar
    
    def set_signal_controller(self, signal_controller) -> None:
        """
        Set signal controller for workspace operations.
        
        Args:
            signal_controller: Object with disconnect_signals() and reconnect_signals() methods.
        """
        self._signal_controller = signal_controller
    
    def _setup_ui(self) -> None:
        """Build UI layout as horizontal compact bar."""
        layout = QHBoxLayout(self)
        button_height = WORKSPACE_BUTTON_HEIGHT
        widget_height = WORKSPACE_HEADER_HEIGHT
        visual_area_height = widget_height - ROUNDED_BG_TOP_OFFSET
        vertical_centering = (visual_area_height - button_height) // 2
        top_margin = ROUNDED_BG_TOP_OFFSET + vertical_centering
        bottom_margin = vertical_centering
        layout.setContentsMargins(LAYOUT_LEFT_MARGIN, top_margin, LAYOUT_LEFT_MARGIN, bottom_margin)
        layout.setSpacing(LAYOUT_SPACING)

        # === IZQUIERDA: Workspace button ===
        self._workspace_button = QPushButton()
        self._workspace_button.setObjectName("WorkspaceButton")
        self._workspace_button.setFixedHeight(WORKSPACE_BUTTON_HEIGHT)
        self._workspace_button.setFixedWidth(220)
        self._workspace_button.setStyleSheet(get_workspace_button_dark_stylesheet())
        self._workspace_button.clicked.connect(self._on_workspace_button_clicked)
        layout.addWidget(self._workspace_button, 0)

        # Espacio entre workspace y botones
        layout.addSpacing(8)

        # Focus button
        self._focus_button = QPushButton()
        self._focus_button.setObjectName("HeaderButton")
        self._focus_button.setFixedSize(75, 28)
        self._focus_button.setToolTip("Nueva Carpeta")

        # Cargar icono de carpeta (tamaño pequeño para botón de 28x28)
        small_icon_size = QSize(20, 20)
        folder_icon = None

        try:
            folder_icon = load_folder_icon_with_fallback(small_icon_size)
        except Exception as e:
            logger.warning(f"No se pudo cargar icono de carpeta para botón Focus: {e}")

        if folder_icon and not folder_icon.isNull():
            self._focus_button.setIcon(folder_icon)
            self._focus_button.setIconSize(small_icon_size)
        else:
            self._focus_button.setText("📁")

        self._focus_button.clicked.connect(self._on_focus_button_clicked)
        layout.addWidget(self._focus_button, 0)

        # Offset para alinear navegación con contenido central + ajuste visual
        layout.addSpacing(SIDEBAR_DEFAULT_WIDTH + CONTENT_LEFT_MARGIN - LAYOUT_LEFT_MARGIN + NAV_VISUAL_OFFSET)

        # Navigation buttons (back/forward) alineados con contenido central
        self._back_button, self._forward_button = create_navigation_buttons(
            self, size=(28, 28), use_default_style=False
        )
        self._back_button.setObjectName("HeaderButton")
        self._forward_button.setObjectName("HeaderButton")
        self._back_button.clicked.connect(self.navigation_back.emit)
        self._forward_button.clicked.connect(self.navigation_forward.emit)
        layout.addWidget(self._back_button, 0)
        layout.addWidget(self._forward_button, 0)

        # Separador visual
        layout.addWidget(self._create_separator(), 0)
        
        # Grid button
        self._grid_button = QPushButton()
        self._grid_button.setObjectName("ViewToggleButton")
        self._grid_button.setFixedSize(28, 28)
        self._grid_button.setCheckable(True)
        self._grid_button.setChecked(True)  # Grid es la vista por defecto
        self._grid_button.setToolTip("Vista Grid")
        icon_size = QSize(20, 20)
        grid_icon = load_view_icon("grid.svg", icon_size, True)
        if not grid_icon.isNull():
            self._grid_button.setIcon(grid_icon)
            self._grid_button.setIconSize(icon_size)
        else:
            self._grid_button.setText("⧉")
        self._grid_button.clicked.connect(self.view_grid_requested.emit)
        self._grid_button.toggled.connect(lambda checked: self._update_view_button_icon_and_style(self._grid_button, "grid.svg", checked))
        self._update_view_button_style(self._grid_button, True)
        layout.addWidget(self._grid_button, 0)
        
        # List button
        self._list_button = QPushButton()
        self._list_button.setObjectName("ViewToggleButton")
        self._list_button.setFixedSize(28, 28)
        self._list_button.setCheckable(True)
        self._list_button.setChecked(False)
        self._list_button.setToolTip("Vista Lista")
        list_icon = load_view_icon("lista.svg", icon_size, False)
        if not list_icon.isNull():
            self._list_button.setIcon(list_icon)
            self._list_button.setIconSize(icon_size)
        else:
            self._list_button.setText("☰")
        self._list_button.clicked.connect(self.view_list_requested.emit)
        self._list_button.toggled.connect(lambda checked: self._update_view_button_icon_and_style(self._list_button, "lista.svg", checked))
        self._update_view_button_style(self._list_button, False)
        layout.addWidget(self._list_button, 0)

        # Stretch para empujar los botones finales a la derecha
        layout.addStretch(1)

        # File box button
        self._file_box_button = QPushButton("📦")
        self._file_box_button.setObjectName("HeaderButton")
        self._file_box_button.setFixedSize(75, 28)
        self._file_box_button.setToolTip("Caja de archivos")
        self._file_box_button.clicked.connect(self.file_box_requested.emit)
        layout.addWidget(self._file_box_button, 0)

        # Rename button
        self._rename_button = QPushButton("Renombrar")
        self._rename_button.setObjectName("WorkspaceButton")
        self._rename_button.setFixedHeight(WORKSPACE_BUTTON_HEIGHT)
        self._rename_button.setMinimumWidth(80)
        self._rename_button.setMaximumWidth(180)
        self._rename_button.setToolTip("Renombrar archivos seleccionados")
        self._rename_button.setEnabled(False)
        self._rename_button.clicked.connect(self.rename_clicked.emit)
        layout.addWidget(self._rename_button, 0)

        # State button
        self._state_button = QPushButton("🏷️")
        self._state_button.setObjectName("StateButton")
        self._state_button.setFixedHeight(WORKSPACE_BUTTON_HEIGHT)
        self._state_button.setFixedWidth(75)
        self._state_button.setToolTip("Estados")
        self._attach_state_menu(self._state_button)
        layout.addWidget(self._state_button, 0)

        # Set fixed height for the entire widget
        self.setFixedHeight(WORKSPACE_HEADER_HEIGHT)
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        widget_rect = self.rect().adjusted(0, 0, -1, -1)
        bg_color = QColor(self._theme_color)  # Usar color del tema dinámico

        paint_rounded_background(painter, widget_rect, bg_color)
        
        # Pintar offset visual para el botón de workspace
        if self._workspace_button:
            button_rect = self._workspace_button.geometry()
            if button_rect.isValid():
                # Offset visual: sombra sutil alrededor del botón
                offset_rect = button_rect.adjusted(-2, -2, 2, 2)
                painter.setPen(QColor(0, 0, 0, 20))
                painter.setBrush(QColor(0, 0, 0, 5))
                painter.drawRoundedRect(offset_rect, 8, 8)
        
        painter.end()
        super().paintEvent(event)
    
    def _apply_styling(self) -> None:
        """Apply stylesheet to widget."""
        self.setStyleSheet(get_base_stylesheet())
    
    def _refresh_workspaces(self) -> None:
        """Refresh workspace button text from manager."""
        if not self._workspace_manager or not self._workspace_button:
            return
        
        active_id = self._workspace_manager.get_active_workspace_id()
        if active_id:
            active_workspace = self._workspace_manager.get_workspace(active_id)
            if active_workspace:
                name = active_workspace.name
                if len(name) > MAX_WORKSPACE_NAME_DISPLAY_LENGTH:
                    name = name[:TRUNCATE_TO_LENGTH] + "..."
                self._workspace_button.setText(f"{name} ▼")
            else:
                self._workspace_button.setText("Sin workspace ▼")
        else:
            self._workspace_button.setText("Sin workspace ▼")
    
    def _get_menu_stylesheet(self, menu_type: str) -> str:
        """Get stylesheet for menu based on type."""
        if menu_type == "workspace":
            return get_workspace_menu_stylesheet()
        else:  # "state"
            return get_state_menu_stylesheet()
    
    def _on_workspace_button_clicked(self) -> None:
        """Handle workspace button click - show dropdown menu."""
        if not self._workspace_manager:
            return
        
        workspaces = self._workspace_manager.get_workspaces()
        active_id = self._workspace_manager.get_active_workspace_id()
        
        menu = QMenu(self)
        menu.setStyleSheet(self._get_menu_stylesheet("workspace"))
        
        for workspace in workspaces:
            is_active = workspace.id == active_id
            action = menu.addAction(workspace.name)
            action.setCheckable(True)
            action.setChecked(is_active)
            action.triggered.connect(lambda checked, ws_id=workspace.id: self._on_menu_item_selected(ws_id))
        
        menu.addSeparator()
        create_action = menu.addAction("+ Nuevo workspace")
        create_action.triggered.connect(self._on_add_clicked)
        
        # Añadir opciones de renombrar y eliminar workspace activo
        if active_id:
            menu.addSeparator()
            reorder_action = menu.addAction("Reordenar workspace")
            reorder_action.triggered.connect(self._on_reorder_workspace_clicked)
            rename_action = menu.addAction("Renombrar workspace…")
            rename_action.triggered.connect(self._on_rename_workspace_clicked)
            delete_action = menu.addAction("Eliminar workspace…")
            delete_action.triggered.connect(self._on_delete_workspace_clicked)
        
        button_rect = self._workspace_button.geometry()
        y_local = button_rect.bottom()
        menu_pos = self._workspace_button.mapToGlobal(QPoint(button_rect.left(), y_local))
        menu.exec(menu_pos)
    
    def _on_reorder_workspace_clicked(self) -> None:
        """Handle reorder workspace action - show reorder dialog."""
        if not self._workspace_manager:
            return
        
        from app.ui.windows.reorder_workspaces_dialog import ReorderWorkspacesDialog
        
        workspaces = self._workspace_manager.get_workspaces()
        if not workspaces:
            return
        
        dialog = ReorderWorkspacesDialog(workspaces, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            reordered_workspaces = dialog.get_reordered_workspaces()
            if reordered_workspaces:
                # Obtener IDs en el nuevo orden
                workspace_ids = [ws.id for ws in reordered_workspaces]
                # Reordenar en el manager
                if self._workspace_manager.reorder_workspaces(workspace_ids):
                    # Refrescar la lista de workspaces
                    self._refresh_workspaces()
    
    def _on_menu_item_selected(self, workspace_id: str) -> None:
        """Handle workspace selection from menu."""
        self.workspace_selected.emit(workspace_id)
    
    def _on_add_clicked(self) -> None:
        """Handle + button click - create new workspace."""
        if not self._workspace_manager:
            return
        
        dialog = InputDialog(
            parent=self,
            title="Nuevo Workspace",
            label="Nombre del workspace:",
            text=""
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_text()
            if name and name.strip():
                workspace = self._workspace_manager.create_workspace(name.strip())
                self._refresh_workspaces()
                self.workspace_selected.emit(workspace.id)
    
    def _on_rename_workspace_clicked(self) -> None:
        """Handle rename workspace action - show dialog and rename."""
        if not self._workspace_manager:
            return
        
        active_workspace = self._workspace_manager.get_active_workspace()
        if not active_workspace:
            return
        
        current_name = active_workspace.name
        workspace_id = active_workspace.id
        
        # Diálogo de entrada con nombre actual pre-rellenado
        dialog = InputDialog(
            parent=self,
            title="Renombrar Workspace",
            label="Nuevo nombre del workspace:",
            text=current_name
        )
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        new_name = dialog.get_text()
        if not new_name:
            return
        
        # Validar que el nombre no esté vacío después de strip
        new_name = new_name.strip()
        if not new_name:
            error_dialog = ErrorDialog(
                parent=self,
                title="Nombre inválido",
                message="El nombre del workspace no puede estar vacío.",
                is_warning=True
            )
            error_dialog.exec()
            return
        
        # Si el nombre no cambió, no hacer nada
        if new_name == current_name:
            return
        
        # Renombrar workspace
        renamed = self._workspace_manager.rename_workspace(workspace_id, new_name)
        
        if renamed:
            # Refrescar UI para mostrar el nuevo nombre
            self._refresh_workspaces()
        else:
            error_dialog = ErrorDialog(
                parent=self,
                title="Error",
                message="No se pudo renombrar el workspace.",
                is_warning=False
            )
            error_dialog.exec()
    
    def _on_delete_workspace_clicked(self) -> None:
        """Handle delete workspace action - show confirmation and delete."""
        if not self._workspace_manager:
            return
        
        active_workspace = self._workspace_manager.get_active_workspace()
        if not active_workspace:
            return
        
        workspace_name = active_workspace.name
        workspace_id = active_workspace.id
        
        # Diálogo de confirmación
        dialog = ConfirmationDialog(
            parent=self,
            title="Eliminar Workspace",
            message=f"¿Estás seguro de que quieres eliminar el workspace \"{workspace_name}\"?\n\n"
                    "Esta acción no se puede deshacer.",
            confirm_text="Eliminar",
            cancel_text="Cancelar"
        )
        
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.is_confirmed():
            return
        
        # Eliminar workspace (el manager guardará estado y hará switch completo si es necesario)
        deleted = self._workspace_manager.delete_workspace(
            workspace_id,
            tab_manager=self._tab_manager,
            sidebar=self._sidebar,
            signal_controller=self._signal_controller
        )
        
        if deleted:
            # El manager ya guardó estado, cambió y cargó el nuevo workspace si era necesario
            # Solo necesitamos actualizar la UI y emitir señal si hay un nuevo workspace activo
            current_active_id = self._workspace_manager.get_active_workspace_id()
            if current_active_id:
                # Emitir señal para que MainWindow actualice la UI
                self.workspace_selected.emit(current_active_id)
            else:
                # Si no hay activo, refrescar para mostrar el nuevo estado
                self._refresh_workspaces()
    
    def _on_workspace_changed(self, workspace_id: str) -> None:
        """Handle workspace change from manager."""
        # Protección defensiva: verificar que el botón existe antes de actualizar
        if self._workspace_button:
            self._refresh_workspaces()
        else:
            # Si el botón aún no existe, programar actualización
            QTimer.singleShot(0, self._refresh_workspaces)
    
    def set_nav_enabled(self, can_back: bool, can_forward: bool) -> None:
        """Update navigation buttons enabled state."""
        if self._back_button:
            self._back_button.setEnabled(can_back)
        if self._forward_button:
            self._forward_button.setEnabled(can_forward)
    
    def _on_focus_button_clicked(self) -> None:
        """Handle focus button click - open folder dialog and emit signal."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder_path:
            self.new_focus_requested.emit(folder_path)
    
    def _update_view_button_icon_and_style(self, button: QPushButton, svg_name: str, checked: bool) -> None:
        """Update view button icon and style based on checked state."""
        icon_size = QSize(20, 20)
        icon = load_view_icon(svg_name, icon_size, checked)
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(icon_size)
        self._update_view_button_style(button, checked)
    
    def _update_view_button_style(self, button: QPushButton, checked: bool) -> None:
        """Update view button style based on checked state."""
        button.setStyleSheet(get_view_toggle_button_style(checked))
    
    def update_button_styles(self, grid_checked: bool) -> None:
        """Update button checked states to reflect current view."""
        if self._grid_button and self._list_button:
            self._grid_button.setChecked(grid_checked)
            self._list_button.setChecked(not grid_checked)
            self._update_view_button_icon_and_style(self._grid_button, "grid.svg", grid_checked)
            self._update_view_button_icon_and_style(self._list_button, "lista.svg", not grid_checked)
    
    def _attach_state_menu(self, button: QPushButton) -> None:
        """Attach state menu to button with proper positioning."""
        try:
            from app.ui.widgets.state_badge_widget import (
                STATE_CORRECTED,
                STATE_DELIVERED,
                STATE_PENDING,
                STATE_REVIEW,
            )
        except ImportError:
            return
        
        self._state_menu = QMenu(button)
        self._state_menu.setStyleSheet(self._get_menu_stylesheet("state"))
        
        self._refresh_state_menu()
        
        # No usar setMenu() porque sobrescribe la posición personalizada
        # button.setMenu(self._state_menu)
        
        if button.receivers("clicked()") > 0:
            button.clicked.disconnect()
        button.clicked.connect(lambda: self._show_state_menu_at_position(button, self._state_menu))
    
    def _refresh_state_menu(self) -> None:
        """Refresh state menu with current labels."""
        if not self._state_menu:
            return
        
        self._state_menu.clear()
        
        try:
            from app.ui.widgets.state_badge_widget import (
                STATE_CORRECTED,
                STATE_DELIVERED,
                STATE_PENDING,
                STATE_REVIEW,
            )
        except ImportError:
            return
        
        # Get current labels (custom or default)
        if self._state_label_manager:
            labels = self._state_label_manager.get_all_labels()
        else:
            from app.ui.widgets.state_badge_widget import STATE_LABELS
            labels = {
                STATE_PENDING: STATE_LABELS.get(STATE_PENDING, "PENDIENTE"),
                STATE_DELIVERED: STATE_LABELS.get(STATE_DELIVERED, "ENTREGADO"),
                STATE_CORRECTED: STATE_LABELS.get(STATE_CORRECTED, "CORREGIDO"),
                STATE_REVIEW: STATE_LABELS.get(STATE_REVIEW, "REVISAR"),
            }
        
        # Add state actions with current labels
        self._create_state_action(self._state_menu, labels.get(STATE_PENDING, "Pendiente"), STATE_PENDING)
        self._create_state_action(self._state_menu, labels.get(STATE_DELIVERED, "Entregado"), STATE_DELIVERED)
        self._create_state_action(self._state_menu, labels.get(STATE_CORRECTED, "Corregido"), STATE_CORRECTED)
        self._create_state_action(self._state_menu, labels.get(STATE_REVIEW, "Revisar"), STATE_REVIEW)
        
        self._state_menu.addSeparator()
        self._create_state_action(self._state_menu, "Quitar estado", None)
        
        # Add rename option
        self._state_menu.addSeparator()
        rename_action = self._state_menu.addAction("Renombrar etiqueta…")
        rename_action.triggered.connect(self.rename_state_requested.emit)
    
    def _show_state_menu_at_position(self, button: QPushButton, menu: QMenu) -> None:
        """Show state menu at correct position below button (centered)."""
        # Ocultar overlay de resize mientras el menú está abierto
        main_window = self.window()
        overlay_was_visible = False
        if main_window and hasattr(main_window, '_resize_edge_overlay'):
            overlay = main_window._resize_edge_overlay
            if overlay and overlay.isVisible():
                overlay_was_visible = True
                overlay.hide()

        # Calcular posición global del botón
        button_global_pos = button.mapToGlobal(button.rect().topLeft())

        # Obtener ancho del menú
        menu_width = menu.sizeHint().width()

        # Alinear borde derecho del menú con borde derecho del botón
        menu_x = button_global_pos.x() + button.width() - menu_width

        # Posición Y justo debajo del botón
        menu_y = button_global_pos.y() + button.height()

        menu_pos = QPoint(menu_x, menu_y)
        menu.exec(menu_pos)

        # Restaurar overlay después de cerrar el menú
        if overlay_was_visible and main_window and hasattr(main_window, '_resize_edge_overlay'):
            overlay = main_window._resize_edge_overlay
            if overlay:
                overlay.show()
                overlay.raise_()
    
    def _create_state_action(self, menu: QMenu, label: str, state: Optional[str]) -> None:
        """Create and connect a state menu action."""
        menu.addAction(label).triggered.connect(lambda: self.state_button_clicked.emit(state))
    
    def _create_separator(self) -> QWidget:
        """Create a visual separator widget."""
        separator = QWidget()
        separator.setFixedWidth(1)
        separator.setFixedHeight(WORKSPACE_BUTTON_HEIGHT)
        separator.setStyleSheet(f"background-color: {SEPARATOR_LINE_COLOR};")
        return separator
    
    def update_selection_count(self, count: int) -> None:
        """Update rename button state based on selection count."""
        if self._rename_button:
            self._rename_button.setEnabled(count >= 1)
    
    def set_file_box_button_active(self, active: bool, minimized: bool = False) -> None:
        """Update file box button visual state to indicate active session."""
        if not self._file_box_button:
            return
        
        if active:
            tooltip = "Caja de archivos (minimizada - click para restaurar)" if minimized else "Caja de archivos (activa)"
            self._file_box_button.setToolTip(tooltip)
            self._file_box_button.setStyleSheet(get_file_box_button_active_stylesheet())
        else:
            self._file_box_button.setToolTip("Caja de archivos")
            self._file_box_button.setStyleSheet("")
    
    def _on_theme_changed(self, color_theme: str) -> None:
        """Actualizar color del tema cuando cambia."""
        self._theme_color = CENTRAL_AREA_BG_LIGHT if color_theme == "light" else CENTRAL_AREA_BG
        self.update()  # Forzar repintado