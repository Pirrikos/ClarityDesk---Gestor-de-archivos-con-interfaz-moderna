"""
DesktopWindow - Desktop Focus window with vertical layout.

Auto-start window showing Desktop Focus (top) and Trash Focus (bottom).
Opens automatically on app startup.
"""

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, QUrl, QTimer, QPoint
from PySide6.QtGui import QDesktopServices, QMouseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from app.core.logger import get_logger
from app.managers.tab_manager import TabManager
from app.services.desktop_path_helper import get_clarity_folder_path, get_desktop_path
from app.services.icon_service import IconService
from app.services.path_utils import normalize_path
from app.services.trash_storage import TRASH_FOCUS_PATH
from app.ui.widgets.file_view_container import FileViewContainer
from app.ui.widgets.dock_background_widget import DockBackgroundWidget
from app.ui.widgets.file_view_sync import get_selected_files
from app.ui.windows.main_window_file_handler import filter_previewable_files
from app.ui.windows.quick_preview_window import QuickPreviewWindow
from app.ui.windows.preview_coordination import close_other_window_preview
from app.services.preview_pdf_service import PreviewPdfService

logger = get_logger(__name__)


class DesktopWindow(QWidget):
    """Desktop Focus window with vertical Desktop (top) and Trash (bottom) panels."""
    
    open_main_window = Signal()  # Emitted when user clicks to open main window
    
    # Dock layout constants
    STACK_TILE_WIDTH = 70
    DESKTOP_TILE_WIDTH = 70
    SETTINGS_TILE_WIDTH = 70
    SEPARATOR_WIDTH = 1
    STACK_SPACING = 12
    # Altura base: stack tile (85) + márgenes grid (32) + márgenes layout (56) = 173
    # Añadimos un poco más para el background y bordes
    BASE_WINDOW_HEIGHT = 150
    MIN_WINDOW_HEIGHT = 140
    ANIMATION_DURATION_MS = 250
    DEFAULT_WINDOW_WIDTH = 400
    
    # Layout margins
    MAIN_LAYOUT_MARGIN = 16
    CENTRAL_LAYOUT_MARGIN = 16
    GRID_LAYOUT_LEFT_MARGIN = 20
    GRID_LAYOUT_RIGHT_MARGIN = 12  # Simétrico con spacing después del separador
    
    # Screen positioning
    WINDOW_TOP_MARGIN = 10  # Margen desde la parte superior de la pantalla
    WINDOW_MAX_HEIGHT_MARGIN = 20
    INITIAL_WINDOW_WIDTH_RATIO = 0.6
    
    # Layout vertical margins (reducidos para dar más espacio a los stacks)
    MAIN_LAYOUT_VERTICAL_MARGIN = 8
    CENTRAL_LAYOUT_VERTICAL_MARGIN = 8
    
    def __init__(self, parent=None):
        """Initialize DesktopWindow with Desktop and Trash Focus."""
        super().__init__(parent)
        
        # Initialize managers and services as None - will be created in initialize_after_show()
        self._desktop_tab_manager: Optional[TabManager] = None
        self._trash_tab_manager: Optional[TabManager] = None
        self._icon_service: Optional[IconService] = None
        self._desktop_container: Optional[FileViewContainer] = None
        self._preview_service: Optional[PreviewPdfService] = None
        self._current_preview_window: Optional[QuickPreviewWindow] = None
        self._preview_shortcut: Optional[QShortcut] = None
        
        # Placeholder widget for desktop container (will be replaced after init)
        self._desktop_placeholder: Optional[QWidget] = None
        self._height_animation: Optional[QPropertyAnimation] = None
        self._width_animation: Optional[QPropertyAnimation] = None
        # Flag para prevenir relayouts durante animación de altura
        self._height_animation_in_progress: bool = False
        # Estado de expansión calculado antes de la animación (para usar al finalizar)
        self._pending_expansion_state: Optional[dict] = None
        
        # Setup UI structure only (no heavy initialization)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build Dock-style layout - exactly like macOS Dock."""
        self.setWindowTitle("ClarityDesk - Dock")
        
        # Set window flags: frameless, respeta Z-order normal del sistema
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool  # Don't show in taskbar
        )
        # Enable full transparency and prevent border flashing
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_PaintOnScreen, False)  # Prevent flicker
        # Disable window frame painting to prevent border flash
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        # Habilitar drops en la ventana principal
        self.setAcceptDrops(True)
        # Permitir que la ventana reciba foco para que funcionen los shortcuts
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Position window according to dock_anchor setting
        self._position_window_by_anchor()
        
        # Subscribe to anchor changes
        from app.managers import app_settings as app_settings_module
        if app_settings_module.app_settings is not None:
            app_settings_module.app_settings.dock_anchor_changed.connect(self._on_anchor_changed)
        # Minimum size will be set dynamically based on stacks count
        # Only set minimum height, width will be adjusted by _adjust_window_width
        self.setMinimumHeight(self.MIN_WINDOW_HEIGHT)
        # No max height limit - window expands as needed
        
        # Create dock background widget with Apple-style transparency
        self._central_widget = DockBackgroundWidget()
        
        # Layout raíz directamente en la ventana
        main_layout = QVBoxLayout(self)
        # Margins match the rounded background (8px outer + some inner padding)
        main_layout.setContentsMargins(
            self.MAIN_LAYOUT_MARGIN, 
            self.MAIN_LAYOUT_VERTICAL_MARGIN, 
            self.MAIN_LAYOUT_MARGIN, 
            self.MAIN_LAYOUT_VERTICAL_MARGIN
        )
        main_layout.setSpacing(0)
        
        # Añadir central_widget al layout raíz
        main_layout.addWidget(self._central_widget, 1)
        
        # Layout interno del central_widget (DockBackgroundWidget mantiene su layout interno)
        central_internal_layout = QVBoxLayout(self._central_widget)
        central_internal_layout.setContentsMargins(
            self.CENTRAL_LAYOUT_MARGIN, 
            self.CENTRAL_LAYOUT_VERTICAL_MARGIN, 
            self.CENTRAL_LAYOUT_MARGIN, 
            self.CENTRAL_LAYOUT_VERTICAL_MARGIN
        )
        central_internal_layout.setSpacing(0)
        
        # Placeholder widget for Desktop Focus panel (will be replaced in initialize_after_show)
        self._desktop_placeholder = QWidget()
        self._desktop_placeholder.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        central_internal_layout.addWidget(self._desktop_placeholder, 1)
        
        # NO footer - pure Dock style
        
        # Fully transparent window
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
    
    def initialize_after_show(self) -> None:
        """
        Initialize heavy components after window is shown.
        
        This method is called via QTimer.singleShot(0, ...) after show()
        to ensure the window appears immediately without blocking.
        """
        # Create TabManager instances for Desktop and Trash using separate storage to avoid collision
        from pathlib import Path as PathLib
        dock_storage = PathLib(__file__).parent.parent.parent / 'storage' / 'dock_tabs.json'
        trash_storage = PathLib(__file__).parent.parent.parent / 'storage' / 'trash_tabs.json'
        self._desktop_tab_manager = TabManager(str(dock_storage))
        self._trash_tab_manager = TabManager(str(trash_storage))
        
        # Set Desktop and Trash as active tabs
        clarity_path = get_clarity_folder_path()
        
        # CRÍTICO: Limpiar tabs existentes y asegurar que solo Clarity esté activo
        # Eliminar cualquier tab del escritorio completo que pueda estar guardado
        desktop_path = get_desktop_path()
        tabs = self._desktop_tab_manager.get_tabs()
        for tab_path in tabs[:]:  # Copia de la lista para iterar
            normalized_tab = normalize_path(tab_path)
            normalized_desktop = normalize_path(desktop_path)
            normalized_clarity = normalize_path(clarity_path)
            # Eliminar tab del escritorio completo (pero NO Clarity)
            if normalized_tab == normalized_desktop and normalized_tab != normalized_clarity:
                tab_index = tabs.index(tab_path)
                self._desktop_tab_manager.remove_tab(tab_index)
        
        # Asegurar que Clarity esté como tab activo
        self._desktop_tab_manager.add_tab(clarity_path)
        self._trash_tab_manager.add_tab(TRASH_FOCUS_PATH)
        
        # Create IconService
        self._icon_service = IconService()
        
        # Create PreviewPdfService for quick preview
        self._preview_service = PreviewPdfService(self._icon_service)
        
        # Setup shortcuts for preview
        self._setup_shortcuts()
        
        # Get parent widget for FileViewContainer (usar referencia directa)
        central_widget = self._central_widget
        
        # Create Desktop Focus panel
        self._desktop_container = FileViewContainer(
            self._desktop_tab_manager,
            self._icon_service,
            None,
            central_widget,  # Parent widget
            is_desktop=True  # Flag explícito: este es DesktopWindow
        )
        
        # Connect expansion height changes to adjust window size
        self._desktop_container.expansion_height_changed.connect(self._adjust_window_height)
        
        # Connect stacks count changes to adjust window width
        self._desktop_container.stacks_count_changed.connect(self._adjust_window_width)
        
        # Connect open_file signal to open files with default application
        self._desktop_container.open_file.connect(self._open_file)
        
        # Get initial stacks count and adjust width
        use_stacks = True  # DesktopWindow always uses stacks
        initial_items = self._desktop_tab_manager.get_files(use_stacks=use_stacks)
        if initial_items and hasattr(initial_items[0], 'files'):  # FileStack objects
            initial_stacks_count = len(initial_items)
        else:
            initial_stacks_count = 0  # No stacks initially
        self._adjust_window_width(initial_stacks_count)
        
        # Replace placeholder with container directly (each stack has its own Dock-style container)
        layout = central_widget.layout()
        if layout and self._desktop_placeholder:
            # Get placeholder index
            placeholder_index = layout.indexOf(self._desktop_placeholder)
            
            # Remove placeholder
            layout.removeWidget(self._desktop_placeholder)
            self._desktop_placeholder.setParent(None)
            self._desktop_placeholder = None
            
            # Insert container at the same position
            layout.insertWidget(placeholder_index, self._desktop_container, 1)
        
        # Warmup: forzar un ciclo de layout para evitar flash en primera contracción
        # Qt cachea información de layout después del primer ciclo
        QTimer.singleShot(100, self._warmup_layout)
        
        # Activar ventana y dar foco para que funcionen los shortcuts de espacio
        self.activateWindow()
        self.setFocus()
    
    def _warmup_layout(self) -> None:
        """
        Warmup del sistema de layouts para evitar flash en primera contracción.
        
        Qt cachea información de geometría y backbuffers después del primer ciclo.
        Este warmup fuerza ese ciclo de manera invisible.
        """
        if not self._desktop_container or not hasattr(self._desktop_container, '_grid_view'):
            return
        
        grid_view = self._desktop_container._grid_view
        if not grid_view:
            return
        
        # Obtener el ExpandedStacksWidget
        expanded_widget = getattr(grid_view, '_expanded_stacks_widget', None)
        if not expanded_widget:
            return
        
        # Forzar un ciclo de altura: 0 → altura pequeña → 0
        # Esto inicializa el cache de Qt sin que el usuario lo note
        expanded_widget.setFixedHeight(1)  # Altura mínima (casi invisible)
        expanded_widget.setFixedHeight(0)  # Volver a 0
        
        # Forzar un update del layout
        if hasattr(grid_view, '_content_widget'):
            grid_view._content_widget.updateGeometry()
    
    def _adjust_window_height(self, expansion_height: int) -> None:
        """Adjust window height based on stack expansion."""
        target_height, target_y = self._calculate_target_geometry(expansion_height)
        current_geometry = self.geometry()
        
        if current_geometry.height() == target_height:
            # Si no hay cambio de altura, ejecutar refresh inmediatamente si está pendiente
            if self._desktop_container and hasattr(self._desktop_container, '_grid_view'):
                grid_view = self._desktop_container._grid_view
                if grid_view and hasattr(grid_view, '_pending_refresh_after_animation'):
                    if grid_view._pending_refresh_after_animation:
                        if self._pending_expansion_state:
                            num_rows = self._pending_expansion_state.get('num_rows')
                            if num_rows:
                                grid_view._dock_rows_state = num_rows
                            self._pending_expansion_state = None
                        grid_view._pending_refresh_after_animation = False
                        grid_view._refresh_tiles()
            return
        
        # Si es la primera expansión (altura base), aplicar inmediatamente
        # para evitar que los archivos se superpongan con el nombre del stack
        is_first_expansion = current_geometry.height() == self.BASE_WINDOW_HEIGHT and expansion_height > 0
        
        if is_first_expansion:
            # Aplicar altura inmediatamente sin animación
            # Suprimir transiciones internas mientras se aplica el cambio
            if self._desktop_container and hasattr(self._desktop_container, '_grid_view'):
                try:
                    self._desktop_container._grid_view._suppress_content_transitions = True
                except Exception:
                    pass
            self.setGeometry(
                current_geometry.x(), target_y,
                current_geometry.width(), target_height
            )
            # Primera expansión: ejecutar refresh inmediatamente después de cambiar geometría
            if self._desktop_container and hasattr(self._desktop_container, '_grid_view'):
                grid_view = self._desktop_container._grid_view
                if grid_view and hasattr(grid_view, '_pending_refresh_after_animation'):
                    # Aplicar estado de expansión previamente calculado si existe
                    if self._pending_expansion_state:
                        # Bloquear filas al valor discreto calculado
                        num_rows = self._pending_expansion_state.get('num_rows')
                        if num_rows:
                            grid_view._dock_rows_state = num_rows
                        self._pending_expansion_state = None
                    grid_view._pending_refresh_after_animation = False
                    grid_view._refresh_tiles()
                    try:
                        grid_view._suppress_content_transitions = False
                    except Exception:
                        pass
        else:
            # Usar animación para cambios entre stacks
            if self._desktop_container and hasattr(self._desktop_container, '_grid_view'):
                grid_view = self._desktop_container._grid_view
                
                # Detectar si estamos colapsando (expansion_height = 0)
                is_collapsing = expansion_height == 0
                
                # Solo bloquear updates cuando NO estamos colapsando
                # El colapso no necesita bloquear - el contenido ya está oculto (altura 0)
                if not is_collapsing:
                    if grid_view and hasattr(grid_view, '_content_widget'):
                        grid_view._content_widget.setUpdatesEnabled(False)
                    try:
                        grid_view._suppress_content_transitions = True
                    except Exception:
                        pass
            
            # Marcar que la animación está en progreso
            self._height_animation_in_progress = True
            
            # El refresh se ejecutará al finalizar la animación en _force_grid_relayout()
            self._apply_height_animation(current_geometry, target_height, target_y)
    
    def _calculate_target_geometry(self, expansion_height: int) -> tuple[int, int]:
        """Calculate target height and Y position for window."""
        screen = self.screen().availableGeometry()
        
        target_height = self.BASE_WINDOW_HEIGHT + expansion_height
        max_screen_height = screen.height() - self.WINDOW_MAX_HEIGHT_MARGIN
        target_height = min(target_height, max_screen_height)
        target_height = max(target_height, self.MIN_WINDOW_HEIGHT)
        
        # Calculate Y position based on anchor
        target_y = self._calculate_y_position(target_height)
        return target_height, target_y
    
    def _calculate_y_position(self, window_height: int) -> int:
        """Calculate Y position based on dock_anchor setting."""
        from app.managers import app_settings as app_settings_module
        screen = self.screen().availableGeometry()
        
        if app_settings_module.app_settings is not None:
            anchor = app_settings_module.app_settings.dock_anchor
            if anchor == "bottom":
                # Bottom: y = screen bottom - window height - margin
                return screen.height() - window_height - self.WINDOW_TOP_MARGIN
        
        # Default: top
        return self.WINDOW_TOP_MARGIN
    
    def _position_window_by_anchor(self) -> None:
        """Position window according to dock_anchor setting."""
        screen = self.screen().availableGeometry()
        window_height = self.BASE_WINDOW_HEIGHT
        window_width = int(screen.width() * self.INITIAL_WINDOW_WIDTH_RATIO)
        window_x = (screen.width() - window_width) // 2
        window_y = self._calculate_y_position(window_height)
        self.setGeometry(window_x, window_y, window_width, window_height)
    
    def _on_anchor_changed(self, anchor: str) -> None:
        """Handle dock anchor change - reposition window once."""
        current_geometry = self.geometry()
        window_height = current_geometry.height()
        window_width = current_geometry.width()
        screen = self.screen().availableGeometry()
        window_x = (screen.width() - window_width) // 2
        window_y = self._calculate_y_position(window_height)
        self.setGeometry(window_x, window_y, window_width, window_height)
    
    def _force_grid_relayout(self) -> None:
        """Force grid layout recalculation after geometry animation finishes."""
        # Marcar que la animación ha terminado
        self._height_animation_in_progress = False
        
        if self._desktop_container and hasattr(self._desktop_container, '_grid_view'):
            grid_view = self._desktop_container._grid_view
            if grid_view:
                # Si estamos colapsando a estado base, no hacer nada
                # Los stacks ya están correctos, nunca se bloquearon updates
                if getattr(grid_view, '_is_collapsing_to_base', False):
                    grid_view._is_collapsing_to_base = False
                    return  # Salir sin tocar nada
                
                # Rehabilitar actualizaciones del grid (solo si fueron desactivadas)
                if hasattr(grid_view, '_content_widget'):
                    grid_view._content_widget.setUpdatesEnabled(True)
                
                # Con QStackedWidget, el estado de expansión ya está aplicado en on_stack_clicked
                # Solo necesitamos aplicar el número de filas discreto
                if self._pending_expansion_state:
                    num_rows = self._pending_expansion_state.get('num_rows')
                    if num_rows:
                        grid_view._dock_rows_state = num_rows
                    self._pending_expansion_state = None
                
                # Ejecutar refresh completo del grid con la altura final real
                if hasattr(grid_view, '_pending_refresh_after_animation'):
                    grid_view._pending_refresh_after_animation = False
                    grid_view._refresh_tiles()
                    try:
                        grid_view._suppress_content_transitions = False
                    except Exception:
                        pass
                else:
                    if hasattr(grid_view, '_grid_layout'):
                        grid_view._grid_layout.activate()
                        if hasattr(grid_view, '_content_widget'):
                            grid_view._content_widget.updateGeometry()
                            grid_view._content_widget.adjustSize()
                
                # Aplicar altura del QStackedWidget después de animación de REDUCCIÓN
                if getattr(grid_view, '_show_expanded_after_animation', False):
                    grid_view._show_expanded_after_animation = False
                    if hasattr(grid_view, '_expanded_stacks_widget') and grid_view._expanded_stacks_widget:
                        widget = grid_view._expanded_stacks_widget
                        if grid_view._expanded_stacks:  # Solo si hay stacks expandidos
                            # Calcular altura basada en el estado actual
                            num_rows = getattr(grid_view, '_dock_rows_state', 1) or 1
                            from app.ui.widgets.expanded_stacks_widget import ExpandedStacksWidget
                            height = ExpandedStacksWidget.calculate_height_for_rows(num_rows)
                            widget.setFixedHeight(height)
    
    def _apply_geometry_animation(
        self,
        current_geometry: QRect,
        target_geometry: QRect,
        animation_attr: str
    ) -> None:
        """Apply smooth geometry animation to window."""
        # Detener animación anterior si existe
        current_animation = getattr(self, animation_attr, None)
        if current_animation:
            current_animation.stop()
            # Desconectar señal finished anterior si existe
            try:
                current_animation.finished.disconnect(self._force_grid_relayout)
            except (TypeError, RuntimeError):
                # No hay conexión o ya fue eliminada - ignorar
                pass
            setattr(self, animation_attr, None)
            
            # Si se detuvo una animación de altura, restaurar estado del grid
            if animation_attr == '_height_animation':
                self._height_animation_in_progress = False
                if self._desktop_container and hasattr(self._desktop_container, '_grid_view'):
                    grid_view = self._desktop_container._grid_view
                    if grid_view and hasattr(grid_view, '_content_widget'):
                        grid_view._content_widget.setUpdatesEnabled(True)
        
        # Crear nueva animación
        animation = QPropertyAnimation(self, b"geometry", self)
        animation.setDuration(self.ANIMATION_DURATION_MS)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.setStartValue(current_geometry)
        animation.setEndValue(target_geometry)
        
        # Conectar señal finished para forzar relayout al finalizar animación
        # Solo para animaciones de altura (donde el grid puede quedar mal posicionado)
        if animation_attr == '_height_animation':
            animation.finished.connect(self._force_grid_relayout)
        
        animation.start()
        
        setattr(self, animation_attr, animation)
    
    def _apply_height_animation(self, current_geometry: QRect, target_height: int, target_y: int) -> None:
        """Apply smooth height animation to window."""
        target_geometry = QRect(
            current_geometry.x(), target_y,
            current_geometry.width(), target_height
        )
        self._apply_geometry_animation(current_geometry, target_geometry, '_height_animation')
    
    def _adjust_window_width(self, stacks_count: int) -> None:
        """Adjust window width based on number of stacks."""
        target_width = self._calculate_target_width(stacks_count)
        current_geometry = self.geometry()
        
        if current_geometry.width() == target_width:
            return
        
        screen = self.screen().availableGeometry()
        new_x = (screen.width() - target_width) // 2
        current_height = current_geometry.height()
        
        self._apply_width_animation(current_geometry, target_width, new_x, current_height)
    
    def _calculate_target_width(self, stacks_count: int) -> int:
        """Calculate target width for dock window based on stacks count."""
        if stacks_count == 0:
            return self.DEFAULT_WINDOW_WIDTH
        
        # Márgenes: main_layout + central_internal_layout + grid_layout
        layout_margins = (self.MAIN_LAYOUT_MARGIN * 2) + (self.CENTRAL_LAYOUT_MARGIN * 2)
        grid_margins = self.GRID_LAYOUT_LEFT_MARGIN + self.GRID_LAYOUT_RIGHT_MARGIN
        total_margins = layout_margins + grid_margins
        
        stacks_width = stacks_count * self.STACK_TILE_WIDTH
        # Spacing: entre escritorio-ajustes, ajustes-separador, separador-primer stack, entre stacks
        # A la izquierda: después del separador hay spacing antes del primer stack
        # A la derecha: el margin derecho del grid proporciona el espacio simétrico
        # Total spacing: 3 espacios fijos + (stacks_count - 1) entre stacks = stacks_count + 2
        total_spacing = (stacks_count + 2) * self.STACK_SPACING
        
        return (self.DESKTOP_TILE_WIDTH + self.SETTINGS_TILE_WIDTH + self.SEPARATOR_WIDTH + 
                stacks_width + total_spacing + total_margins)
    
    def _apply_width_animation(self, current_geometry: QRect, target_width: int, new_x: int, current_height: int) -> None:
        """Apply smooth width animation to window."""
        target_geometry = QRect(
            new_x, current_geometry.y(),
            target_width, current_height
        )
        self._apply_geometry_animation(current_geometry, target_geometry, '_width_animation')
    
    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts for preview."""
        self._preview_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self._preview_shortcut.activated.connect(self._open_quick_preview)
    
    def _enable_preview_shortcut(self, enabled: bool) -> None:
        """Habilitar/deshabilitar shortcut de preview de forma segura."""
        if hasattr(self, '_preview_shortcut') and self._preview_shortcut:
            self._preview_shortcut.setEnabled(enabled)
    
    def _open_quick_preview(self) -> None:
        """Open quick preview for selected files."""
        logger.debug("_open_quick_preview: STARTED")
        try:
            # Si hay un preview abierto, cerrarlo (toggle behavior)
            try:
                if self._current_preview_window and self._current_preview_window.isVisible():
                    logger.debug("_open_quick_preview: Preview already open, closing it (toggle)")
                    self._current_preview_window.close()
                    self._current_preview_window = None
                    self._enable_preview_shortcut(True)
                    return  # Solo cerrar, no abrir otro
            except RuntimeError:
                # Objeto siendo destruido, limpiar referencia y continuar
                self._current_preview_window = None
                self._enable_preview_shortcut(True)
            
            # Obtener archivos seleccionados
            if not self._desktop_container:
                logger.warning("_open_quick_preview: No desktop_container available")
                return
            
            selected_files = get_selected_files(self._desktop_container)
            logger.debug(f"_open_quick_preview: Selected files count={len(selected_files) if selected_files else 0}")
            
            if not selected_files:
                logger.debug("_open_quick_preview: No files selected")
                return
            
            # Filtrar archivos previewables
            previewable_files = filter_previewable_files(selected_files)
            logger.debug(f"_open_quick_preview: Previewable files count={len(previewable_files) if previewable_files else 0}")
            
            if not previewable_files:
                logger.debug("_open_quick_preview: No previewable files")
                return
            
            # Cerrar cualquier preview abierto en MainWindow para evitar conflictos
            from app.ui.windows.main_window import MainWindow
            close_other_window_preview(self, MainWindow)
            
            # Crear y mostrar preview window
            logger.debug(f"_open_quick_preview: Creating QuickPreviewWindow with {len(previewable_files)} files")
            self._current_preview_window = QuickPreviewWindow(
                self._preview_service,
                file_paths=previewable_files,
                start_index=0,
                parent=self
            )
            self._enable_preview_shortcut(False)
            logger.debug("_open_quick_preview: QuickPreviewWindow created, showing...")
            self._current_preview_window.show()
            # Conectar señal closed para rehabilitar shortcut cuando preview se cierre
            self._current_preview_window.closed.connect(self._on_preview_closed)
            logger.debug("_open_quick_preview: QuickPreviewWindow shown")
        except Exception as e:
            logger.error(f"_open_quick_preview: Error opening preview: {e}", exc_info=True)
    
    def _on_preview_closed(self) -> None:
        """Rehabilitar shortcut cuando preview se cierra."""
        self._enable_preview_shortcut(True)
        self._current_preview_window = None
        # Reactivar foco en DesktopWindow para que funcione el próximo shortcut
        self.activateWindow()
        self.setFocus()
    
    def _open_file(self, file_path: str) -> None:
        """Open file with default system application or preview if previewable."""
        logger.debug(f"_open_file: file_path={file_path}")
        
        # Verificar si el archivo está en un stack (si está en un stack, abrir con sistema)
        # Si no está en un stack y es previewable, abrir preview
        if not self._desktop_container:
            logger.debug("_open_file: No desktop_container, opening with system")
            if os.path.exists(file_path):
                url = QUrl.fromLocalFile(file_path)
                QDesktopServices.openUrl(url)
            return
        
        # Verificar si es previewable
        previewable_files = filter_previewable_files([file_path])
        if previewable_files and file_path in previewable_files:
            logger.debug(f"_open_file: File is previewable, opening preview")
            # Cerrar preview anterior si existe
            if self._current_preview_window:
                self._current_preview_window.close()
                self._current_preview_window = None
            
            # Crear y mostrar preview window
            if not self._preview_service:
                logger.warning("_open_file: No preview_service available")
                if os.path.exists(file_path):
                    url = QUrl.fromLocalFile(file_path)
                    QDesktopServices.openUrl(url)
                return
            
            self._current_preview_window = QuickPreviewWindow(
                self._preview_service,
                file_path=file_path
            )
            self._current_preview_window.show()
        else:
            logger.debug(f"_open_file: File not previewable or in stack, opening with system")
            if os.path.exists(file_path):
                url = QUrl.fromLocalFile(file_path)
                QDesktopServices.openUrl(url)
    
    def _handle_drag_event(
        self, 
        event: QDragEnterEvent | QDragMoveEvent | QDropEvent, 
        is_strict: bool = False
    ) -> bool:
        """
        Handle common drag event logic and propagate to FileViewContainer.
        
        Args:
            event: Drag event (enter, move, or drop)
            is_strict: If True, validate strictly (for drop). If False, be permissive (for enter/move).
        
        Returns:
            True if event was handled, False otherwise.
        """
        mime_data = event.mimeData()
        
        # Opción A: dragEnter y dragMove permisivos (feedback positivo)
        # Validación estricta solo en drop
        if is_strict:
            # Validación estricta para drop: debe tener URLs y container debe existir
            if not mime_data.hasUrls():
                event.ignore()
                return False
            
            if not self._desktop_container:
                event.ignore()
                return False
        else:
            # Permisivo para enter/move: aceptar si tiene URLs (feedback positivo)
            if not mime_data.hasUrls():
                event.ignore()
                return False
        
        # Aceptar el evento para que Windows sepa que esta ventana acepta drops
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        
        # Propagar al FileViewContainer si existe
        if self._desktop_container:
            if isinstance(event, QDragEnterEvent):
                self._desktop_container.dragEnterEvent(event)
            elif isinstance(event, QDragMoveEvent):
                self._desktop_container.dragMoveEvent(event)
            else:  # QDropEvent
                self._desktop_container.dropEvent(event)
            return True
        
        return False
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Capture drag enter events and propagate to FileViewContainer (permissive)."""
        self._handle_drag_event(event, is_strict=False)
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Capture drag move events and propagate to FileViewContainer (permissive)."""
        self._handle_drag_event(event, is_strict=False)
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Capture drop events and propagate to FileViewContainer (strict validation)."""
        if not self._handle_drag_event(event, is_strict=True):
            event.ignore()
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Activar ventana y dar foco al hacer clic para que funcionen los shortcuts."""
        self.activateWindow()
        self.setFocus()
        super().mousePressEvent(event)
    
    
