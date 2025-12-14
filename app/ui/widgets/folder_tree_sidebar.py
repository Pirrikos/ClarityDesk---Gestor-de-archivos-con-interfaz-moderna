"""
FolderTreeSidebar - Navigation history tree widget.

Displays hierarchical tree of opened Focus (tabs) as navigation history.
Only shows folders that have been opened as Focus.
"""

import os

from app.core.constants import SIDEBAR_MAX_WIDTH
from PySide6.QtCore import QModelIndex, QMimeData, QPoint, QRect, QSize, Qt, Signal, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QDrag, QDragMoveEvent, QDropEvent, QMouseEvent, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMenu,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.folder_tree_drag_handler import (
    get_drop_target_path,
    handle_drag_enter,
    handle_drag_move,
    handle_drop,
)
from app.ui.widgets.folder_tree_handlers import (
    handle_add_button_click,
    handle_context_menu,
    handle_tree_click,
    resolve_folder_path,
)
from app.ui.widgets.folder_tree_model import (
    add_focus_path_to_model,
    find_parent_item,
    get_root_folder_paths,
    remove_focus_path_from_model,
)
from app.ui.widgets.folder_tree_reorder_handler import (
    handle_reorder_drag_move,
    handle_reorder_drop,
    is_internal_reorder_drag,
)
from app.ui.widgets.folder_tree_styles import get_complete_stylesheet, get_menu_stylesheet
from app.ui.widgets.folder_tree_delegate import FolderTreeSectionDelegate
from app.ui.widgets.folder_tree_menu_utils import calculate_menu_rect_viewport, create_option_from_index
from app.ui.widgets.folder_tree_widget_utils import find_tab_manager
from app.ui.widgets.folder_tree_model import collect_children_paths, collect_expanded_paths


