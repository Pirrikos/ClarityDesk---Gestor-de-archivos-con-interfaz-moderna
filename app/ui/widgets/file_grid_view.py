"""
FileGridView - Grid/tile view for displaying files.

Shows files as tiles with icons and filenames.
Emits signal on double-click to open file.
"""

import os
from math import ceil
from typing import List, Optional, Tuple, Union, TYPE_CHECKING

from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QContextMenuEvent, QMouseEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget, QGridLayout, QSizePolicy

from app.core.constants import CENTRAL_AREA_BG
from app.managers.tab_manager import TabManager
from app.models.file_stack import FileStack
from app.services.file_category_service import get_categorized_files_with_labels
from app.services.icon_service import IconService
from app.ui.widgets.file_grid_view_drag import drag_enter_event, drag_move_event, drop_event
from app.ui.widgets.file_grid_view_events import (
    resize_event, on_stack_clicked, emit_expansion_height,
    remove_tile_safely, animate_tile_exit
)
from app.ui.widgets.file_grid_view_layout import setup_grid_layout
from app.ui.widgets.grid_tile_manager import TileManager
from app.ui.widgets.file_grid_view_scroll import create_scroll_area, configure_scroll_area
from app.ui.widgets.file_stack_tile import FileStackTile
from app.ui.widgets.file_tile import FileTile
from app.ui.widgets.grid_content_widget import GridContentWidget
from app.ui.widgets.grid_layout_config import calculate_files_per_row, DOCK_DEFAULT_FILES_PER_ROW
from app.ui.widgets.grid_layout_engine import build_dock_layout, build_normal_grid
from app.ui.widgets.expanded_stacks_widget import ExpandedStacksWidget
from app.ui.widgets.grid_selection_logic import (
    clear_selection, select_tile, get_selected_paths, set_selected_states
)
from app.ui.widgets.grid_tile_builder import create_file_tile, create_stack_tile
from app.ui.widgets.file_view_context_menu import show_background_menu, show_item_menu
from app.ui.widgets.file_view_utils import create_refresh_callback

# Temporary import for state manager stub
try:
    from app.managers.file_state_manager import FileStateManager
except ImportError:
    FileStateManager = None

if TYPE_CHECKING:
    from app.ui.windows.desktop_window import DesktopWindow


def _refresh_tile_badge_if_state_matches(tile, state_id: str) -> None:
    """
    Helper para refrescar badge de un tile si coincide el estado.
    
    Maneja RuntimeError silenciosamente (widget puede haber sido eliminado).
    """
    try:
        if isinstance(tile, FileTile) and hasattr(tile, '_state_badge') and tile._state_badge:
            current_state = getattr(tile, '_file_state', None)
            if current_state == state_id:
                tile._state_badge.update()
    except RuntimeError:
        pass


