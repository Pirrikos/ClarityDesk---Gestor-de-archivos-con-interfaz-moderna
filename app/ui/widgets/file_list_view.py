"""
FileListView - Vista de lista/tabla para mostrar archivos.

Muestra archivos en una tabla con nombre, extensión y fecha de modificación.
Emite una señal en doble clic para abrir el archivo.
"""

from typing import Optional, Callable

from PySide6.QtCore import Qt, Signal, QEvent, QTimer, QElapsedTimer
from PySide6.QtGui import QContextMenuEvent, QMouseEvent, QResizeEvent
from PySide6.QtWidgets import QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView

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
from app.core.constants import DEBUG_LAYOUT
from app.core.logger import get_logger
logger = get_logger(__name__)
from app.managers.workspace_manager import WorkspaceManager


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
        state_manager: Optional[FileStateManager] = None,
        get_label_callback: Optional[Callable] = None,
        workspace_manager: Optional[WorkspaceManager] = None
    ):
        """
        Inicializa FileListView con lista de archivos vacía.

        Args:
            icon_service: Instancia Opcional de IconService.
            parent: Widget padre.
            tab_manager: Instancia Opcional de TabManager.
            state_manager: Instancia Opcional de FileStateManager.
            get_label_callback: Callback opcional para obtener labels de estado.
            workspace_manager: Instancia Opcional de WorkspaceManager.
        """
        super().__init__(parent)
        self.setAutoFillBackground(False)
        self._files: list[str] = []
        self._icon_service = icon_service or IconService()
        self._tab_manager = tab_manager
        self._workspace_manager = workspace_manager
        self._checked_paths: set[str] = set()
        self._state_manager = state_manager or (FileStateManager() if FileStateManager else None)
        self._get_label_callback = get_label_callback
        self._header_checkbox: Optional[QCheckBox] = None
        self._hovered_row: int = -1
        self._resize_in_progress: bool = False
        self._last_resize_size = None

        # Timer para restaurar el layout automático una vez estabilizado el resize (coalesce)
        self._finalize_resize_timer: QTimer = QTimer(self)
        self._finalize_resize_timer.setSingleShot(True)
        self._finalize_resize_timer.setInterval(150)
        self._finalize_resize_timer.timeout.connect(self._finalize_resize)

        self._resize_timer: QElapsedTimer = QElapsedTimer()
        # Estado de ordenamiento: None indica "sin ordenamiento (usar orden natural)"
        # Solo se activa cuando el usuario hace clic en un header
        self._sort_column: Optional[int] = None
        self._sort_order: Optional[Qt.SortOrder] = None
        self._current_folder: Optional[str] = None  # Para rastrear cambios de carpeta
        self._update_generation: int = 0  # Counter para invalidar actualizaciones obsoletas
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
        # Incrementar generación para invalidar actualizaciones obsoletas pendientes
        self._update_generation += 1
        current_generation = self._update_generation
        
        # CRÍTICO: Siempre reemplazar completamente _files con la nueva lista
        # NO confiar en el contenido previo de _files
        from app.core.logger import get_logger
        import os
        logger = get_logger(__name__)

        # DEBUG: Mostrar qué recibimos ANTES de expand_stacks_to_files
        logger.debug(f">>> update_files LLAMADO (gen={current_generation}): recibiendo {len(file_list)} items")
        for idx, item in enumerate(file_list[:5]):  # Primeros 5
            if hasattr(item, 'files'):
                logger.debug(f"  [{idx}] FileStack con {len(item.files)} archivos")
            else:
                logger.debug(f"  [{idx}] {os.path.basename(item)}")

        self._files = expand_stacks_to_files(file_list)
        logger.debug(f">>> Después de expand_stacks_to_files: {len(self._files)} archivos")

        # Detectar cambio de carpeta y cargar preferencias de ordenamiento
        current_folder = None
        if self._tab_manager and not self._tab_manager.has_state_context():
            current_folder = self._tab_manager.get_active_folder()

            # DEBUG: Logging para diagnosticar el problema
            logger.debug(f"update_files: current_folder={current_folder}, prev_folder={self._current_folder}, files_count={len(self._files)}")

            if current_folder != self._current_folder:
                # Cambio de carpeta detectado - incrementar generación para cancelar updates obsoletas
                self._update_generation += 1
                current_generation = self._update_generation
                self._current_folder = current_folder
                self._load_folder_sort_preferences()
                logger.debug(f"Cambio de carpeta detectado (nueva gen={current_generation}). sort_column={self._sort_column}, sort_order={self._sort_order}")

        # CRÍTICO: SIEMPRE validar que _files solo contiene archivos de la carpeta actual
        # Esto previene que archivos de navegaciones previas se mezclen al ordenar
        # Debe ejecutarse siempre, no solo cuando cambia la carpeta
        if current_folder and self._files:
            from app.services.path_utils import normalize_path
            import os
            from app.core.logger import get_logger
            logger = get_logger(__name__)

            base = normalize_path(current_folder)

            # DEBUG: Mostrar archivos ANTES del filtrado con PATH COMPLETO
            logger.debug(f"========================================")
            logger.debug(f"INICIO FILTRADO DEFENSIVO")
            logger.debug(f"  Base normalizada: '{base}'")
            logger.debug(f"  Archivos a filtrar: {len(self._files)}")
            logger.debug(f"========================================")

            for idx, f in enumerate(self._files[:10]):  # Solo primeros 10
                parent = os.path.dirname(f)
                logger.debug(f"  [{idx}] {os.path.basename(f)}")
                logger.debug(f"       Path completo: {f}")
                logger.debug(f"       Parent dir: {parent}")

            # Filtrar archivos: solo mantener los que están DIRECTAMENTE en current_folder
            # No confundir con subcarpetas (las carpetas/archivos dentro de subcarpetas deben excluirse)
            validated_files = []
            excluded_count = 0
            for f in self._files:
                try:
                    normalized_file = normalize_path(f)
                    parent_dir = os.path.dirname(normalized_file)
                    # Solo incluir si el padre directo coincide exactamente con current_folder
                    if parent_dir == base:
                        validated_files.append(f)
                    else:
                        excluded_count += 1
                        if excluded_count <= 10:  # Solo mostrar primeros 10 excluidos
                            logger.warning(f"❌ EXCLUIDO [{excluded_count}]: {os.path.basename(f)}")
                            logger.warning(f"   Path normalizado: {normalized_file}")
                            logger.warning(f"   Parent dir: '{parent_dir}'")
                            logger.warning(f"   Base dir:   '{base}'")
                            logger.warning(f"   ¿Coinciden? {parent_dir == base}")
                except Exception as e:
                    logger.error(f"Error normalizando '{f}': {e}")
                    continue

            # DEBUG: Resultado del filtrado
            logger.debug(f"========================================")
            logger.debug(f"RESULTADO FILTRADO:")
            logger.debug(f"  Antes: {len(self._files)} archivos")
            logger.debug(f"  Después: {len(validated_files)} archivos")
            logger.debug(f"  Excluidos: {excluded_count} archivos")
            logger.debug(f"========================================")

            if excluded_count > 0:
                logger.warning(f"⚠️ Se excluyeron {excluded_count} archivos que NO pertenecen a la carpeta actual")

            # IMPORTANTE: Reemplazar completamente _files, no modificar in-place
            self._files = validated_files

        # Verificar que esta actualización sigue siendo válida (no fue supersedida por navegación)
        if current_generation != self._update_generation:
            logger.warning(f"⚠️ Actualización obsoleta detectada (gen={current_generation} vs actual={self._update_generation}). Abortando refresh.")
            return

        self._refresh_table()

    def _refresh_table(self) -> None:
        """Rebuild table rows from file list."""
        # Remove checked paths that no longer exist in the current file list
        self._checked_paths = {path for path in self._checked_paths if path in self._files}

        # TabManager.get_files() es la única fuente de verdad - no se filtra aquí
        # self._files contiene exactamente los archivos que deben mostrarse

        refresh_table(
            self, self._files, self._icon_service,
            self._state_manager, self._checked_paths, self._on_checkbox_changed,
            self._get_label_callback, self._tab_manager, self._workspace_manager
        )
        try:
            from app.core.logger import get_logger
            logger = get_logger(__name__)
            vp = self.viewport()
            if DEBUG_LAYOUT:
                logger.info(
                    f"📏 [List] rows={self.rowCount()} | table_h={self.height()} | vp_h={vp.height()} | vp_rect={vp.rect()}"
                )
        except Exception:
            pass
    
    def update_item_state_visual(self, file_path: str, new_state: Optional[str]) -> bool:
        """
        Actualizar estado visual de un item específico sin reconstruir la tabla.
        
        Args:
            file_path: Ruta del archivo cuyo estado cambió.
            new_state: Nuevo estado (o None para eliminar estado).
            
        Returns:
            True si se encontró la fila y se actualizó, False si no existe.
        """
        from app.ui.widgets.list_state_delegate import STATE_ROLE
        for row in range(self.rowCount()):
            name_item = self.item(row, 1)
            if name_item and name_item.data(Qt.ItemDataRole.UserRole) == file_path:
                state_item = self.item(row, 4)
                if state_item:
                    state_item.setData(STATE_ROLE, new_state)
                    self.viewport().update()
                    return True
        return False
    
    def refresh_state_labels(self, state_id: Optional[str]) -> None:
        """
        Refrescar labels de estado en todas las filas visibles.
        
        Cuando se renombra un label de estado, este método actualiza solo el texto
        visible sin reconstruir la tabla.
        
        Args:
            state_id: ID del estado cuyo label cambió (o None para refrescar todos).
        """
        # Con delegate: basta forzar repaint del viewport; opcionalmente filtrar por state_id
        self.viewport().update()

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
    
    def resizeEvent(self, event) -> None:
        """Manejar resize SIN ajustar columnas (para evitar parpadeo)."""
        super().resizeEvent(event)
        # Las columnas solo se ajustan cuando se usan los botones de tamaño de ventana
        # NO durante resize continuo (drag), porque causa parpadeo

    def _adjust_columns_to_viewport_width(self) -> None:
        """
        Ajustar anchos de columnas para usar el ancho disponible del viewport.

        - Ventana pequeña (< 1000px): Anchos fijos mínimos
        - Ventana mediana/grande (>= 1000px): Distribuir espacio disponible
        """
        viewport_width = self.viewport().width()
        header = self.horizontalHeader()

        # Ancho fijo de columna checkbox
        checkbox_width = 16

        if viewport_width < 1000:
            # Ventana pequeña: usar anchos mínimos fijos
            header.resizeSection(1, 300)  # Nombre (mínimo)
            header.resizeSection(2, 100)  # Tipo
            header.resizeSection(3, 150)  # Fecha
            header.resizeSection(4, 120)  # Estado
        else:
            # Ventana mediana/grande: distribuir espacio disponible
            # Dejar más margen: scrollbar (20px) + margen derecho (40px) = 60px total
            available_width = viewport_width - checkbox_width - 60

            # Distribución proporcional:
            # Nombre: 50% del espacio
            # Tipo: 13%
            # Fecha: 20%
            # Estado: 17%
            nombre_width = max(300, int(available_width * 0.50))
            tipo_width = max(100, int(available_width * 0.13))
            fecha_width = max(150, int(available_width * 0.20))
            estado_width = max(120, int(available_width * 0.17))

            header.resizeSection(1, nombre_width)
            header.resizeSection(2, tipo_width)
            header.resizeSection(3, fecha_width)
            header.resizeSection(4, estado_width)

    def _finalize_resize(self) -> None:
        """Obsoleto - no ajustamos columnas para evitar parpadeo."""
        pass

    def _on_resize_paint_tick(self) -> None:
        """Obsolete."""
        pass

    def _set_row_widgets_visible(self, visible: bool) -> None:
        try:
            for row in range(self.rowCount()):
                for col in (0, 4):
                    w = self.cellWidget(row, col)
                    if w:
                        w.setVisible(visible)
        except RuntimeError:
            pass

    def viewportEvent(self, event: QEvent) -> bool:
        et = event.type()
        if DEBUG_LAYOUT:
            if et == QEvent.Paint:
                rect = self.viewport().rect()
                logger.warning(f"🎯 Viewport.Paint rect: {rect}")
            elif et == QEvent.Resize:
                sz = self.viewport().size()
                logger.warning(f"📐 Viewport.Resize size: {sz.width()}x{sz.height()}")
            elif et == QEvent.UpdateRequest:
                logger.info("🔄 Viewport.UpdateRequest")
        return super().viewportEvent(event)

    def showEvent(self, event) -> None:
        """Propagar evento de mostrar."""
        super().showEvent(event)


    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        item = self.itemAt(event.pos())
        new_hovered_row = item.row() if item else -1
        if new_hovered_row < 0:
            if self._hovered_row >= 0:
                old_row = self._hovered_row
                self._hovered_row = -1
                self._update_row_visual(old_row)
                self.viewport().update()
            return
        if new_hovered_row != self._hovered_row:
            old_row = self._hovered_row
            self._hovered_row = new_hovered_row
            if old_row >= 0:
                self._update_row_visual(old_row)
            if new_hovered_row >= 0:
                self._update_row_visual(new_hovered_row)
            self.viewport().update()

    def leaveEvent(self, event) -> None:
        if self._hovered_row >= 0:
            old_row = self._hovered_row
            self._hovered_row = -1
            self._update_row_visual(old_row)
        self.viewport().update()
        super().leaveEvent(event)

    def _update_row_visual(self, row: int) -> None:
        if row < 0 or row >= self.rowCount():
            return
        index = self.model().index(row, 0)
        if index.isValid():
            rect = self.visualRect(index)
            if self.columnCount() > 0:
                last_index = self.model().index(row, self.columnCount() - 1)
                if last_index.isValid():
                    last_rect = self.visualRect(last_index)
                    rect.setRight(last_rect.right())
            self.viewport().update(rect)

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
        from app.services.path_utils import normalize_path
        target = normalize_path(file_path)
        for row in range(self.rowCount()):
            item = self.item(row, 1)
            if item:
                path = item.data(Qt.ItemDataRole.UserRole)
                if path and normalize_path(path) == target:
                    return row
        return -1

    def _load_folder_sort_preferences(self) -> None:
        """Cargar preferencias de ordenamiento para la carpeta actual."""
        if not self._current_folder:
            # Sin carpeta activa, resetear a sin ordenamiento
            self._sort_column = None
            self._sort_order = None
            return

        from app.services.folder_sort_storage import get_folder_sort
        preferences = get_folder_sort(self._current_folder)

        if preferences:
            self._sort_column, self._sort_order = preferences
            # Actualizar indicador visual
            header = self.horizontalHeader()
            header.setSortIndicatorShown(True)
            header.setSortIndicator(self._sort_column, self._sort_order)
        else:
            # Sin preferencias guardadas: MANTENER el ordenamiento actual
            # NO resetear a None - el usuario puede tener ordenamiento activo
            # que quiere aplicar a todas las carpetas
            if self._sort_column is not None and self._sort_order is not None:
                # Mantener ordenamiento actual y actualizar indicador
                header = self.horizontalHeader()
                header.setSortIndicatorShown(True)
                header.setSortIndicator(self._sort_column, self._sort_order)
            else:
                # Si no hay ordenamiento activo, no hacer nada
                header = self.horizontalHeader()
                header.setSortIndicatorShown(False)

    def _save_folder_sort_preferences(self) -> None:
        """Guardar preferencias de ordenamiento para la carpeta actual."""
        if not self._current_folder or self._sort_column is None or self._sort_order is None:
            return

        from app.services.folder_sort_storage import set_folder_sort
        set_folder_sort(self._current_folder, self._sort_column, self._sort_order)

    def _on_sort_column_clicked(self, logical_index: int) -> None:
        if logical_index < 1 or logical_index > 4:
            return
        if logical_index == self._sort_column:
            self._sort_order = (
                Qt.SortOrder.DescendingOrder
                if self._sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._sort_column = logical_index
            self._sort_order = Qt.SortOrder.AscendingOrder

        header = self.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(self._sort_column, self._sort_order)

        # Guardar preferencias para esta carpeta
        self._save_folder_sort_preferences()

        self._refresh_table()

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

    def clear_selection(self) -> None:
        """Compatibility alias: call Qt's `clearSelection()` for consistency with grid view."""
        # QTableWidget already exposes clearSelection(); provide snake_case alias
        self.clearSelection()
        # Clear checkbox selection to prevent accumulation of old paths
        self._checked_paths.clear()
        # Update header checkbox state to reflect cleared selection
        self._update_header_checkbox_state()

    def set_selected_states(self, state) -> None:
        """
        Set state for all selected files.
        
        La actualización visual se maneja a través de las señales state_changed/states_changed
        emitidas por FileStateManager, que son procesadas por FileViewContainer._on_state_changed
        y _on_states_changed para decidir si refrescar la vista o solo actualizar badges.
        
        Args:
            state: State constant or None to remove state.
        """
        if not self._state_manager:
            return
        
        selected_paths = self.get_selected_paths()
        if not selected_paths:
            return
        
        # Update states in manager - esto emitirá states_changed que será procesado por FileViewContainer
        self._state_manager.set_files_state(selected_paths, state)
        
        # NO refrescar tabla aquí - dejar que las señales manejen la actualización
    
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
