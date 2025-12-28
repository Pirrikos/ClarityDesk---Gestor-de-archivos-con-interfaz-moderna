"""
FolderTreeEventHandler - Manejo de eventos del sidebar.

Gestiona eventos de mouse, drag & drop, y clics en controles.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import QModelIndex, QPoint, Qt
from PySide6.QtGui import QMouseEvent, QStandardItemModel
from PySide6.QtWidgets import QMenu, QTreeView

from app.ui.widgets.folder_tree_styles import get_menu_stylesheet
from app.ui.widgets.folder_tree_handlers import resolve_folder_path
from app.ui.widgets.folder_tree_model import is_root_folder_item

if TYPE_CHECKING:
    from app.ui.widgets.folder_tree_sidebar import FolderTreeSidebar


class FolderTreeEventHandler:
    """Maneja eventos de mouse y drag & drop del sidebar."""
    
    def __init__(
        self,
        sidebar: "FolderTreeSidebar",
        tree_view: QTreeView,
        model: QStandardItemModel
    ):
        self._sidebar = sidebar
        self._tree_view = tree_view
        self._model = model
        
        self._chevron_click_index = None
        self._last_click_pos = None
        self._reorder_drag_start_pos = None
        self._dragged_index = None
    
    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        """
        Manejar mouse press en viewport.
        
        Retorna True si el evento fue completamente manejado (chevron).
        Retorna False para permitir que se propague y se emita la señal clicked.
        """
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        
        index = self._tree_view.indexAt(event.pos())
        if not index.isValid():
            return False
        
        visual_rect = self._tree_view.visualRect(index)
        item = self._model.itemFromIndex(index)
        
        self._last_click_pos = event.pos()
        
        if item and item.rowCount() > 0:
            chevron_rect = self._sidebar._get_chevron_rect(index, visual_rect)
            if chevron_rect.contains(event.pos()):
                self._chevron_click_index = index
                return True
        
        self._handle_reorder_drag_start(event)
        
        return False
    
    def handle_mouse_release(self, event: QMouseEvent) -> bool:
        """
        Manejar mouse release en viewport.
        
        Retorna True si el evento fue completamente manejado (chevron expand/collapse).
        Retorna False para permitir que se propague y se emita la señal clicked.
        """
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        
        if self._chevron_click_index is not None and self._chevron_click_index.isValid():
            index = self._chevron_click_index
            visual_rect = self._tree_view.visualRect(index)
            chevron_rect = self._sidebar._get_chevron_rect(index, visual_rect)
            
            press_pos = self._last_click_pos if self._last_click_pos else event.pos()
            release_in_chevron = chevron_rect.contains(event.pos())
            press_in_chevron = chevron_rect.contains(press_pos)
            
            if press_in_chevron:
                chevron_center = chevron_rect.center()
                distance = ((event.pos().x() - chevron_center.x()) ** 2 + 
                           (event.pos().y() - chevron_center.y()) ** 2) ** 0.5
                within_tolerance = distance <= 20
                
                if release_in_chevron or within_tolerance:
                    self._tree_view.blockSignals(True)
                    try:
                        is_currently_expanded = self._tree_view.isExpanded(index)
                        self._tree_view.setExpanded(index, not is_currently_expanded)
                        self._tree_view.viewport().update()
                    finally:
                        self._tree_view.blockSignals(False)
                    
                    self._chevron_click_index = None
                    self._last_click_pos = None
                    return True
                else:
                    self._chevron_click_index = None
            else:
                self._chevron_click_index = None
        
        self._handle_reorder_drag_end(event)
        
        return False
    
    def handle_mouse_move(self, event: QMouseEvent) -> None:
        """Manejar mouse move en viewport."""
        pass
    
    def handle_tree_click(self, index: QModelIndex) -> None:
        """Manejar click en item del árbol y emitir folder_selected signal."""
        if (self._chevron_click_index is not None and 
            self._chevron_click_index.isValid() and 
            self._chevron_click_index == index):
            return
        
        if self._last_click_pos is None:
            return
        
        visual_rect = self._tree_view.visualRect(index)
        
        item = self._model.itemFromIndex(index)
        if item and item.rowCount() > 0:
            chevron_rect = self._sidebar._get_chevron_rect(index, visual_rect)
            if chevron_rect.isValid() and chevron_rect.contains(self._last_click_pos):
                self._last_click_pos = None
                return
        
        separator_line_x = self._sidebar._get_separator_line_x(index, visual_rect)
        if separator_line_x is not None and self._last_click_pos.x() >= separator_line_x:
            self._last_click_pos = None
            return
        
        folder_path = resolve_folder_path(index, self._model)
        if folder_path:
            if hasattr(self._sidebar, '_state_manager') and self._sidebar._state_manager:
                self._sidebar._state_manager.clear_state_selection(from_user_action=True)
            self._sidebar.folder_selected.emit(folder_path)
        
        self._last_click_pos = None
    
    def _handle_reorder_drag_start(self, event: QMouseEvent) -> None:
        """Iniciar drag de reordenamiento."""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        
        index = self._tree_view.indexAt(event.pos())
        if not index.isValid():
            return
        
        item = self._model.itemFromIndex(index)
        if not item:
            return
        
        if is_root_folder_item(item, self._model):
            self._reorder_drag_start_pos = event.pos()
            self._dragged_index = index
    
    def _handle_reorder_drag_end(self, event: QMouseEvent) -> None:
        """Finalizar drag de reordenamiento."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._reorder_drag_start_pos = None
    
    def handle_context_menu(self, event: QMouseEvent) -> bool:
        """Manejar clic derecho para mostrar menú contextual en carpetas raíz."""
        index = self._tree_view.indexAt(event.pos())
        
        if not index.isValid() or index.parent().isValid():
            return False
        
        folder_path = resolve_folder_path(index, self._model)
        if folder_path:
            self._show_root_menu(folder_path, event.globalPos())
            return True
        
        return False
    
    def _show_root_menu(self, folder_path: str, global_pos: QPoint) -> None:
        """Mostrar menú contextual de carpeta raíz."""
        menu = QMenu(self._sidebar)
        menu.setStyleSheet(get_menu_stylesheet())
        remove_action = menu.addAction("Quitar del sidebar")
        remove_action.triggered.connect(
            lambda: self._sidebar.focus_remove_requested.emit(folder_path)
        )
        menu.exec(global_pos)

