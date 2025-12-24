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
    QInputDialog,
    QMenu,
    QFileDialog
)

from app.core.constants import (
    SIDEBAR_BG, ROUNDED_BG_TOP_OFFSET, ROUNDED_BG_RADIUS, SEPARATOR_LINE_COLOR,
    WORKSPACE_HEADER_HEIGHT, WORKSPACE_BUTTON_HEIGHT
)
from app.core.logger import get_logger
from app.ui.widgets.folder_tree_icon_utils import load_folder_icon_with_fallback
from app.ui.widgets.toolbar_navigation_buttons import create_navigation_buttons
from app.ui.utils.rounded_background_painter import paint_rounded_background
from app.ui.widgets.workspace_selector_styles import (
    get_base_stylesheet,
    get_workspace_menu_stylesheet,
    get_state_menu_stylesheet
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
        self._workspace_button = None
        self._add_button = None
        self._focus_button = None
        self._back_button = None
        self._forward_button = None
        self._grid_button = None
        self._list_button = None
        self._file_box_button = None
        self._state_button = None
        self._rename_button = None
        self._setup_ui()
        self._apply_styling()
    
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
        
        # === IZQUIERDA: Botones ===
        # Workspace selector button (fuera del fondo redondeado)
        self._workspace_button = QPushButton()
        self._workspace_button.setObjectName("WorkspaceButton")
        self._workspace_button.setFixedHeight(WORKSPACE_BUTTON_HEIGHT)
        self._workspace_button.setMaximumWidth(180)
        self._workspace_button.clicked.connect(self._on_workspace_button_clicked)
        layout.addWidget(self._workspace_button, 0)
        
        # Espacio entre workspace y los 4 botones
        layout.addSpacing(8)
        
        # Los 4 botones que tendrán fondo redondeado (pintado en paintEvent)
        # Add button
        self._add_button = QPushButton("+")
        self._add_button.setObjectName("HeaderButton")
        self._add_button.setFixedSize(28, 28)
        self._add_button.clicked.connect(self._on_add_clicked)
        layout.addWidget(self._add_button, 0)
        
        # Focus button
        self._focus_button = QPushButton()
        self._focus_button.setObjectName("HeaderButton")
        self._focus_button.setFixedSize(28, 28)
        self._focus_button.setToolTip("Nuevo Focus")
        
        # Cargar icono de carpeta (tamaño pequeño para botón de 28x28)
        icon_loaded = False
        try:
            small_icon_size = QSize(20, 20)
            folder_icon = load_folder_icon_with_fallback(small_icon_size)
            if not folder_icon.isNull():
                self._focus_button.setIcon(folder_icon)
                self._focus_button.setIconSize(small_icon_size)
                icon_loaded = True
        except Exception as e:
            logger.warning(f"No se pudo cargar icono de carpeta para botón Focus: {e}")
        
        if not icon_loaded:
            self._focus_button.setText("📁")
        
        self._focus_button.clicked.connect(self._on_focus_button_clicked)
        layout.addWidget(self._focus_button, 0)
        
        # Navigation buttons (back/forward)
        self._back_button, self._forward_button = create_navigation_buttons(
            self, size=(28, 28), use_default_style=False
        )
        self._back_button.setObjectName("HeaderButton")
        self._forward_button.setObjectName("HeaderButton")
        self._back_button.clicked.connect(self.navigation_back.emit)
        self._forward_button.clicked.connect(self.navigation_forward.emit)
        layout.addWidget(self._back_button, 0)
        layout.addWidget(self._forward_button, 0)
        
        # === CENTRO: Espacio libre ===
        layout.addStretch(1)
        
        # === DERECHA: Botones de vista y acciones ===
        # Separador visual
        layout.addWidget(self._create_separator(), 0)
        
        # Grid button
        self._grid_button = QPushButton("⧉")
        self._grid_button.setObjectName("HeaderButton")
        self._grid_button.setFixedSize(28, 28)
        self._grid_button.setCheckable(True)
        self._grid_button.setChecked(True)  # Grid es la vista por defecto
        self._grid_button.setToolTip("Vista Grid")
        self._grid_button.clicked.connect(self.view_grid_requested.emit)
        layout.addWidget(self._grid_button, 0)
        
        # List button
        self._list_button = QPushButton("☰")
        self._list_button.setObjectName("HeaderButton")
        self._list_button.setFixedSize(28, 28)
        self._list_button.setCheckable(True)
        self._list_button.setChecked(False)
        self._list_button.setToolTip("Vista Lista")
        self._list_button.clicked.connect(self.view_list_requested.emit)
        layout.addWidget(self._list_button, 0)
        
        # Separador visual
        layout.addWidget(self._create_separator(), 0)
        
        # File box button
        self._file_box_button = QPushButton("📦")
        self._file_box_button.setObjectName("HeaderButton")
        self._file_box_button.setFixedSize(28, 28)
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
        self._state_button.setFixedWidth(28)
        self._state_button.setToolTip("Estados")
        self._attach_state_menu(self._state_button)
        layout.addWidget(self._state_button, 0)
        
        # Set fixed height for the entire widget
        self.setFixedHeight(WORKSPACE_HEADER_HEIGHT)
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        widget_rect = self.rect().adjusted(0, 0, -1, -1)
        bg_color = QColor(SIDEBAR_BG)
        
        paint_rounded_background(painter, widget_rect, bg_color)
        
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
        
        button_rect = self._workspace_button.geometry()
        y_local = button_rect.bottom()
        menu_pos = self._workspace_button.mapToGlobal(QPoint(button_rect.left(), y_local))
        menu.exec(menu_pos)
    
    def _on_menu_item_selected(self, workspace_id: str) -> None:
        """Handle workspace selection from menu."""
        self.workspace_selected.emit(workspace_id)
    
    def _on_add_clicked(self) -> None:
        """Handle + button click - create new workspace."""
        if not self._workspace_manager:
            return
        
        name, ok = QInputDialog.getText(
            self,
            "Nuevo Workspace",
            "Nombre del workspace:",
            text=""
        )
        
        if ok and name.strip():
            workspace = self._workspace_manager.create_workspace(name.strip())
            self._refresh_workspaces()
            self.workspace_selected.emit(workspace.id)
    
    def _on_workspace_changed(self, workspace_id: str) -> None:
        """Handle workspace change from manager."""
        self._refresh_workspaces()
    
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
    
    def update_button_styles(self, grid_checked: bool) -> None:
        """Update button checked states to reflect current view."""
        if self._grid_button and self._list_button:
            self._grid_button.setChecked(grid_checked)
            self._list_button.setChecked(not grid_checked)
    
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
        
        menu = QMenu(button)
        menu.setStyleSheet(self._get_menu_stylesheet("state"))
        
        self._create_state_action(menu, "Pendiente", STATE_PENDING)
        self._create_state_action(menu, "Entregado", STATE_DELIVERED)
        self._create_state_action(menu, "Corregido", STATE_CORRECTED)
        self._create_state_action(menu, "Revisar", STATE_REVIEW)
        menu.addSeparator()
        self._create_state_action(menu, "Quitar estado", None)
        
        button.setMenu(menu)
        
        if button.receivers("clicked()") > 0:
            button.clicked.disconnect()
        button.clicked.connect(lambda: self._show_state_menu_at_position(button, menu))
    
    def _show_state_menu_at_position(self, button: QPushButton, menu: QMenu) -> None:
        """Show state menu at correct position below button."""
        button_rect = button.geometry()
        y_local = button_rect.bottom()
        menu_pos = button.mapToGlobal(QPoint(button_rect.left(), y_local))
        menu.exec(menu_pos)
    
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
