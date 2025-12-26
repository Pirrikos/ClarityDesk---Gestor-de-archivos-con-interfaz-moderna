"""
FolderTreeEventHandler - Manejo de eventos del sidebar.

Gestiona eventos de mouse, drag & drop, y clics en controles.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import QModelIndex, QPoint, QRect, Qt
from PySide6.QtGui import QMouseEvent, QStandardItemModel
from PySide6.QtWidgets import QApplication, QMenu, QTreeView

from app.ui.widgets.folder_tree_menu_utils import calculate_menu_rect_viewport, create_option_from_index
from app.ui.widgets.folder_tree_widget_utils import find_tab_manager
from app.ui.widgets.folder_tree_styles import get_menu_stylesheet
from app.ui.widgets.folder_tree_handlers import resolve_folder_path

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
        self._hovered_menu_index = None
        self._reorder_drag_start_pos = None
        self._dragged_index = None
    
    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        """
        Manejar mouse press en viewport.
        
        Retorna True si el evento fue completamente manejado (chevron, menu button).
        Retorna False para permitir que se propague y se emita la señal clicked.
        """
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        
        index = self._tree_view.indexAt(event.pos())
        if not index.isValid():
            return False
        
        visual_rect = self._tree_view.visualRect(index)
        item = self._model.itemFromIndex(index)
        
        # Guardar posición de click para usar en handle_tree_click
        self._last_click_pos = event.pos()
        
        # Verificar si es click en chevron (consumir evento)
        if item and item.rowCount() > 0:
            chevron_rect = self._sidebar._get_chevron_rect(index, visual_rect)
            if chevron_rect.contains(event.pos()):
                self._chevron_click_index = index
                return True  # Consumir evento - no propagar
        
        # Verificar si es click en área de controles (menu button o reorder)
        separator_line_x = self._sidebar._get_separator_line_x(index, visual_rect)
        if separator_line_x is not None and event.pos().x() >= separator_line_x:
            handled = self._handle_menu_button_click(event)
            if handled:
                return True  # Consumir evento - menu button manejado
            # Si no es menu button, iniciar drag de reordenamiento (pero NO consumir evento)
            self._handle_reorder_drag_start(event)
            return False  # NO consumir - permitir que se emita clicked
        
        # Verificar menu button fuera del área de controles (solo root items)
        handled = self._handle_menu_button_click(event)
        if handled:
            return True  # Consumir evento - menu button manejado
        
        # Iniciar drag de reordenamiento si es root item (pero NO consumir evento)
        self._handle_reorder_drag_start(event)
        
        # NO consumir evento - permitir que se propague y se emita clicked signal
        return False
    
    def handle_mouse_release(self, event: QMouseEvent) -> bool:
        """
        Manejar mouse release en viewport.
        
        Retorna True si el evento fue completamente manejado (chevron expand/collapse).
        Retorna False para permitir que se propague y se emita la señal clicked.
        """
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        
        # Manejar release de chevron si estaba presionado
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
                    return True  # Consumir evento - chevron manejado
                else:
                    self._chevron_click_index = None
                    # NO limpiar _last_click_pos aquí - permitir navegación normal
            else:
                self._chevron_click_index = None
                # NO limpiar _last_click_pos aquí - permitir navegación normal
        
        # Finalizar drag de reordenamiento si estaba activo
        self._handle_reorder_drag_end(event)
        
        # NO consumir evento - permitir que se propague y se emita clicked signal
        return False
    
    def handle_mouse_move(self, event: QMouseEvent) -> None:
        """Manejar mouse move en viewport."""
        self._handle_menu_button_hover(event)
        self._handle_reorder_drag_move(event)
    
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
            # Limpiar selección de estado desde acción del usuario (no activar guard)
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
        
        from app.ui.widgets.folder_tree_model import is_root_folder_item
        if is_root_folder_item(item, self._model):
            self._reorder_drag_start_pos = event.pos()
            self._dragged_index = index
    
    def _handle_reorder_drag_move(self, event: QMouseEvent) -> None:
        """Manejar movimiento durante drag de reordenamiento."""
        if self._reorder_drag_start_pos is None:
            return
        
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            self._reorder_drag_start_pos = None
            self._dragged_index = None
            return
        
        delta = (event.pos() - self._reorder_drag_start_pos).manhattanLength()
        if delta > QApplication.startDragDistance():
            return
    
    def _handle_reorder_drag_end(self, event: QMouseEvent) -> None:
        """Finalizar drag de reordenamiento."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._reorder_drag_start_pos = None
    
    def _handle_menu_button_click(self, event: QMouseEvent) -> bool:
        """Manejar click en botón de menú (tres puntitos)."""
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        
        index = self._tree_view.indexAt(event.pos())
        if not index.isValid() or index.parent().isValid():
            return False
        
        delegate = self._tree_view.itemDelegate()
        if not delegate or not hasattr(delegate, '_get_menu_button_rect'):
            return False
        
        option, visual_rect = create_option_from_index(self._tree_view, index)
        if not option or not visual_rect:
            return False
        
        menu_rect = delegate._get_menu_button_rect(option, index)
        if not menu_rect.isValid():
            return False
        
        menu_rect_viewport = calculate_menu_rect_viewport(menu_rect, visual_rect)
        
        if menu_rect_viewport.contains(event.pos()):
            folder_path = resolve_folder_path(index, self._model)
            if folder_path:
                self._show_root_menu(folder_path, event.globalPos())
            return True
        
        return False
    
    def _handle_menu_button_hover(self, event: QMouseEvent) -> None:
        """Manejar hover sobre botón de menú."""
        index = self._tree_view.indexAt(event.pos())
        delegate = self._tree_view.itemDelegate()
        
        if index.isValid() and not index.parent().isValid() and delegate and hasattr(delegate, '_get_menu_button_rect'):
            option, visual_rect = create_option_from_index(self._tree_view, index)
            if not option or not visual_rect:
                if self._hovered_menu_index:
                    self._hovered_menu_index = None
                    self._tree_view.viewport().update()
                return
            
            menu_rect = delegate._get_menu_button_rect(option, index)
            if menu_rect.isValid():
                menu_rect_viewport = calculate_menu_rect_viewport(menu_rect, visual_rect)
                
                if menu_rect_viewport.contains(event.pos()):
                    if self._hovered_menu_index != index:
                        self._hovered_menu_index = index
                        self._tree_view.viewport().update()
                else:
                    if self._hovered_menu_index == index:
                        self._hovered_menu_index = None
                        self._tree_view.viewport().update()
            else:
                if self._hovered_menu_index == index:
                    self._hovered_menu_index = None
                    self._tree_view.viewport().update()
        else:
            if self._hovered_menu_index:
                self._hovered_menu_index = None
                self._tree_view.viewport().update()
    
    def _show_root_menu(self, folder_path: str, global_pos: QPoint) -> None:
        """Mostrar menú contextual de carpeta raíz."""
        menu = QMenu(self._sidebar)
        menu.setStyleSheet(get_menu_stylesheet())
        remove_action = menu.addAction("Quitar del sidebar")
        remove_action.triggered.connect(
            lambda: self._sidebar.focus_remove_requested.emit(folder_path)
        )
        menu.exec(global_pos)
    
    @property
    def hovered_menu_index(self):
        """Índice del menú con hover."""
        return self._hovered_menu_index