class FileGridView(QWidget):
    """Grid view widget displaying files as tiles."""

    open_file = Signal(str)
    file_dropped = Signal(str)
    file_deleted = Signal(str)
    folder_moved = Signal(str, str)  # Emitted when folder is moved (old_path, new_path)
    stack_expand_requested = Signal(FileStack)
    expansion_height_changed = Signal(int)
    stacks_count_changed = Signal(int)

    def __init__(
        self,
        icon_service: Optional[IconService] = None,
        filesystem_service: Optional = None,
        parent=None,
        tab_manager: Optional[TabManager] = None,
        state_manager=None,
        is_desktop: bool = False,
        desktop_window: Optional['DesktopWindow'] = None,
        get_label_callback: Optional = None
    ):
        """
        Initialize FileGridView with empty file list.
        
        Args:
            icon_service: Service for icon generation.
            filesystem_service: Deprecated, kept for compatibility.
            parent: Parent widget.
            tab_manager: TabManager instance.
            state_manager: FileStateManager instance.
            is_desktop: True if this view represents Desktop Focus.
            desktop_window: Optional DesktopWindow instance (for Desktop Focus context).
            get_label_callback: Optional callback to get state labels.
        """
        super().__init__(parent)
        # _files puede ser lista de paths o lista de tuplas (category_label, files) para categorización
        self._files: Union[List[str], List[Tuple[str, List[str]]]] = []
        self._stacks: list[FileStack] = []
        self._icon_service = icon_service or IconService()
        self._tab_manager = tab_manager
        self._selected_tiles: set[FileTile] = set()
        self._use_stacks = False
        self._expanded_stacks: dict[str, list] = {}
        self._expanded_file_tiles: dict[str, list[FileTile]] = {}
        self._state_manager = state_manager or (FileStateManager() if FileStateManager else None)
        self._get_label_callback = get_label_callback
        # Flag explícito del modo - no se infiere desde la jerarquía
        self._is_desktop_window = is_desktop
        self._desktop_window = desktop_window
        # Desktop files are always visible - stacks are always shown
        self._desktop_files_hidden = True  # Always True - stacks always visible
        # Flag para suprimir transiciones de contenido durante animación de ventana
        # Evita recalcular/animar internamente mientras la geometría cambia
        self._suppress_content_transitions: bool = False
        # Cache para optimización de cálculo de columnas
        self._cached_columns: Optional[int] = None
        self._cached_width: int = 0
        # Cache para categorización de archivos
        self._cached_categorized_files: Optional[Union[List[str], List[Tuple[str, List[str]]]]] = None
        self._cached_file_list_hash: Optional[int] = None
        # Estado del grid: tile_id -> (row, col)
        self._grid_state: dict[str, tuple[int, int]] = {}
        # Tile manager para gestión del ciclo de vida
        self._tile_manager: Optional[TileManager] = None
        # Estado anterior para actualización incremental
        self._previous_files: Optional[Union[List[str], List[Tuple[str, List[str]]]]] = None
        # Flag para diferir refresh del grid hasta que termine la animación de altura
        self._pending_refresh_after_animation: bool = False
        # QStackedWidget para archivos expandidos (solo en modo desktop)
        self._expanded_stacks_widget: Optional[ExpandedStacksWidget] = None
        # Control de animación de reducción (ocultar durante animación, mostrar después)
        self._previous_dock_rows_state: int = 0
        self._show_expanded_after_animation: bool = False
        # Flag para indicar colapso a estado base (sin expansión)
        self._is_collapsing_to_base: bool = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        self.setAcceptDrops(True)
        self.setAutoFillBackground(False)
        
        if not self._is_desktop_window:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
            self.setStyleSheet("QWidget { background-color: transparent; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll = create_scroll_area(self)
        self._content_widget = GridContentWidget(self, self._desktop_window)
        # _is_desktop_window ya está establecido desde __init__ (flag explícito)
        self._use_stacks = self._is_desktop_window
        
        configure_scroll_area(scroll, self._content_widget, self._is_desktop_window)
        
        # Para modo desktop: usar QVBoxLayout con grid de stacks + ExpandedStacksWidget
        if self._is_desktop_window:
            content_layout = QVBoxLayout(self._content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)
            
            # Widget para el grid de stacks (fila 0) - altura fija para evitar rebotes
            self._stacks_container = QWidget()
            self._stacks_container.setContentsMargins(0, 0, 0, 0)
            # Fixed height evita que los stacks "reboten" cuando aparece/desaparece el expanded
            self._stacks_container.setFixedHeight(105)  # 85 (tile) + 20 (nombre + margen)
            self._stacks_container.setSizePolicy(
                QSizePolicy.Policy.Expanding, 
                QSizePolicy.Policy.Fixed
            )
            self._grid_layout = QGridLayout(self._stacks_container)
            # Configurar márgenes del grid de stacks
            # Margin bottom aumentado para dar espacio a los nombres de stacks
            self._grid_layout.setSpacing(12)
            self._grid_layout.setContentsMargins(20, 8, 12, 8)
            self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            content_layout.addWidget(self._stacks_container)
            
            # QStackedWidget para archivos expandidos
            self._expanded_stacks_widget = ExpandedStacksWidget()
            content_layout.addWidget(self._expanded_stacks_widget)
            
            # Stretch al final para empujar todo arriba
            content_layout.addStretch()
        else:
            self._grid_layout = setup_grid_layout(self._content_widget)
        
        # Initialize tile manager
        self._tile_manager = TileManager(
            self,
            self._icon_service,
            self._state_manager,
            self._grid_layout,
            self._content_widget
        )
        
        scroll.setWidget(self._content_widget)
        layout.addWidget(scroll)

    def set_desktop_mode(self, is_desktop: bool) -> None:
        """
        Actualizar explícitamente el estado de Desktop Focus.
        
        Este método se llama cuando cambia el tab activo para asegurar que
        FileGridView sepa correctamente si está mostrando Desktop Focus o una carpeta normal.
        
        Args:
            is_desktop: True si la carpeta activa es Desktop Focus, False en caso contrario.
        """
        self._is_desktop_window = is_desktop
        self._use_stacks = is_desktop
    
    def refresh_state_labels(self, state_id: str) -> None:
        """
        Refrescar labels de estado en todos los tiles visibles.
        
        Cuando se renombra un label de estado, este método actualiza solo el texto
        visible sin reconstruir los tiles.
        
        Args:
            state_id: ID del estado cuyo label cambió.
        """
        # Refrescar tiles seleccionados
        for tile in list(self._selected_tiles):
            _refresh_tile_badge_if_state_matches(tile, state_id)
        
        # Refrescar tiles expandidos (stacks)
        for tiles in self._expanded_file_tiles.values():
            for tile in tiles:
                _refresh_tile_badge_if_state_matches(tile, state_id)
        
        # Refrescar todos los tiles en el tile manager
        if self._tile_manager:
            for tile in self._tile_manager._tiles_by_id.values():
                _refresh_tile_badge_if_state_matches(tile, state_id)
    
    def update_tile_state_visual(self, file_path: str, new_state: Optional[str]) -> bool:
        """
        Actualizar estado visual de un tile específico sin reconstruir el grid.
        
        Args:
            file_path: Ruta del archivo cuyo estado cambió.
            new_state: Nuevo estado (o None para eliminar estado).
            
        Returns:
            True si se encontró y actualizó el tile, False si no existe.
        """
        if not self._tile_manager:
            return False
        
        tile = self._tile_manager.get_tile(file_path)
        if tile and isinstance(tile, FileTile):
            try:
                tile.set_file_state(new_state)
                tile.update()
                return True
            except RuntimeError:
                return False
        
        for tiles in self._expanded_file_tiles.values():
            for t in tiles:
                try:
                    if isinstance(t, FileTile) and t.get_file_path() == file_path:
                        t.set_file_state(new_state)
                        t.update()
                        return True
                except RuntimeError:
                    continue
        
        return False
    
    def update_files(self, file_list: list) -> None:
        """Update displayed files or stacks with incremental updates when possible."""
        
        
        # Almacenar datos y renderizar inmediatamente (como Lista)
        if file_list and isinstance(file_list[0], FileStack):
            old_expanded = self._expanded_stacks.copy()
            self._expanded_stacks = {}
            self._stacks = file_list
            self._files = []
            for stack in self._stacks:
                if stack.stack_type in old_expanded:
                    self._expanded_stacks[stack.stack_type] = stack.files
            # Limpiar cache de categorización cuando hay stacks
            self._cached_categorized_files = None
            self._cached_file_list_hash = None
            self._previous_files = None
        else:
            # Categorizar archivos solo en MainWindow (no en DesktopWindow)
            if not self._is_desktop_window:
                # Cache de categorización: recalcular si lista filtrada cambió
                file_list_hash = hash(tuple(file_list) if file_list else ())
                if (self._cached_categorized_files is None or 
                    self._cached_file_list_hash != file_list_hash):
                    self._files = get_categorized_files_with_labels(file_list or [])
                    self._cached_categorized_files = self._files
                    self._cached_file_list_hash = file_list_hash
                else:
                    self._files = self._cached_categorized_files
            else:
                self._files = file_list
                # Limpiar cache de categorización cuando es desktop window
                self._cached_categorized_files = None
                self._cached_file_list_hash = None
            self._stacks = []
            self._expanded_stacks = {}
        
        # Refresh completo (el nuevo sistema maneja incrementalmente)
        self._previous_files = self._files.copy() if hasattr(self._files, 'copy') else self._files
        self._refresh_tiles()
    

    def _refresh_tiles(self) -> None:
        """Rebuild file tiles or stack tiles in grid layout."""
        # Si estamos en DesktopWindow y la ventana está animando altura,
        # mantener visible el grid anterior sin cambios y NO reconstruir.
        if self._is_desktop_window and self._desktop_window:
            if hasattr(self._desktop_window, '_height_animation_in_progress'):
                if self._desktop_window._height_animation_in_progress:
                    return
        items_to_render = self._stacks if self._stacks else self._files
        
        clear_selection(self)
        
        if self._is_desktop_window:
            # build_dock_layout solo construye stacks
            # Los archivos expandidos son manejados por ExpandedStacksWidget
            build_dock_layout(self, items_to_render, {}, self._grid_layout)
            # Emit stacks count change to adjust window width
            stacks_count = len(self._stacks) if self._stacks else 0
            self.stacks_count_changed.emit(stacks_count)
            
            # Actualizar ExpandedStacksWidget si hay un stack expandido
            self._update_expanded_stack_if_visible()
        else:
            build_normal_grid(self, items_to_render, self._grid_layout)
        
        # Force content widget to recalculate size after adding tiles
        if self._is_desktop_window and self._desktop_window:
            if hasattr(self._desktop_window, '_height_animation_in_progress'):
                if self._desktop_window._height_animation_in_progress:
                    return
        
        # Use QTimer to ensure layout has been processed
        container = getattr(self, '_stacks_container', self._content_widget)
        QTimer.singleShot(0, lambda: container.adjustSize())
        QTimer.singleShot(0, lambda: container.updateGeometry())

    def _on_stack_clicked(self, file_stack: FileStack) -> None:
        """Handle stack click - toggle expansion horizontally below stack."""
        on_stack_clicked(self, file_stack)
    
    
    def _emit_expansion_height(self) -> None:
        """Calculate and emit the height needed for expanded stacks."""
        emit_expansion_height(self)
    
    def _update_expanded_stack_if_visible(self) -> None:
        """Actualizar ExpandedStacksWidget si hay un stack expandido con nuevos archivos."""
        if not self._expanded_stacks_widget:
            return
        
        current_stack_type = self._expanded_stacks_widget.get_current_stack_type()
        if not current_stack_type:
            return
        
        # Buscar archivos actuales del stack expandido
        files = self._expanded_stacks.get(current_stack_type, [])
        if not files:
            # Stack ya no tiene archivos - ocultar y ajustar altura
            self._expanded_stacks_widget.hide_stack()
            self._dock_rows_state = 0
            self._emit_expansion_height()
            return
        
        # Calcular files_per_row basado en el ancho actual
        files_per_row = DOCK_DEFAULT_FILES_PER_ROW
        if self._desktop_window:
            width = self._desktop_window.width()
            files_per_row = calculate_files_per_row(width)
        
        # Calcular nuevo número de filas
        num_rows = ceil(len(files) / files_per_row) if files_per_row > 0 else 1
        num_rows = max(1, min(3, num_rows))
        
        # Actualizar estado de filas y emitir cambio de altura si cambió
        old_rows = getattr(self, '_dock_rows_state', 0) or 0
        if num_rows != old_rows:
            self._dock_rows_state = num_rows
            self._emit_expansion_height()
        
        # Actualizar el widget con los archivos actuales
        self._expanded_stacks_widget.show_stack(
            current_stack_type, files, self, files_per_row
        )

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter for file drop on main widget."""
        drag_enter_event(self, event)

    def dragMoveEvent(self, event) -> None:
        """Handle drag move to maintain drop acceptance."""
        drag_move_event(self, event)

    def dropEvent(self, event) -> None:
        """Handle file drop on main widget."""
        drop_event(self, event)

    def _clear_selection(self) -> None:
        """Clear all tile selections."""
        clear_selection(self)

    def _select_tile(self, tile: FileTile, modifiers: Qt.KeyboardModifiers) -> None:
        """Handle tile selection based on keyboard modifiers."""
        select_tile(self, tile, modifiers)

    def resizeEvent(self, event) -> None:
        """Handle resize to recalculate grid columns."""
        resize_event(self, event)

    def get_selected_paths(self) -> list[str]:
        """Get paths of currently selected files."""
        return get_selected_paths(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press - clear selection if clicking on empty background."""
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_tile, _ = self._get_clicked_tile(event.pos())
            
            # Check if clicked widget is a FileStackTile - let it handle the event
            clicked_widget = self.childAt(event.pos())
            widget = clicked_widget
            while widget is not None and widget != self:
                widget_type = widget.__class__.__name__
                if widget_type == 'FileStackTile':
                    # Let FileStackTile handle the event
                    super().mousePressEvent(event)
                    return
                widget = widget.parent()
            
            if clicked_tile is None:
                # If this is desktop mode and click is on background, propagate to parent DockBackgroundWidget
                if self._is_desktop_window:
                    parent = self.parent()
                    while parent:
                        parent_type = parent.__class__.__name__
                        if parent_type == 'DockBackgroundWidget':
                            # Convert event position to parent coordinates
                            parent_pos = parent.mapFromGlobal(event.globalPos())
                            parent_event = QMouseEvent(
                                event.type(),
                                parent_pos,
                                event.globalPos(),
                                event.button(),
                                event.buttons(),
                                event.modifiers()
                            )
                            parent.mousePressEvent(parent_event)
                            return
                        parent = parent.parent()
                
                self._clear_selection()
                event.accept()
                return
        
        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Show context menu - background menu or item menu depending on click location."""
        refresh_callback = create_refresh_callback(self)
        
        # Detectar si el clic es sobre un tile o sobre el fondo
        clicked_tile, item_path = self._get_clicked_tile(event.pos())
        
        if clicked_tile and item_path:
            # Clic sobre un elemento (archivo/carpeta)
            # Obtener selección múltiple si existe
            selected_paths = self.get_selected_paths()
            
            # Normalizar a lista siempre: usar selección múltiple si hay 2+ elementos, sino usar item_path como lista
            if len(selected_paths) > 1:
                # Hay selección múltiple (2+ elementos)
                item_paths = selected_paths
            else:
                # No hay selección múltiple, usar item_path como lista de 1 elemento
                item_paths = [item_path]
            
            show_item_menu(self, event, item_paths, self._tab_manager, refresh_callback)
        else:
            # Clic sobre el fondo (espacio vacío)
            show_background_menu(self, event, self._tab_manager, refresh_callback)
    
    def _get_clicked_tile(self, pos: QPoint) -> tuple[Optional[object], Optional[str]]:
        """
        Detectar si el clic es sobre un tile o sobre el fondo.
        
        Args:
            pos: Posición del clic en coordenadas del widget (FileGridView).
            
        Returns:
            Tuple de (tile_widget, item_path) o (None, None) si es fondo.
        """
        # Convertir posición a coordenadas del content_widget
        content_pos = self._content_widget.mapFrom(self, pos)
        
        # Buscar widget hijo en la posición del clic
        child_widget = self._content_widget.childAt(content_pos)
        
        if not child_widget:
            return None, None
        
        # Verificar si el widget o alguno de sus padres es un tile
        widget = child_widget
        while widget and widget != self._content_widget:
            widget_type = type(widget).__name__
            
            # Verificar si es un tile (FileTile, FileStackTile, DesktopStackTile)
            if 'Tile' in widget_type:
                # Obtener ruta del archivo desde el tile
                if hasattr(widget, 'get_file_path'):
                    file_path = widget.get_file_path()
                    return widget, file_path
                elif hasattr(widget, '_file_stack') and widget._file_stack:
                    # Es un FileStackTile, usar el primer archivo del stack
                    if widget._file_stack.files:
                        return widget, widget._file_stack.files[0]
                elif hasattr(widget, '_file_path'):
                    return widget, widget._file_path
            
            widget = widget.parent()
        
        return None, None

    def set_selected_states(self, state) -> None:
        """Set state for all selected files and update badges."""
        set_selected_states(self, state)
    
    def _remove_tile_safely(self, tile: FileTile) -> None:
        """Safely remove a tile after exit animation completes."""
        remove_tile_safely(self, tile)
    
    def _animate_tile_exit(self, tile: FileTile, delay_ms: int = 0) -> None:
        """Animate tile exit with delay, then remove it."""
        animate_tile_exit(self, tile, delay_ms)
    
