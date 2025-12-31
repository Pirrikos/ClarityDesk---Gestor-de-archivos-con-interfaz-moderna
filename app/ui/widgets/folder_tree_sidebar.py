"""
FolderTreeSidebar - Navigation history tree widget.

Displays hierarchical tree of opened Focus (tabs) as navigation history.
Only shows folders that have been opened as Focus.
"""

import os
from typing import Optional

from app.core.constants import SIDEBAR_MAX_WIDTH, DEBUG_LAYOUT
from app.core.logger import get_logger
from app.services.path_utils import normalize_path
from app.services.desktop_path_helper import is_system_desktop

logger = get_logger(__name__)
logger.debug("🚀 Loading folder_tree_sidebar.py")
from PySide6.QtCore import QModelIndex, QPoint, QRect, QSize, Qt, Signal, QTimer, QElapsedTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QDragMoveEvent, QDropEvent, QMouseEvent, QStandardItem, QPainter, QColor, QFont, QFontMetrics, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QMenu,
    QSplitter,
    QStyle,
    QStyleOptionViewItem,
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
    resolve_folder_path,
)
from app.ui.widgets.folder_tree_model import (
    FolderTreeModel,
    add_focus_path_to_model,
    collect_children_paths,
    collect_expanded_paths,
    find_parent_item,
    get_root_folder_paths,
    remove_focus_path_from_model,
    _remove_item_recursive,
    _get_original_path,
)
from app.ui.widgets.folder_tree_reorder_handler import (
    handle_reorder_drag_move,
    handle_reorder_drop,
    is_internal_reorder_drag,
)
from app.ui.widgets.folder_tree_styles import get_complete_stylesheet, SEPARATOR_VERTICAL_COLOR_RGBA, FONT_FAMILY, TEXT_PRIMARY
from app.core.constants import SIDEBAR_BG, ROUNDED_BG_TOP_OFFSET
from app.ui.widgets.folder_tree_delegate import FolderTreeSectionDelegate
from app.ui.utils.rounded_background_painter import paint_rounded_background
from app.ui.widgets.folder_tree_icon_utils import FOLDER_ICON_SIZE
from app.ui.widgets.folder_tree_widget_utils import find_tab_manager
from app.ui.widgets.folder_tree_constants import CONTROLS_AREA_TOTAL_OFFSET, CONTAINER_PADDING_LEFT
from app.ui.widgets.folder_tree_state_manager import FolderTreeStateManager
from app.ui.widgets.folder_tree_event_handler import FolderTreeEventHandler
from app.ui.widgets.state_section_widget import StateSectionWidget