class FolderTreeSidebar(QWidget):
    """Navigation history tree showing opened Focus folders."""
    
    folder_selected = Signal(str)  # Emitted when folder is clicked (folder path)
    new_focus_requested = Signal(str)  # Emitted when + button is clicked (folder path)
    focus_remove_requested = Signal(str)  # Emitted when remove is requested (folder path)
    files_moved = Signal(str, str)  # Emitted when files are moved (source_path, target_path)
    
    def __init__(self, parent=None):
        """
        Initialize FolderTreeSidebar.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setObjectName("FolderTreeSidebar")  # Para stylesheet
        self.setMinimumWidth(180)  # Ancho mínimo
        self.setMaximumWidth(SIDEBAR_MAX_WIDTH)
        self._path_to_item: dict[str, QStandardItem] = {}
        self.setAcceptDrops(True)  # Enable drop on widget
        self._setup_model()
        self._setup_ui()
        self._apply_styling()
        self._click_expand_timer = QTimer(self)
        self._click_expand_timer.setSingleShot(True)
        try:
            app = QApplication.instance()
            interval = app.doubleClickInterval() if app else 500
        except Exception:
            interval = 500
        self._click_expand_timer.setInterval(interval)
        self._click_expand_timer.timeout.connect(self._on_single_click_timeout)
        self._pending_click_path: str = None
        self._drag_start_position = None
        self._dragged_index = None
        self._reorder_drag_start_pos = None
    
    def _setup_model(self) -> None:
        """Setup QStandardItemModel for navigation history."""
        self._model = QStandardItemModel(self)
        self._model.setHorizontalHeaderLabels(["Folders"])
    
    def _setup_ui(self) -> None:
        """Build UI layout with QTreeView and + button."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add button at top
        self._add_button = QPushButton("+")
        self._add_button.setObjectName("AddButton")  # Para stylesheet
        self._add_button.setFixedHeight(52)  # Altura suficiente para texto 20px + padding 8px arriba/abajo
        self._add_button.setMinimumWidth(50)  # Ancho mínimo para que se vea
        self._add_button.setMaximumWidth(240)  # Respetar ancho del sidebar
        self._add_button.clicked.connect(self._on_add_clicked)
        layout.addWidget(self._add_button)
        
        # Spacer para alinear el primer elemento del árbol con el header de la tabla
        # FileViewContainer spacing (52px) + Toolbar (56px) + Header tabla (~30px) = ~138px
        # Botón "+" (52px) + spacer necesario (~86px) = ~138px
        layout.addSpacing(86)
        
        # Tree view
        self._tree_view = QTreeView(self)
        self._tree_view.setModel(self._model)
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setAnimated(True)  # Habilitar animaciones con easing personalizado
        self._tree_view.setExpandsOnDoubleClick(False)
        self._tree_view.setRootIsDecorated(False)  # Sin flechas expand/collapse
        self._tree_view.setIndentation(24)  # Arc-style (era 12)
        self._tree_view.setUniformRowHeights(True)  # Optimización
        self._tree_view.setIconSize(QSize(24, 24))
        self._tree_view.setWordWrap(False)  # Prevent text wrapping, use ellipsis
        # Delegate visual para dibujar bloque tipo tarjeta en la sección activa
        self._tree_view.setItemDelegate(FolderTreeSectionDelegate(self._tree_view))
        self._tree_view.setMouseTracking(True)
        
        # Enable drag & drop (internal for reordering, external for files)
        self._tree_view.setAcceptDrops(True)
        self._tree_view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        
        self._tree_view.clicked.connect(self._on_tree_clicked)
        self._tree_view.doubleClicked.connect(self._on_tree_double_clicked)
        # Deshabilitar menú contextual del botón derecho - ahora se usa el botón de tres puntitos
        self._tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        
        # Interceptar eventos de mouse para detectar clic en botón de menú
        self._tree_view.viewport().installEventFilter(self)
        self._hovered_menu_index = None
        
        layout.addWidget(self._tree_view, 1)  # Stretch factor to fill space
    
    def _on_tree_clicked(self, index: QModelIndex) -> None:
        if self._click_expand_timer.isActive():
            return
        folder_path = resolve_folder_path(index, self._model)
        if folder_path:
            self._pending_click_path = folder_path
            self._click_expand_timer.start()
    
    def _on_tree_double_clicked(self, index: QModelIndex) -> None:
        self._click_expand_timer.stop()
        self._pending_click_path = None
        folder_path = resolve_folder_path(index, self._model)
        if folder_path:
            self.folder_selected.emit(folder_path)
    
    def _on_single_click_timeout(self) -> None:
        if self._pending_click_path and self._pending_click_path in self._path_to_item:
            item = self._path_to_item[self._pending_click_path]
            index = self._model.indexFromItem(item)
            if index.isValid():
                handle_tree_click(index, self._model, self._tree_view)
        self._pending_click_path = None
    
    def _on_add_clicked(self) -> None:
        """Handle + button click - open folder picker."""
        folder_path = handle_add_button_click(self)
        if folder_path:
            self.new_focus_requested.emit(folder_path)
    
    def add_focus_path(self, path: str) -> None:
        """
        Add Focus path to navigation history tree.
        
        Inserts path under its parent ONLY if parent exists in tree.
        Otherwise inserts as root node.
        Recoloca el nodo si ya existe pero está en posición incorrecta.
        
        Args:
            path: Folder path to add.
        """
        normalized_path = os.path.normpath(path)
        
        # Si el path ya existe, verificar si necesita recolocación jerárquica
        if normalized_path in self._path_to_item:
            existing_item = self._path_to_item[normalized_path]
            current_parent = existing_item.parent() if existing_item.parent() else self._model.invisibleRootItem()
            
            # Buscar el padre correcto según la jerarquía de paths
            correct_parent = find_parent_item(self._model, self._path_to_item, normalized_path)
            
            # Si el padre actual no es el correcto, recolocar el nodo
            if current_parent != correct_parent:
                # Reubicamos el nodo al añadir un tab para mantener la jerarquía basada en paths.
                # Guardar estado expandido del nodo antes de eliminarlo
                existing_index = self._model.indexFromItem(existing_item)
                was_expanded = existing_index.isValid() and self._tree_view.isExpanded(existing_index)
                
                children_paths = collect_children_paths(existing_item)
                
                # Eliminar nodo antiguo del modelo (los hijos se eliminarán también del dict)
                remove_focus_path_from_model(self._model, self._path_to_item, normalized_path)
                
                # Recrear nodo bajo el padre correcto
                item = add_focus_path_to_model(self._model, self._path_to_item, normalized_path)
                
                if item:
                    # Deshabilitar actualizaciones durante la restauración de hijos para mayor velocidad
                    self._tree_view.setUpdatesEnabled(False)
                    try:
                        # Restaurar hijos recursivamente (se añadirán bajo sus padres correctos)
                        for child_path in children_paths:
                            if child_path not in self._path_to_item:
                                add_focus_path_to_model(self._model, self._path_to_item, child_path)
                    finally:
                        self._tree_view.setUpdatesEnabled(True)
                    
                    # Expandir padre para mostrar el nodo recolocado
                    if correct_parent != self._model.invisibleRootItem():
                        parent_index = self._model.indexFromItem(correct_parent)
                        if parent_index.isValid():
                            self._tree_view.expand(parent_index)
                    
                    # Restaurar estado expandido del nodo si estaba expandido (sin timer para mayor velocidad)
                    if was_expanded:
                        new_index = self._model.indexFromItem(item)
                        if new_index.isValid() and item.rowCount() > 0:
                            self._tree_view.expand(new_index)
                
                return
        
        # Path no existe o ya está en posición correcta, añadir normalmente
        item = add_focus_path_to_model(self._model, self._path_to_item, path)
        if not item:
            return
        
        self._expand_parent_if_needed(path)
    
    def remove_focus_path(self, path: str) -> None:
        """
        Remove Focus path from navigation history tree.
        
        Removes node and all its children (breadcrumb hierarchy).
        Does NOT delete folder from filesystem.
        
        Args:
            path: Folder path to remove.
        """
        remove_focus_path_from_model(self._model, self._path_to_item, path)
    
    def update_focus_path(self, old_path: str, new_path: str) -> None:
        """
        Update Focus path when folder is moved or renamed.
        
        Removes old path and adds new path ONLY if it corresponds to an existing tab.
        Does NOT create new tabs, only updates existing nodes in sidebar.
        
        Args:
            old_path: Old folder path.
            new_path: New folder path.
        """
        normalized_old = os.path.normpath(old_path)
        normalized_new = os.path.normpath(new_path)
        
        if normalized_old not in self._path_to_item:
            return
        
        if not os.path.isdir(normalized_new):
            return
        
        if normalized_old == normalized_new:
            return
        
        tab_manager = find_tab_manager(self)
        if tab_manager and hasattr(tab_manager, 'get_tabs'):
            tabs = tab_manager.get_tabs()
            # Normalizar tabs para comparación
            normalized_tabs = {os.path.normpath(tab) for tab in tabs}
            if normalized_new not in normalized_tabs:
                # El nuevo path no corresponde a un tab existente, solo remover el viejo
                remove_focus_path_from_model(self._model, self._path_to_item, normalized_old)
                return
        
        # Qt no permite mutar nodos activos; se recrea el item para mantener índices válidos.
        old_item = self._path_to_item[normalized_old]
        old_index = self._model.indexFromItem(old_item)
        was_expanded = old_index.isValid() and self._tree_view.isExpanded(old_index)
        
        # PASO 1: Eliminar TODAS las referencias internas primero (_path_to_item)
        # Esto incluye el item principal y todos sus hijos recursivamente
        from app.ui.widgets.folder_tree_model import _remove_item_recursive
        _remove_item_recursive(self._path_to_item, normalized_old)
        
        # PASO 2: Eliminar el item del modelo (ya no está en _path_to_item)
        parent = old_item.parent()
        if parent:
            parent.removeRow(old_item.row())
        else:
            root = self._model.invisibleRootItem()
            root.removeRow(old_item.row())
        
        # PASO 3: Verificar que el path viejo ya no existe antes de crear el nuevo
        if normalized_old in self._path_to_item:
            # Si todavía está, eliminarlo explícitamente (fallback de seguridad)
            del self._path_to_item[normalized_old]
        
        # PASO 4: Crear nuevo item con new_path (ahora es seguro, el viejo está completamente eliminado)
        new_item = add_focus_path_to_model(self._model, self._path_to_item, normalized_new)
        
        if not new_item:
            return
        
        self._expand_parent_if_needed(normalized_new)
        
        # Si estaba expandido y tiene hijos, expandir el nuevo nodo (sin timer para mayor velocidad)
        if was_expanded and new_item.rowCount() > 0:
            new_index = self._model.indexFromItem(new_item)
            if new_index.isValid():
                self._tree_view.expand(new_index)
    
    def dragEnterEvent(self, event) -> None:
        """Handle drag enter on tree view."""
        handle_drag_enter(event)
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move over tree view."""
        # Check if internal reorder drag
        if is_internal_reorder_drag(event, self._tree_view):
            if handle_reorder_drag_move(event, self._tree_view, self._model):
                event.accept()
            else:
                event.ignore()
        else:
            # External file drag
            handle_drag_move(event, self._tree_view, self._model)
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop on tree view - reorder root folders or move files."""
        # Check if internal reorder drag
        if is_internal_reorder_drag(event, self._tree_view):
            # Prevent Qt's automatic move by setting IgnoreAction BEFORE processing
            # This prevents Qt from moving items automatically
            event.setDropAction(Qt.DropAction.IgnoreAction)
            
            # Do our own reordering with validation
            if handle_reorder_drop(
                event, self._tree_view, self._model, self._path_to_item
            ):
                event.accept()
                self._dragged_index = None
            else:
                event.ignore()
                self._dragged_index = None
        else:
            # External file drag
            tab_manager = find_tab_manager(self)
            watcher = None
            if tab_manager and hasattr(tab_manager, 'get_watcher'):
                watcher = tab_manager.get_watcher()
            
            source_paths = handle_drop(event, self._tree_view, self._model, watcher=watcher)
            
            if source_paths:
                target_path = self._get_drop_target_path(event)
                if target_path:
                    for source_path in source_paths:
                        self.files_moved.emit(source_path, target_path)
                event.accept()
            else:
                event.ignore()
    
    def _get_drop_target_path(self, event) -> str:
        """Get target folder path from drop event."""
        return get_drop_target_path(event, self._tree_view, self._model)
    
    def _expand_parent_if_needed(self, path: str) -> None:
        """Expandir padre automáticamente para que el nodo sea visible."""
        parent_item = find_parent_item(self._model, self._path_to_item, os.path.normpath(path))
        if parent_item != self._model.invisibleRootItem():
            parent_index = self._model.indexFromItem(parent_item)
            if parent_index.isValid():
                self._tree_view.expand(parent_index)
    
    def _apply_styling(self) -> None:
        """Apply Arc Browser stylesheet to sidebar."""
        self.setStyleSheet(get_complete_stylesheet())
    
    def mousePressEvent(self, event) -> None:
        """Iniciar arrastre si el clic es en fondo/botón, no dentro del árbol."""
        if event.button() == Qt.MouseButton.LeftButton:
            child_widget = self.childAt(event.pos())
            # No iniciar arrastre si se pulsa dentro del QTreeView (para no romper DnD)
            if child_widget is not None:
                # Comparar contra el propio árbol o su viewport
                if child_widget == self._tree_view or child_widget == self._tree_view.viewport():
                    return
            self._drag_start_position = event.globalPos()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        """Mover la ventana principal mientras se arrastra."""
        if self._drag_start_position is not None:
            delta = event.globalPos() - self._drag_start_position
            main_window = self.window()
            if main_window:
                new_pos = main_window.pos() + delta
                main_window.move(new_pos)
                self._drag_start_position = event.globalPos()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """Finalizar arrastre al soltar el botón."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def get_focus_tree_paths(self) -> list[str]:
        """
        Get all paths currently in the focus tree, preserving root folder order.
        
        Returns root folders first (in their current order), then children recursively.
        
        Returns:
            List of folder paths in the tree, with root folders first.
        """
        paths = []
        root_paths = get_root_folder_paths(self._model, self._path_to_item)
        
        # Add root folders first (in order)
        paths.extend(root_paths)
        
        # Then add children recursively
        def add_children_recursive(parent_path: str) -> None:
            if parent_path not in self._path_to_item:
                return
            
            parent_item = self._path_to_item[parent_path]
            for i in range(parent_item.rowCount()):
                child = parent_item.child(i)
                if child:
                    child_path = child.data(Qt.ItemDataRole.UserRole)
                    if child_path and child_path not in paths:
                        paths.append(child_path)
                        add_children_recursive(child_path)
        
        # Add children of each root folder
        for root_path in root_paths:
            add_children_recursive(root_path)
        
        return paths
    
    def get_expanded_paths(self) -> list[str]:
        """
        Get all currently expanded node paths.
        
        Returns:
            List of expanded folder paths.
        """
        root = self._model.invisibleRootItem()
        return collect_expanded_paths(self._model, self._path_to_item, self._tree_view, root)
    
    def restore_tree(self, paths: list[str], expanded_paths: list[str]) -> None:
        """
        Restore tree state from saved paths and expanded nodes.
        
        Respects the order of root folders in the paths list.
        Root folders are added first in the specified order, then children.
        
        Args:
            paths: List of folder paths to add to tree (root folders first, then children).
            expanded_paths: List of paths that should be expanded.
        """
        # Clear current tree
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["Folders"])
        self._path_to_item.clear()
        
        # Separate root folders from children
        root = self._model.invisibleRootItem()
        root_paths = []
        child_paths = []
        
        for path in paths:
            normalized = os.path.normpath(path)
            # Check if path would be a root folder (no parent in paths list)
            parent_path = os.path.dirname(normalized)
            normalized_parent = os.path.normpath(parent_path) if parent_path else None
            
            # If parent is not in paths list, it's a root folder
            if not normalized_parent or normalized_parent not in paths:
                root_paths.append(path)
            else:
                child_paths.append(path)
        
        # Add root folders first (preserving order)
        for path in root_paths:
            self.add_focus_path(path)
        
        # Then add children (they will be placed under their parents)
        for path in child_paths:
            self.add_focus_path(path)
        
        # Expand specified nodes
        expanded_set = set(expanded_paths)
        for path in expanded_set:
            if path in self._path_to_item:
                item = self._path_to_item[path]
                index = self._model.indexFromItem(item)
                if index.isValid():
                    self._tree_view.expand(index)
    
    def showEvent(self, event) -> None:
        """Asegurar que el botón sea visible cuando se muestra el widget."""
        super().showEvent(event)
        if hasattr(self, '_add_button'):
            self._add_button.setVisible(True)
            self._add_button.raise_()  # Traer al frente
            self._add_button.update()
    
    def eventFilter(self, obj, event) -> bool:
        """Interceptar eventos de mouse para detectar clic en botón de menú y drag de carpetas raíz."""
        if obj == self._tree_view.viewport():
            if event.type() == QMouseEvent.Type.MouseButtonPress:
                handled = self._handle_menu_button_click(event)
                if not handled:
                    self._handle_reorder_drag_start(event)
                return handled
            elif event.type() == QMouseEvent.Type.MouseMove:
                self._handle_menu_button_hover(event)
                self._handle_reorder_drag_move(event)
            elif event.type() == QMouseEvent.Type.MouseButtonRelease:
                self._handle_reorder_drag_end(event)
        return super().eventFilter(obj, event)
    
    def _handle_reorder_drag_start(self, event: QMouseEvent) -> None:
        """Handle mouse press for potential reorder drag."""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        
        index = self._tree_view.indexAt(event.pos())
        if not index.isValid():
            return
        
        item = self._model.itemFromIndex(index)
        if not item:
            return
        
        # Only allow drag for root folders
        from app.ui.widgets.folder_tree_model import is_root_folder_item
        if is_root_folder_item(item, self._model):
            self._reorder_drag_start_pos = event.pos()
            self._dragged_index = index
    
    def _handle_reorder_drag_move(self, event: QMouseEvent) -> None:
        """Handle mouse move to detect drag start."""
        if self._reorder_drag_start_pos is None:
            return
        
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            self._reorder_drag_start_pos = None
            self._dragged_index = None
            return
        
        # Check if moved enough to start drag
        delta = (event.pos() - self._reorder_drag_start_pos).manhattanLength()
        if delta > QApplication.startDragDistance():
            # Drag started, Qt will handle it via InternalMove
            pass
    
    def _handle_reorder_drag_end(self, event: QMouseEvent) -> None:
        """Handle mouse release after drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._reorder_drag_start_pos = None
            # Don't clear _dragged_index here, it's needed in dropEvent
    
    def _handle_menu_button_click(self, event: QMouseEvent) -> bool:
        """Manejar clic en botón de menú (tres puntitos)."""
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
            event.accept()
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
        """Mostrar menú para carpeta raíz."""
        menu = QMenu(self)
        menu.setStyleSheet(get_menu_stylesheet())
        remove_action = menu.addAction("Quitar del sidebar")
        remove_action.triggered.connect(
            lambda: self.focus_remove_requested.emit(folder_path)
        )
        menu.exec(global_pos)
    
    def closeEvent(self, event) -> None:
        """Cleanup timers before closing."""
        if hasattr(self, '_click_expand_timer') and self._click_expand_timer.isActive():
            self._click_expand_timer.stop()
        super().closeEvent(event)