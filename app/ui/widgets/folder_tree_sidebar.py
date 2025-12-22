"""
FolderTreeSidebar - Navigation history tree widget.

Displays hierarchical tree of opened Focus (tabs) as navigation history.
Only shows folders that have been opened as Focus.
"""

import os

from app.core.constants import SIDEBAR_MAX_WIDTH
from app.core.logger import get_logger

logger = get_logger(__name__)
from PySide6.QtCore import QModelIndex, QMimeData, QPoint, QSize, Qt, Signal, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QDragMoveEvent, QDropEvent, QMouseEvent, QStandardItem, QStandardItemModel, QPainter, QColor, QPen, QIcon, QBrush, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QMenu,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from app.ui.utils.font_manager import FontManager
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
    collect_children_paths,
    collect_expanded_paths,
    find_parent_item,
    get_root_folder_paths,
    remove_focus_path_from_model,
    _remove_item_recursive,
)
from app.ui.widgets.folder_tree_reorder_handler import (
    handle_reorder_drag_move,
    handle_reorder_drop,
    is_internal_reorder_drag,
)
from app.ui.widgets.folder_tree_styles import get_complete_stylesheet, get_menu_stylesheet, PANEL_BG
from app.ui.widgets.folder_tree_delegate import FolderTreeSectionDelegate
from app.ui.widgets.folder_tree_icon_utils import load_folder_icon_with_fallback, FOLDER_ICON_SIZE
from app.ui.widgets.folder_tree_menu_utils import calculate_menu_rect_viewport, create_option_from_index
from app.ui.widgets.folder_tree_widget_utils import find_tab_manager


class MinimalTreeView(QTreeView):
    """QTreeView sin líneas de conexión del árbol - mantiene flechas de expansión."""
    
    def drawBranches(self, painter, rect, index):
        # No dibujar líneas de conexión - esto es intencional y documentado
        # Las flechas de expansión se mantienen mediante setRootIsDecorated(True)
        pass


