"""
FileListView - List/table view for displaying files.

Shows files in a table with filename, extension, and modified date.
Emits signal on double-click to open file.
"""

from typing import Optional

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtGui import QContextMenuEvent, QMouseEvent
from PySide6.QtWidgets import QCheckBox, QTableWidget, QTableWidgetItem

try:
    from app.managers.file_state_manager import FileStateManager
except ImportError:
    FileStateManager = None

from app.managers.tab_manager import TabManager
from app.services.icon_service import IconService
from app.ui.widgets.file_list_handlers import (
    start_drag, drag_enter_event, drag_move_event, drop_event,
    mouse_press_event, on_item_double_clicked, on_checkbox_changed
)
from app.ui.widgets.file_list_renderer import (
    setup_ui, expand_stacks_to_files, refresh_table
)
from app.ui.widgets.file_view_context_menu import show_background_menu, show_item_menu
from app.ui.widgets.file_view_utils import create_refresh_callback


class FileListView(QTableWidget):
    """Table view widget displaying files as a list."""

    open_file = Signal(str)  # Emitted on double-click (file path)
    file_dropped = Signal(str)  # Emitted when file is dropped (source file path)
    file_deleted = Signal(str)  # Emitted when file is deleted (file path)
    folder_moved = Signal(str, str)  # Emitted when folder is moved (old_path, new_path)

    def __init__(
        self,
        icon_service: Optional[IconService] = None,
        parent=None,
        tab_manager: Optional[TabManager] = None,
        state_manager=None
    ):
        """Initialize FileListView with empty file list."""
        super().__init__(parent)
        self._files: list[str] = []
        self._icon_service = icon_service or IconService()
        self._tab_manager = tab_manager
        self._checked_paths: set[str] = set()
        self._state_manager = state_manager or (FileStateManager() if FileStateManager else None)
        self._header_checkbox: Optional[QCheckBox] = None
        self._hovered_row: int = -1  # Fila bajo el mouse para efecto hover tipo Finder
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        setup_ui(self, self._on_checkbox_changed, self._on_item_double_clicked)

    def update_files(self, file_list: list) -> None:
        """
        Update displayed files or stacks.
        
        Args:
            file_list: List of file paths OR FileStack objects.
                      Stacks are automatically expanded to show individual files.
        """
        self._files = expand_stacks_to_files(file_list)
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Rebuild table rows from file list."""
        refresh_table(
            self, self._files, self._icon_service,
            self._state_manager, self._checked_paths, self._on_checkbox_changed
        )

    def startDrag(self, supported_actions) -> None:
        """Handle drag start for file copy or move using checkbox selection."""
        start_drag(self, self._icon_service, self.file_deleted)

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter for file drop."""
        drag_enter_event(self, event, self._tab_manager)

    def dragMoveEvent(self, event) -> None:
        """Handle drag move to maintain drop acceptance."""
        drag_move_event(self, event, self._tab_manager)

    def dropEvent(self, event) -> None:
        """Handle file drop into list view."""
        drop_event(self, event, self._tab_manager, self.file_dropped)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press - toggle checkbox with Ctrl+click."""
        mouse_press_event(self, event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move - update hovered row for Finder-like hover effect."""
        super().mouseMoveEvent(event)
        item = self.itemAt(event.pos())
        new_hovered_row = item.row() if item else -1
        
        # Si el mouse está fuera de cualquier item, limpiar hover
        if new_hovered_row < 0:
            if self._hovered_row >= 0:
                old_row = self._hovered_row
                self._hovered_row = -1
                self._update_row_visual(old_row)
            return
        
        # Actualizar solo si cambió la fila en hover
        if new_hovered_row != self._hovered_row:
            old_row = self._hovered_row
            self._hovered_row = new_hovered_row
            
            # Actualizar visualización de ambas filas
            if old_row >= 0:
                self._update_row_visual(old_row)
            if new_hovered_row >= 0:
                self._update_row_visual(new_hovered_row)
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave - clear hover effect."""
        if self._hovered_row >= 0:
            old_row = self._hovered_row
            self._hovered_row = -1
            self._update_row_visual(old_row)
        super().leaveEvent(event)
    
    def _update_row_visual(self, row: int) -> None:
        """Actualizar visualización de una fila completa."""
        if row < 0 or row >= self.rowCount():
            return
        # Actualizar toda la fila usando visualRect
        index = self.model().index(row, 0)
        if index.isValid():
            rect = self.visualRect(index)
            # Expandir rectángulo para cubrir todas las columnas
            if self.columnCount() > 0:
                last_index = self.model().index(row, self.columnCount() - 1)
                if last_index.isValid():
                    last_rect = self.visualRect(last_index)
                    rect.setRight(last_rect.right())
            self.update(rect)

    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click on table row."""
        on_item_double_clicked(self, item, self.open_file)

    def _on_checkbox_changed(self, file_path: str, state: int) -> None:
        """Handle checkbox state change to update selection set."""
        on_checkbox_changed(self, file_path, state)
        self._update_header_checkbox_state()
    
    def _update_header_checkbox_state(self) -> None:
        """Update header checkbox state based on individual checkboxes."""
        if not self._header_checkbox or not self._files:
            return
        
        total_files = len(self._files)
        checked_count = len(self._checked_paths)
        
        # Bloquear señal para evitar recursión
        self._header_checkbox.blockSignals(True)
        
        if checked_count == 0:
            self._header_checkbox.setCheckState(Qt.CheckState.Unchecked)
        elif checked_count == total_files:
            self._header_checkbox.setCheckState(Qt.CheckState.Checked)
        else:
            # Estado indeterminado cuando algunos están marcados
            self._header_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
        
        self._header_checkbox.blockSignals(False)
    
    def select_all_files(self) -> None:
        """Select all files by checking all checkboxes."""
        if not self._files:
            return
        self._update_all_checkboxes(checked=True)
        if self._header_checkbox:
            self._header_checkbox.setCheckState(Qt.CheckState.Checked)
    
    def deselect_all_files(self) -> None:
        """Deselect all files by unchecking all checkboxes."""
        if not self._files:
            return
        self._update_all_checkboxes(checked=False)
        if self._header_checkbox:
            self._header_checkbox.setCheckState(Qt.CheckState.Unchecked)
    
    def _update_all_checkboxes(self, checked: bool) -> None:
        """Update all checkboxes state and selection set."""
        if self._header_checkbox:
            self._header_checkbox.blockSignals(True)
        
        for file_path in self._files:
            if checked:
                self._checked_paths.add(file_path)
            else:
                self._checked_paths.discard(file_path)
            
            checkbox = self._get_checkbox_from_row(self.row_from_path(file_path))
            if checkbox:
                checkbox.setChecked(checked)
        
        if self._header_checkbox:
            self._header_checkbox.blockSignals(False)
    
    def _get_checkbox_from_row(self, row: int) -> Optional[QCheckBox]:
        """Get checkbox widget from row's column 0."""
        from app.ui.widgets.file_list_handlers import get_checkbox_from_row
        return get_checkbox_from_row(self, row)
    
    def row_from_path(self, file_path: str) -> int:
        """Get row index for a given file path."""
        for row in range(self.rowCount()):
            item = self.item(row, 1)
            if item and item.data(Qt.ItemDataRole.UserRole) == file_path:
                return row
        return -1

    def get_selected_paths(self) -> list[str]:
        """Get paths of currently selected files via checkboxes or traditional selection."""
        if self._checked_paths:
            return list(self._checked_paths)
        selected_paths = []
        for item in self.selectedItems():
            if item:
                path = item.data(Qt.ItemDataRole.UserRole)
                if path:
                    selected_paths.append(path)
        if selected_paths:
            return selected_paths
        # Fallback: usar currentItem cuando selectedItems() está vacío (problema de foco)
        current_row = self.currentRow()
        if current_row >= 0:
            current_item = self.item(current_row, 1)
            if current_item:
                path = current_item.data(Qt.ItemDataRole.UserRole)
                if path:
                    return [path]
        return []

    def set_selected_states(self, state) -> None:
        """
        Set state for all selected files and update display.
        
        Args:
            state: State constant or None to remove state.
        """
        if not self._state_manager:
            return
        
        selected_paths = self.get_selected_paths()
        if not selected_paths:
            return
        
        self._state_manager.set_files_state(selected_paths, state)
        self._refresh_table()
    
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Show context menu - background menu or item menu depending on click location."""
        refresh_callback = create_refresh_callback(self)
        
        # Detectar si el clic es sobre un item o sobre el fondo
        item_path = self._get_clicked_item_path(event.pos())
        
        if item_path:
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
    
    def _get_clicked_item_path(self, pos) -> Optional[str]:
        """
        Detectar si el clic es sobre un item o sobre el fondo.
        
        Args:
            pos: Posición del clic en coordenadas del widget.
            
        Returns:
            Ruta del archivo si el clic es sobre un item, None si es fondo.
        """
        # itemAt retorna el QTableWidgetItem en esa posición, o None si es fondo
        item = self.itemAt(pos)
        
        if not item:
            return None
        
        # Obtener ruta del archivo desde el item (columna 1 contiene el nombre con la ruta)
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            return path
        
        # Si no hay UserRole, intentar obtener desde la fila completa
        row = item.row()
        if row >= 0:
            name_item = self.item(row, 1)  # Columna 1 contiene el nombre
            if name_item:
                path = name_item.data(Qt.ItemDataRole.UserRole)
                return path if path else None
        
        return None