class MinimalTreeView(QTreeView):
    """QTreeView sin líneas de conexión del árbol - mantiene flechas de expansión."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_resizing = False
    
    def drawBranches(self, painter, rect, index):
        # No dibujar nada - el chevron se dibuja en el delegate al lado derecho
        pass
    
    def _set_resizing_state(self, is_resizing: bool) -> None:
        self._is_resizing = is_resizing
    
    def is_resizing(self) -> bool:
        return self._is_resizing


class FolderTreeSidebar(QWidget):
    """Navigation history tree showing opened Focus folders."""
    
    folder_selected = Signal(str)
    focus_remove_requested = Signal(str)
    files_moved = Signal(str, str)
    state_selected = Signal(str)  # Emitido cuando se selecciona un estado
    
    def __init__(self, parent=None, state_label_manager=None, tab_manager=None):
        """
        Inicializar sidebar con sección ESTADOS.
        
        Args:
            parent: Widget padre.
            state_label_manager: StateLabelManager para obtener orden y labels de estados.
            tab_manager: TabManager para activar contexto de estado.
        """
        super().__init__(parent)
        self.setObjectName("FolderTreeSidebar")
        self.setMinimumWidth(250)
        self.setMaximumWidth(SIDEBAR_MAX_WIDTH)
        self._path_to_item: dict[str, QStandardItem] = {}
        self._state_label_manager = state_label_manager
        self._tab_manager = tab_manager
        
        # OPACIDAD ESTRUCTURAL: Usar paleta y AutoFillBackground
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(SIDEBAR_BG))
        self.setPalette(palette)
        
        self.setAcceptDrops(True)
        self._setup_model()
        self._setup_ui()
        self._apply_styling()
        
        self._click_expand_timer = QTimer(self)
        self._click_expand_timer.setSingleShot(True)
        self._click_expand_timer.setInterval(500)
        self._click_expand_timer.timeout.connect(self._on_single_click_timeout)
        
        self._drag_start_position = None
        
        self._is_resizing = False
        self._resize_debounce_timer = QTimer(self)
        self._resize_debounce_timer.setSingleShot(True)
        self._resize_debounce_timer.timeout.connect(self._on_resize_finished)
        
        self._state_manager = None
        # _event_handler se inicializa en _setup_ui() línea 270 - NO sobrescribir aquí
        
        self._connect_splitter_signals()
        
        # Inicializar state_manager después de _setup_ui() para tener acceso a _state_section y _tree_view
        state_section = getattr(self, '_state_section', None)
        if hasattr(self, '_tree_view'):
            self._state_manager = FolderTreeStateManager(
                self._tree_view,
                state_section,
                self._tab_manager
            )
    
    def _setup_model(self) -> None:
        # Usar modelo personalizado que previene cambios de jerarquía internos
        self._model = FolderTreeModel(self)
        self._model.setHorizontalHeaderLabels(["Folders"])
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        # Sin padding superior para alineación perfecta con FileViewContainer
        layout.setContentsMargins(0, ROUNDED_BG_TOP_OFFSET, 0, 0)
        layout.setSpacing(0)
        
        # Padding superior para la sección ESTADOS
        layout.addSpacing(8)
        
        # Sección ESTADOS en la parte superior (siempre visible)
        if self._state_label_manager and self._tab_manager:
            self._state_section = StateSectionWidget(
                self._state_label_manager,
                self._tab_manager,
                self
            )
            # Conectar señal de cambio de estado activo
            self._state_section.state_selected.connect(self._on_state_selected)
            # Re-emitir señal para que MainWindow pueda cancelar búsqueda
            self._state_section.state_selected.connect(self.state_selected.emit)
            # Conectar cambios de contexto de estado desde TabManager
            if hasattr(self._tab_manager, 'activeTabChanged'):
                self._tab_manager.activeTabChanged.connect(self._on_tab_changed)
            layout.addWidget(self._state_section, 0)
            
            # Espacio superior antes de la línea separadora
            layout.addSpacing(12)
            
            # Línea separadora sutil entre estados y carpetas (mismo estilo que líneas verticales)
            separator_widget = QWidget(self)
            separator_widget.setFixedHeight(1)
            separator_widget.setObjectName("StatesSeparator")
            # Usar el mismo color que las líneas separadoras verticales pero más sutil
            # Agregar márgenes laterales para que no ocupe todo el ancho
            separator_widget.setStyleSheet(f"""
                QWidget#StatesSeparator {{
                    background-color: rgba{SEPARATOR_VERTICAL_COLOR_RGBA};
                    margin-left: 10px;
                    margin-right: 10px;
                }}
            """)
            layout.addWidget(separator_widget, 0)
            
            # Espacio inferior después de la línea separadora
            layout.addSpacing(8)
        
        tree_container = QWidget(self)
        tree_container.setObjectName("TreeContainer")
        tree_container_layout = QVBoxLayout(tree_container)
        tree_container_layout.setContentsMargins(0, 0, 0, 0)
        tree_container_layout.setSpacing(0)
        
        # Título "ACCESOS DIRECTOS" (igual que ESTADOS pero sin chevron)
        title_widget = QWidget(self)
        title_widget.setFixedHeight(30)  # Misma altura que TITLE_HEIGHT
        title_widget.setObjectName("AccessosDirectosTitle")
        title_widget.setStyleSheet("""
            QWidget#AccessosDirectosTitle {
                background-color: transparent;
            }
        """)
        
        def paint_title(event):
            painter = QPainter(title_widget)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            rect = title_widget.rect()
            y = 0
            
            # Fuente igual que las carpetas del sidebar
            font = QFont()
            font_family_list = FONT_FAMILY.replace('"', '').split(',')
            font.setFamily(font_family_list[0].strip() if font_family_list else "Segoe UI")
            font.setPixelSize(11)  # Tamaño 11px
            font.setWeight(QFont.Weight.Medium)
            painter.setFont(font)
            
            font_metrics = QFontMetrics(font)
            
            # Calcular posición de la línea separadora (igual que ESTADOS)
            viewport_width = rect.width()
            separator_x = viewport_width - CONTROLS_AREA_TOTAL_OFFSET
            
            # Dibujar texto "ACCESOS DIRECTOS" (sin línea separadora vertical)
            text_color = QColor("#666666")  # Gris oscuro
            painter.setPen(QPen(text_color))
            text_x = CONTAINER_PADDING_LEFT
            text_y = y + (30 + font_metrics.ascent()) // 2  # TITLE_HEIGHT = 30
            painter.drawText(text_x, text_y, "ACCESOS DIRECTOS")
            
            painter.end()
        
        title_widget.paintEvent = paint_title
        tree_container_layout.addWidget(title_widget, 0)
        
        # Tree view container con padding
        tree_view_container = QWidget(self)
        tree_view_container.setObjectName("TreeViewContainer")
        tree_view_layout = QVBoxLayout(tree_view_container)
        tree_view_layout.setContentsMargins(10, 4, 0, 0)
        tree_view_layout.setSpacing(0)
        
        # Tree view - usar subclase profesional que oculta líneas de conexión
        self._tree_view = MinimalTreeView(tree_view_container)
        self._tree_view.setModel(self._model)
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setAnimated(True)
        self._tree_view.setExpandsOnDoubleClick(False)
        self._tree_view.setRootIsDecorated(False)  # Desactivar chevron nativo - dibujamos el nuestro a la derecha
        self._tree_view.setIndentation(12)
        self._tree_view.setUniformRowHeights(True)
        self._tree_view.setIconSize(FOLDER_ICON_SIZE)
        self._tree_view.setWordWrap(False)
        self._tree_view.setItemDelegate(FolderTreeSectionDelegate(self._tree_view))
        self._tree_view.setMouseTracking(True)
        # Scrollbar se muestra automáticamente solo cuando es necesario
        self._tree_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self._tree_view.setAcceptDrops(True)
        self._tree_view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        
        self._tree_view.clicked.connect(self._on_tree_clicked)
        self._tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        
        # Inicializar event_handler ANTES de installEventFilter para evitar errores
        self._event_handler = FolderTreeEventHandler(self, self._tree_view, self._model)
        self._tree_view.viewport().installEventFilter(self)
        
        tree_view_layout.addWidget(self._tree_view, 1)
        tree_container_layout.addWidget(tree_view_container, 1)
        layout.addWidget(tree_container, 1)
    
    def _on_state_selected(self, state: str) -> None:
        """Manejar selección de estado desde StateSectionWidget."""
        if self._state_manager:
            self._state_manager.on_state_selected(state)
    
    def _on_tab_changed(self, index: int, path: Optional[str]) -> None:
        """Manejar cambio de tab para actualizar estado activo."""
        if self._state_manager:
            self._state_manager.on_tab_changed(index, path)
    
    def _clear_tree_selection(self) -> None:
        """Limpiar selección del árbol de carpetas."""
        if self._state_manager:
            self._state_manager.clear_tree_selection()
    
    def _clear_state_selection(self, from_user_action: bool = False) -> None:
        """
        Limpiar selección del estado activo.
        
        Args:
            from_user_action: Si True, viene de acción del usuario (no activar guard).
        """
        if self._state_manager:
            self._state_manager.clear_state_selection(from_user_action=from_user_action)
    
    def _connect_splitter_signals(self) -> None:
        parent = self.parent()
        while parent:
            if isinstance(parent, QSplitter):
                parent.splitterMoved.connect(self._on_splitter_moved)
                break
            parent = parent.parent()
    
    def _on_splitter_moved(self, pos: int, index: int) -> None:
        if not self._is_resizing:
            self._is_resizing = True
            # Notificar al tree view INMEDIATAMENTE
            if hasattr(self._tree_view, '_set_resizing_state'):
                self._tree_view._set_resizing_state(True)
        # Timer solo para detectar fin del resize
        self._resize_debounce_timer.stop()
        self._resize_debounce_timer.start(33)  # 30fps throttling suave
    
    def resizeEvent(self, event) -> None:
        if not self._is_resizing:
            self._is_resizing = True
            if hasattr(self._tree_view, '_set_resizing_state'):
                self._tree_view._set_resizing_state(True)
        # Timer solo para detectar fin del resize
        self._resize_debounce_timer.stop()
        self._resize_debounce_timer.start(33)  # Throttling suave
        super().resizeEvent(event)
    
    def _on_resize_finished(self) -> None:
        self._is_resizing = False
        if hasattr(self._tree_view, '_set_resizing_state'):
            self._tree_view._set_resizing_state(False)
        # Forzar un repaint final para asegurar estado correcto
        self._tree_view.viewport().update()
    
    def _on_tree_clicked(self, index: QModelIndex) -> None:
        """
        Manejar click en item del árbol.
        
        NAVEGACIÓN: Este handler se ejecuta solo por clicks del usuario (clicked signal).
        Delega al event_handler que emite folder_selected para navegación.
        """
        if self._event_handler:
            self._event_handler.handle_tree_click(index)
        else:
            logger.warning("_on_tree_clicked: _event_handler es None")
    
    def _on_single_click_timeout(self) -> None:
        # Placeholder: método reservado para futuras funcionalidades
        pass
    
    def add_focus_path(self, path: str, skip_sort: bool = False) -> None:
        # Rechazar Escritorio globalmente
        if is_system_desktop(path):
            return
        
        normalized_path = normalize_path(path)
        
        if normalized_path in self._path_to_item:
            if self._reposition_node_if_needed(normalized_path):
                return
        
        item = add_focus_path_to_model(self._model, self._path_to_item, path, skip_sort=skip_sort)
        if not item:
            return
        
        self._expand_parent_if_needed(path)
    
    def _reposition_node_if_needed(self, normalized_path: str) -> bool:
        existing_item = self._path_to_item.get(normalized_path)
        if not existing_item:
            return False
        
        try:
            current_parent = existing_item.parent() if existing_item.parent() else self._model.invisibleRootItem()
        except RuntimeError:
            # Objeto C++ ya fue eliminado
            return False
        
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
    
    def has_path(self, path: str) -> bool:
        """Verificar si un path existe en el sidebar."""
        normalized_path = normalize_path(path)
        return normalized_path in self._path_to_item
    
    def add_path(self, path: str) -> None:
        """Agregar path al sidebar (alias público de add_focus_path)."""
        self.add_focus_path(path)
    
    def remove_path(self, path: str) -> None:
        """Eliminar path del sidebar (alias público de remove_focus_path)."""
        remove_focus_path_from_model(self._model, self._path_to_item, path)
    
    def sync_children(self, parent_path: str, real_children: set[str]) -> None:
        """
        Sincronizar hijos de una carpeta con la lista real recibida.
        
        Args:
            parent_path: Path de la carpeta padre.
            real_children: Set de paths normalizados de hijos reales.
        """
        normalized_parent = normalize_path(parent_path)
        
        if normalized_parent not in self._path_to_item:
            return
        
        parent_item = self._path_to_item[normalized_parent]
        
        # Obtener hijos actuales en el modelo
        current_children = set()
        for i in range(parent_item.rowCount()):
            child = parent_item.child(i)
            if child:
                child_path = child.data(Qt.ItemDataRole.UserRole)
                if child_path:
                    current_children.add(normalize_path(child_path))
        
        # Guardar si el padre tenía hijos antes (para detectar cambio de 0 a >0)
        had_children_before = parent_item.rowCount() > 0
        
        # Agregar carpetas nuevas que no están en el modelo
        for child_path in real_children:
            if child_path not in current_children:
                add_focus_path_to_model(self._model, self._path_to_item, child_path)
        
        # Eliminar carpetas que ya no existen
        for child_path in current_children:
            if child_path not in real_children:
                remove_focus_path_from_model(self._model, self._path_to_item, child_path)
        
        # Si el padre pasó de no tener hijos a tener hijos (o viceversa),
        # notificar al modelo que el estado visual del item cambió
        # Qt decidirá automáticamente qué repintar
        has_children_after = parent_item.rowCount() > 0
        if had_children_before != has_children_after:
            parent_index = self._model.indexFromItem(parent_item)
            if parent_index.isValid():
                self._model.dataChanged.emit(parent_index, parent_index, [])
    
    def update_focus_path(self, old_path: str, new_path: str) -> None:
        """Update focus path in sidebar."""

        normalized_old = normalize_path(old_path)
        normalized_new = normalize_path(new_path)

        logger.info(f"   Normalized: '{normalized_old}' -> '{normalized_new}'")

        if normalized_old not in self._path_to_item:
            logger.info(f"   ❌ SKIP: normalized_old not in _path_to_item")
            return

        if not os.path.isdir(normalized_new):
            logger.info(f"   ❌ SKIP: new_path is not a directory")
            return

        # Compare original paths to detect case-only renames (e.g., "folder" -> "FOLDER")
        if old_path == new_path:
            logger.info(f"   ❌ SKIP: old_path == new_path (no change)")
            return

        logger.info(f"   ✅ PROCEEDING with rename in sidebar")
        
        tab_manager = find_tab_manager(self)
        if tab_manager and hasattr(tab_manager, 'get_tabs'):
            tabs = tab_manager.get_tabs()
            # Normalizar tabs para comparación
            normalized_tabs = {normalize_path(tab) for tab in tabs}
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

        # PASO 4: Crear nuevo item con new_path original (preserva case correcto)
        new_item = add_focus_path_to_model(self._model, self._path_to_item, new_path)
        
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
        # Split: interno = reordenar raíz; externo = mover filesystem
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
        # Split: interno = solo orden visual; externo = mover archivos reales
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
                # Guardar orden de carpetas raíz después de reorder exitoso
                self._save_root_folders_order()
            else:
                event.ignore()
        else:
            # External file drag - validación centralizada en handle_drop()
            tab_manager = find_tab_manager(self)
            watcher = None
            if tab_manager and hasattr(tab_manager, 'get_watcher'):
                watcher = tab_manager.get_watcher()
            
            source_paths = handle_drop(event, self._tree_view, self._model, watcher=watcher, path_to_item=self._path_to_item)
            
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
        parent_item = find_parent_item(self._model, self._path_to_item, normalize_path(path))
        if parent_item != self._model.invisibleRootItem():
            parent_index = self._model.indexFromItem(parent_item)
            if parent_index.isValid():
                self._tree_view.expand(parent_index)
    
    def _apply_styling(self) -> None:
        self.setStyleSheet(get_complete_stylesheet())
        
        if hasattr(self, '_tree_view') and self._tree_view:
            FontManager.safe_set_font(
                self._tree_view,
                'Segoe UI',
                FontManager.SIZE_NORMAL,  # 11px (reducido de SIZE_MEDIUM que era 13px)
                QFont.Weight.Normal
            )
    
    
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            child_widget = self.childAt(event.pos())
            if child_widget is not None:
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
            # parent_path puede ser original o normalizado, normalizar para búsqueda
            normalized_parent = normalize_path(parent_path)
            if normalized_parent not in self._path_to_item:
                return
            
            try:
                parent_item = self._path_to_item[normalized_parent]
                row_count = parent_item.rowCount()
            except RuntimeError:
                # Objeto C++ ya fue eliminado durante el cierre
                return
            
            for i in range(row_count):
                try:
                    child = parent_item.child(i)
                    if child:
                        # Obtener path original (case-preserving) para guardar estado
                        child_path = _get_original_path(child)
                        if child_path and child_path not in paths:
                            paths.append(child_path)
                            add_children_recursive(child_path)
                except RuntimeError:
                    # Objeto C++ ya fue eliminado durante el cierre
                    continue
        
        # Add children of each root folder
        for root_path in root_paths:
            add_children_recursive(root_path)
        
        return paths
    
    def get_expanded_paths(self) -> list[str]:
        root = self._model.invisibleRootItem()
        return collect_expanded_paths(self._model, self._path_to_item, self._tree_view, root)
    
    def get_root_folders_order(self) -> list[str]:
        """
        Obtener orden de carpetas raíz (paths normalizados).
        
        Solo devuelve paths normalizados de carpetas raíz, en el orden visual actual.
        Usado para persistir el orden después de reorders.
        """
        root_paths = get_root_folder_paths(self._model, self._path_to_item)
        # Normalizar paths para guardar orden (comparaciones internas)
        return [normalize_path(path) for path in root_paths]
    
    def _save_root_folders_order(self) -> None:
        """
        Guardar orden de carpetas raíz después de un reorder exitoso.
        
        Obtiene el orden actual y guarda el estado completo de la aplicación.
        Si hay WorkspaceManager, usa save_current_state() del workspace.
        Si no hay WorkspaceManager, usa save_app_state() del estado global.
        """
        try:
            tab_manager = find_tab_manager(self)
            if not tab_manager:
                return
            
            # Verificar si hay WorkspaceManager
            workspace_manager = None
            if hasattr(tab_manager, '_workspace_manager'):
                workspace_manager = tab_manager._workspace_manager
            
            if workspace_manager:
                # Usar save_current_state() del workspace manager
                workspace_manager.save_current_state(tab_manager, self)
            else:
                # Usar save_app_state() del estado global (sin workspace)
                tabs = tab_manager.get_tabs()
                active_tab = tab_manager.get_active_folder()
                history = tab_manager.get_history()
                history_index = tab_manager.get_history_index()
                focus_tree_paths = self.get_focus_tree_paths()
                expanded_nodes = self.get_expanded_paths()
                root_folders_order = self.get_root_folders_order()
                
                state_manager = tab_manager.get_state_manager()
                state = state_manager.build_app_state(
                    tabs=tabs,
                    active_tab_path=active_tab,
                    history=history,
                    history_index=history_index,
                    focus_tree_paths=focus_tree_paths,
                    expanded_nodes=expanded_nodes,
                    root_folders_order=root_folders_order
                )
                state_manager.save_app_state(state)
        except Exception as e:
            logger.error(f"Error saving root folders order: {e}", exc_info=True)
    
    def get_current_state(self) -> tuple[list[str], list[str]]:
        paths = self.get_focus_tree_paths()
        expanded = self.get_expanded_paths()
        return (paths, expanded)
    
    def load_workspace_state(self, paths: list[str], expanded: list[str], root_folders_order: list[str] = None) -> None:
        self.restore_tree(paths, expanded, root_folders_order)
    
    def restore_tree(self, paths: list[str], expanded_paths: list[str], root_folders_order: list[str] = None) -> None:
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
        
        # Filtrar Escritorio globalmente; Clarity no se filtra a nivel global
        filtered_paths = [path for path in paths if not is_system_desktop(path)]
        filtered_expanded = [path for path in expanded_paths if not is_system_desktop(path)]
        filtered_root_order = [path for path in root_folders_order if not is_system_desktop(path)] if root_folders_order else None
        
        # Separate root folders from children
        root = self._model.invisibleRootItem()
        root_paths = []
        child_paths = []
        
        # Crear set de paths normalizados para comparación rápida
        normalized_paths_set = {normalize_path(p) for p in filtered_paths}
        
        for path in filtered_paths:
            normalized = normalize_path(path)
            # Check if path would be a root folder (no parent in paths list)
            parent_path = os.path.dirname(normalized)
            normalized_parent = normalize_path(parent_path) if parent_path else None
            
            # If parent is not in normalized paths set, it's a root folder
            if not normalized_parent or normalized_parent not in normalized_paths_set:
                root_paths.append(path)  # Preservar path original
            else:
                child_paths.append(path)  # Preservar path original
        
        # Ordenar carpetas raíz según root_folders_order si existe
        if filtered_root_order:
            # Crear diccionario de orden: normalized_path -> índice en root_folders_order
            order_map = {normalized: idx for idx, normalized in enumerate(filtered_root_order)}
            
            # Separar carpetas con orden guardado y nuevas carpetas
            ordered_roots = []
            new_roots = []
            
            for path in root_paths:
                normalized = normalize_path(path)
                if normalized in order_map:
                    ordered_roots.append((order_map[normalized], path))
                else:
                    new_roots.append(path)
            
            # Ordenar según el orden guardado
            ordered_roots.sort(key=lambda x: x[0])
            root_paths = [path for _, path in ordered_roots] + new_roots
        
        # Add root folders first (preserving order)
        # IMPORTANTE: skip_sort=True durante restauración para mantener orden guardado
        for path in root_paths:
            self.add_focus_path(path, skip_sort=True)
        
        # Then add children (they will be placed under their parents)
        for path in child_paths:
            self.add_focus_path(path, skip_sort=True)
        
        # Expand specified nodes
        expanded_set = set(filtered_expanded)
        for path in expanded_set:
            try:
                # Normalizar path para buscar en _path_to_item (las claves están normalizadas)
                normalized_path = normalize_path(path)
                if normalized_path in self._path_to_item:
                    item = self._path_to_item[normalized_path]
                    index = self._model.indexFromItem(item)
                    if index.isValid():
                        self._tree_view.expand(index)
            except Exception as e:
                logger.warning(f"Error expanding path {path}: {e}")
        
        # Desbloquear señales después de cargar contenido completo
        self._tree_view.blockSignals(False)
    
    def showEvent(self, event) -> None:
        super().showEvent(event)
    
    def _get_separator_line_x(self, index: QModelIndex, visual_rect: QRect) -> int | None:
        if not index.isValid() or not visual_rect.isValid():
            return None
        
        # Verificar si tiene chevron o es raíz (tiene controles)
        item = self._model.itemFromIndex(index)
        has_chevron = item and item.rowCount() > 0
        is_root = not index.parent().isValid()
        
        # Solo hay línea si tiene controles (chevron o tres puntitos)
        if not has_chevron and not is_root:
            return None
        
        # Consultar directamente al delegate para obtener la posición usando método centralizado
        delegate = self._tree_view.itemDelegate()
        if delegate and hasattr(delegate, '_calculate_separator_line_x'):
            viewport_width = self._tree_view.viewport().width()
            return delegate._calculate_separator_line_x(viewport_width)
        
        return None
    
    def _get_chevron_rect(self, index: QModelIndex, visual_rect: QRect) -> QRect:
        """
        Obtener el área clickeable del chevron en coordenadas del viewport.
        Usa el método centralizado del delegate para asegurar alineación perfecta con el dibujo visual.
        """
        if not index.isValid() or not visual_rect.isValid():
            return QRect()
        
        delegate = self._tree_view.itemDelegate()
        if not delegate:
            return QRect()
        
        # Usar el método centralizado del delegate que usa la misma lógica que _paint_chevron_right
        if hasattr(delegate, '_get_chevron_clickable_rect'):
            style = self._tree_view.style()
            option = QStyleOptionViewItem()
            option.initFrom(self._tree_view)
            option.rect = visual_rect
            option.state = QStyle.State.State_Enabled
            
            # Obtener rect en coordenadas relativas a option.rect
            chevron_rect_rel = delegate._get_chevron_clickable_rect(option, index)
            
            # Convertir a coordenadas absolutas del viewport
            return QRect(
                visual_rect.left() + chevron_rect_rel.left(),
                visual_rect.top() + chevron_rect_rel.top(),
                chevron_rect_rel.width(),
                chevron_rect_rel.height()
            )
        
        # Fallback si el delegate no tiene el método (no debería ocurrir)
        return QRect()
    
    def eventFilter(self, obj, event) -> bool:
        """Filtrar eventos del viewport del árbol."""
        if obj == self._tree_view.viewport() and self._event_handler:
            if event.type() == QMouseEvent.Type.MouseButtonPress:
                # Manejar clic derecho para menú contextual
                if event.button() == Qt.MouseButton.RightButton:
                    handled = self._event_handler.handle_context_menu(event)
                    if handled:
                        return True
                else:
                    handled = self._event_handler.handle_mouse_press(event)
                    if handled:
                        return True
            elif event.type() == QMouseEvent.Type.MouseButtonRelease:
                handled = self._event_handler.handle_mouse_release(event)
                if handled:
                    return True
            elif event.type() == QMouseEvent.Type.MouseMove:
                self._event_handler.handle_mouse_move(event)
        return super().eventFilter(obj, event)
    
    def closeEvent(self, event) -> None:
        if hasattr(self, '_click_expand_timer') and self._click_expand_timer.isActive():
            self._click_expand_timer.stop()
        super().closeEvent(event)

    def paintEvent(self, event) -> None:
        """Pintar fondo sólido de refuerzo para el sidebar con instrumentación."""
        if not hasattr(self, '_paint_count_debug'): self._paint_count_debug = 0
        self._paint_count_debug += 1
        t = QElapsedTimer()
        t.start()

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(SIDEBAR_BG))
        painter.end()
        
        # super().paintEvent(event) NO es necesario si ya pintamos todo
        
        elapsed = t.nsecsElapsed() / 1000000.0
        if DEBUG_LAYOUT:
            logger.info(f"🎨 [Sidebar] Paint #{self._paint_count_debug} | dur={elapsed:.2f}ms")