class FolderTreeSidebar(QWidget):
    """Navigation history tree showing opened Focus folders."""
    
    folder_selected = Signal(str)
    new_focus_requested = Signal(str)
    focus_remove_requested = Signal(str)
    files_moved = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FolderTreeSidebar")
        self.setMinimumWidth(180)
        self.setMaximumWidth(SIDEBAR_MAX_WIDTH)
        self._path_to_item: dict[str, QStandardItem] = {}
        self.setAcceptDrops(True)
        # Mismo patrón que DockBackgroundWidget para transparencia
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
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
        self._model = QStandardItemModel(self)
        self._model.setHorizontalHeaderLabels(["Folders"])
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Alineación: button_container con padding-left 10px para alinear con viewport del tree_container
        button_container = QWidget(self)
        button_container.setObjectName("ButtonContainer")
        button_container_layout = QHBoxLayout(button_container)
        button_container_layout.setContentsMargins(10, 0, 0, 0)
        button_container_layout.setSpacing(0)
        
        self._add_button = QPushButton(button_container)
        self._add_button.setObjectName("AddButton")
        self._add_button.setFixedHeight(36)
        self._add_button.setVisible(True)
        
        icon_loaded = False
        try:
            folder_icon = load_folder_icon_with_fallback(FOLDER_ICON_SIZE)
            if not folder_icon.isNull():
                self._add_button.setIcon(folder_icon)
                self._add_button.setIconSize(FOLDER_ICON_SIZE)
                icon_loaded = True
        except Exception as e:
            logger.warning(f"No se pudo cargar icono de carpeta para botón: {e}")
        
        if icon_loaded:
            self._add_button.setText("Nueva carpeta")
        else:
            self._add_button.setText("+")
        
        self._add_button.clicked.connect(self._on_add_clicked)
        
        button_container_layout.addWidget(self._add_button, 1)
        
        layout.addWidget(button_container, 0)  # Sin stretch - siempre arriba
        
        # Contenedor del árbol - estilo Finder: padding izquierdo mínimo
        # Finder usa padding izquierdo pequeño (alrededor de 10px) para alinear contenido
        tree_container = QWidget(self)
        tree_container.setObjectName("TreeContainer")
        tree_container_layout = QVBoxLayout(tree_container)
        tree_container_layout.setContentsMargins(10, 0, 0, 0)  # Padding izquierdo estilo Finder (reducido de 24px)
        tree_container_layout.setSpacing(0)
        
        # Tree view - usar subclase profesional que oculta líneas de conexión
        self._tree_view = MinimalTreeView(tree_container)
        self._tree_view.setModel(self._model)
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setAnimated(True)
        self._tree_view.setExpandsOnDoubleClick(False)
        self._tree_view.setRootIsDecorated(True)
        self._tree_view.setIndentation(12)
        self._tree_view.setUniformRowHeights(True)
        self._tree_view.setIconSize(FOLDER_ICON_SIZE)
        self._tree_view.setWordWrap(False)
        self._tree_view.setItemDelegate(FolderTreeSectionDelegate(self._tree_view))
        self._tree_view.setMouseTracking(True)
        
        self._tree_view.setAcceptDrops(True)
        self._tree_view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        
        self._tree_view.clicked.connect(self._on_tree_clicked)
        self._tree_view.doubleClicked.connect(self._on_tree_double_clicked)
        self._tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self._tree_view.viewport().installEventFilter(self)
        self._hovered_menu_index = None
        
        tree_container_layout.addWidget(self._tree_view, 1)
        layout.addWidget(tree_container, 1)  # Stretch factor to fill space
    
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
        if not self._pending_click_path:
            return
        
        normalized_path = os.path.normpath(self._pending_click_path)
        
        if normalized_path not in self._path_to_item:
            self._pending_click_path = None
            return
        
        item = self._path_to_item[normalized_path]
        if not item:
            self._pending_click_path = None
            return
        
        try:
            index = self._model.indexFromItem(item)
            if index.isValid():
                handle_tree_click(index, self._model, self._tree_view)
        except RuntimeError:
            pass
        
        self._pending_click_path = None
    
    def _on_add_clicked(self) -> None:
        folder_path = handle_add_button_click(self)
        if folder_path:
            self.new_focus_requested.emit(folder_path)
    
    def add_focus_path(self, path: str) -> None:
        normalized_path = os.path.normpath(path)
        
        if normalized_path in self._path_to_item:
            if self._reposition_node_if_needed(normalized_path):
                return
        
        item = add_focus_path_to_model(self._model, self._path_to_item, path)
        if not item:
            return
        
        self._expand_parent_if_needed(path)
    
    def _reposition_node_if_needed(self, normalized_path: str) -> bool:
        existing_item = self._path_to_item[normalized_path]
        current_parent = existing_item.parent() if existing_item.parent() else self._model.invisibleRootItem()
        correct_parent = find_parent_item(self._model, self._path_to_item, normalized_path)
        
        if current_parent == correct_parent:
            return False
        
        existing_index = self._model.indexFromItem(existing_item)
        was_expanded = existing_index.isValid() and self._tree_view.isExpanded(existing_index)
        children_paths = collect_children_paths(existing_item)
        
        remove_focus_path_from_model(self._model, self._path_to_item, normalized_path)
        
        item = add_focus_path_to_model(self._model, self._path_to_item, normalized_path)
        if not item:
            return True
        
        self._tree_view.setUpdatesEnabled(False)
        try:
            for child_path in children_paths:
                if child_path not in self._path_to_item:
                    add_focus_path_to_model(self._model, self._path_to_item, child_path)
        finally:
            self._tree_view.setUpdatesEnabled(True)
        
        if correct_parent != self._model.invisibleRootItem():
            parent_index = self._model.indexFromItem(correct_parent)
            if parent_index.isValid():
                self._tree_view.expand(parent_index)
        
        if was_expanded:
            new_index = self._model.indexFromItem(item)
            if new_index.isValid() and item.rowCount() > 0:
                self._tree_view.expand(new_index)
        
        return True
    
    def remove_focus_path(self, path: str) -> None:
        remove_focus_path_from_model(self._model, self._path_to_item, path)
    
    def update_focus_path(self, old_path: str, new_path: str) -> None:
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
        handle_drag_enter(event)
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
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
        return get_drop_target_path(event, self._tree_view, self._model)
    
    def _expand_parent_if_needed(self, path: str) -> None:
        parent_item = find_parent_item(self._model, self._path_to_item, os.path.normpath(path))
        if parent_item != self._model.invisibleRootItem():
            parent_index = self._model.indexFromItem(parent_item)
            if parent_index.isValid():
                self._tree_view.expand(parent_index)
    
    def _apply_styling(self) -> None:
        """Apply stylesheet and ensure fonts are properly initialized."""
        self.setStyleSheet(get_complete_stylesheet())
        
        if hasattr(self, '_add_button') and self._add_button:
            FontManager.safe_set_font(
                self._add_button,
                'Segoe UI',
                FontManager.SIZE_MEDIUM,
                QFont.Weight.Normal
            )
        
        if hasattr(self, '_tree_view') and self._tree_view:
            FontManager.safe_set_font(
                self._tree_view,
                'Segoe UI',
                FontManager.SIZE_MEDIUM,
                QFont.Weight.Normal
            )
    
    def paintEvent(self, event) -> None:
        # Mismo patrón que DockBackgroundWidget para transparencia
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg_color = QColor(PANEL_BG)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        rect = self.rect()
        separator_x = rect.right() - 1
        separator_color = QColor(255, 255, 255, 23)
        painter.setPen(QPen(separator_color, 1))
        painter.drawLine(separator_x, rect.top(), separator_x, rect.bottom())
        
        painter.end()
    
    def mousePressEvent(self, event) -> None:
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
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def get_focus_tree_paths(self) -> list[str]:
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
        root = self._model.invisibleRootItem()
        return collect_expanded_paths(self._model, self._path_to_item, self._tree_view, root)
    
    def get_current_state(self) -> tuple[list[str], list[str]]:
        paths = self.get_focus_tree_paths()
        expanded = self.get_expanded_paths()
        return (paths, expanded)
    
    def load_workspace_state(self, paths: list[str], expanded: list[str]) -> None:
        self.restore_tree(paths, expanded)
    
    def restore_tree(self, paths: list[str], expanded_paths: list[str]) -> None:
        # Bloquear señales del widget para evitar parpadeo visual
        self._tree_view.blockSignals(True)
        
        # Limpiar animaciones del delegate antes de restaurar
        delegate = self._tree_view.itemDelegate()
        if delegate and hasattr(delegate, 'clear_all_animations'):
            delegate.clear_all_animations()
        
        # Limpiar explícitamente la selección
        self._tree_view.clearSelection()
        
        # Resetear el selection model completamente
        selection_model = self._tree_view.selectionModel()
        if selection_model:
            selection_model.clearSelection()
            selection_model.clearCurrentIndex()
        
        # Resetear índice actual
        self._tree_view.setCurrentIndex(QModelIndex())
        
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
            try:
                if path in self._path_to_item:
                    item = self._path_to_item[path]
                    index = self._model.indexFromItem(item)
                    if index.isValid():
                        self._tree_view.expand(index)
            except Exception as e:
                logger.warning(f"Error expanding path {path}: {e}")
        
        # Desbloquear señales después de cargar contenido completo
        self._tree_view.blockSignals(False)
    
    def showEvent(self, event) -> None:
        super().showEvent(event)
        if hasattr(self, '_add_button'):
            self._add_button.setVisible(True)
            self._add_button.raise_()  # Traer al frente
            self._add_button.update()
    
    def eventFilter(self, obj, event) -> bool:
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
        if event.button() == Qt.MouseButton.LeftButton:
            self._reorder_drag_start_pos = None
            # Don't clear _dragged_index here, it's needed in dropEvent
    
    def _handle_menu_button_click(self, event: QMouseEvent) -> bool:
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
        menu = QMenu(self)
        menu.setStyleSheet(get_menu_stylesheet())
        remove_action = menu.addAction("Quitar del sidebar")
        remove_action.triggered.connect(
            lambda: self.focus_remove_requested.emit(folder_path)
        )
        menu.exec(global_pos)
    
    def closeEvent(self, event) -> None:
        if hasattr(self, '_click_expand_timer') and self._click_expand_timer.isActive():
            self._click_expand_timer.stop()
        super().closeEvent(event)