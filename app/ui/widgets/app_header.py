"""AppHeader - Header estilo Finder con controles por defecto.

Contiene navegación, cambio de vista (Grid/Lista), búsqueda y estados.
Reutiliza la lógica existente conectando señales al FileViewContainer.
Soporta modo de personalización estilo Finder con drag & drop.
"""

from typing import Optional, Dict, List, Any
import os
import json

from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QMessageBox
)

from app.ui.widgets.toolbar_navigation_buttons import create_navigation_buttons
from app.ui.widgets.toolbar_button_styles import get_view_button_style
from app.services.header_customization_service import HeaderCustomizationService
from app.ui.widgets.header_customization_palette import HeaderCustomizationPalette


class AppHeader(QWidget):
    """Barra superior de aplicación con controles estándares de Finder."""

    # Señales para reutilizar la lógica existente en FileViewContainer
    navigation_back = Signal()
    navigation_forward = Signal()
    state_button_clicked = Signal(str)  # Emite constante de estado o None
    search_changed = Signal(str)        # Cambio incremental del campo búsqueda
    search_submitted = Signal(str)      # Enter en el campo búsqueda

    # MIME type para drag & drop
    MIME_TYPE = "application/x-header-control"

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._back_button: QPushButton | None = None
        self._forward_button: QPushButton | None = None
        self._grid_button: QPushButton | None = None
        self._list_button: QPushButton | None = None
        self._search: QLineEdit | None = None
        self._state_button: QPushButton | None = None
        self._workspace_label: QLabel | None = None
        
        # Modo personalización
        self._customization_mode = False
        self._original_height: int = 56
        self._signal_states: Dict[int, bool] = {}
        self._control_instances: Dict[str, QWidget] = {}
        self._removed_widgets: List[tuple[str, QWidget]] = []
        self._current_items: List[str] = []
        self._customization_palette: Optional[HeaderCustomizationPalette] = None
        self._customize_button: Optional[QPushButton] = None
        self._done_button: Optional[QPushButton] = None
        
        # Servicio de personalización
        self._service = HeaderCustomizationService()
        
        # Layout principal
        self._layout: QHBoxLayout | None = None
        
        self._setup_ui()
        self._load_configuration()

    def _setup_ui(self) -> None:
        """Construir header con controles por defecto y nombre de workspace."""
        # Altura cómoda para controles y búsqueda
        self.setFixedHeight(56)
        self._original_height = 56
        
        # Estilo sobrio y transparente para integrarse con WindowHeader
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.02);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QLabel {
                color: rgba(255, 255, 255, 0.68);
                font-size: 12px;
                padding: 0px 12px;
            }
            QLineEdit {
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 6px;
                padding: 6px 10px;
                color: rgba(255,255,255,0.88);
                selection-background-color: rgba(128,180,255,0.35);
            }
        """)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 0, 12, 0)
        self._layout.setSpacing(8)

        # Navegación (Atrás / Adelante) — reutiliza helpers existentes
        self._back_button, self._forward_button = create_navigation_buttons(self)
        self._back_button.clicked.connect(self.navigation_back.emit)
        self._forward_button.clicked.connect(self.navigation_forward.emit)
        self._control_instances["back"] = self._back_button
        self._control_instances["forward"] = self._forward_button
        self._layout.addWidget(self._back_button, 0)
        self._layout.addWidget(self._forward_button, 0)

        # Separador pequeño (espaciado)
        self._layout.addSpacing(8)

        # Vista (Grid / Lista)
        self._grid_button = QPushButton("Grid", self)
        self._grid_button.setCheckable(True)
        self._grid_button.setChecked(True)
        self._grid_button.setFixedHeight(32)
        self._grid_button.setStyleSheet(get_view_button_style(True))
        self._layout.addWidget(self._grid_button, 0)

        self._list_button = QPushButton("List", self)
        self._list_button.setCheckable(True)
        self._list_button.setFixedHeight(32)
        self._list_button.setStyleSheet(get_view_button_style(False))
        self._layout.addWidget(self._list_button, 0)
        
        # Guardar referencia al grupo de vista
        self._control_instances["view"] = self._grid_button  # Usar grid como referencia

        # Espacio flexible
        self._layout.addStretch(1)

        # Búsqueda (campo de texto)
        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Buscar")
        self._search.returnPressed.connect(lambda: self.search_submitted.emit(self._search.text()))
        self._search.textChanged.connect(self.search_changed.emit)
        self._control_instances["search"] = self._search
        self._layout.addWidget(self._search, 0)

        # Etiquetas/Estados: botón único con menú contextual
        self._state_button = QPushButton("Estados", self)
        self._state_button.setFixedHeight(32)
        self._attach_state_menu(self._state_button)
        self._control_instances["states"] = self._state_button
        self._layout.addWidget(self._state_button, 0)

        # Nombre de workspace a la derecha (indicación del foco activo)
        self._workspace_label = QLabel("", self)
        self._layout.addWidget(self._workspace_label, 0)
        
        # Botón Personalizar (siempre visible)
        self._customize_button = QPushButton("⚙️", self)
        self._customize_button.setFixedSize(32, 32)
        self._customize_button.setToolTip("Personalizar header")
        self._customize_button.clicked.connect(self._enter_customization_mode)
        self._layout.addWidget(self._customize_button, 0)
        
        # Botón Listo (solo visible en modo personalización)
        self._done_button = QPushButton("Listo", self)
        self._done_button.setFixedHeight(32)
        self._done_button.setVisible(False)
        self._done_button.clicked.connect(self._exit_customization_mode)
        # No añadir al layout todavía, se añadirá cuando entre en modo personalización
        
        # Configurar drag & drop (inicialmente desactivado)
        self.setAcceptDrops(False)

    def _load_configuration(self) -> None:
        """Cargar configuración guardada y aplicarla."""
        config = self._service.load_header_config()
        self._current_items = config.get("items", [])
        self._apply_configuration(self._current_items)

    def _apply_configuration(self, items: List[str]) -> None:
        """
        Aplicar configuración de controles al header.
        
        Args:
            items: Lista de IDs de controles en el orden deseado.
        """
        # Guardar widgets especiales que no deben removerse
        special_widgets = []
        if self._workspace_label:
            special_widgets.append(self._workspace_label)
        if self._customize_button:
            special_widgets.append(self._customize_button)
        if self._done_button:
            special_widgets.append(self._done_button)
        
        # Limpiar layout actual (sin destruir widgets)
        widgets_to_remove = []
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget not in special_widgets:
                    widgets_to_remove.append(widget)
        
        for widget in widgets_to_remove:
            self._layout.removeWidget(widget)
            widget.hide()
        
        # Reconstruir layout según configuración
        for item_id in items:
            if item_id == "separator":
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setStyleSheet("background-color: rgba(255,255,255,0.1); max-width: 1px;")
                separator.setFixedWidth(1)
                separator.setFixedHeight(32)
                self._layout.addWidget(separator, 0)
            elif item_id == "flexible_space":
                self._layout.addStretch(1)
            else:
                widget = self._control_instances.get(item_id)
                if widget:
                    widget.show()
                    self._layout.addWidget(widget, 0)
        
        # Añadir workspace label y botones al final
        if self._workspace_label:
            self._layout.addWidget(self._workspace_label, 0)
        if self._done_button and self._done_button.isVisible():
            self._layout.addWidget(self._done_button, 0)
        if self._customize_button and self._customize_button.isVisible():
            self._layout.addWidget(self._customize_button, 0)

    def _enter_customization_mode(self) -> None:
        """Entrar en modo personalización."""
        if self._customization_mode:
            return
        
        self._customization_mode = True
        
        # Guardar altura original
        self._original_height = self.height()
        self.setFixedHeight(self._original_height)
        
        # Bloquear señales de todos los widgets
        self._signal_states = {}
        all_widgets = [
            self._back_button, self._forward_button, self._grid_button,
            self._list_button, self._search, self._state_button
        ]
        for widget in all_widgets:
            if widget:
                self._signal_states[id(widget)] = widget.signalsBlocked()
                widget.blockSignals(True)
        
        # Activar drag & drop
        self.setAcceptDrops(True)
        
        # Mostrar botón Listo y ocultar Personalizar
        if self._done_button:
            self._done_button.setVisible(True)
            # Añadir al layout si no está ya
            if self._layout.indexOf(self._done_button) == -1:
                self._layout.addWidget(self._done_button, 0)
        if self._customize_button:
            self._customize_button.setVisible(False)
        
        # Aplicar estilo visual de personalización
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.02);
                border: 2px dashed rgba(128, 180, 255, 0.6);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QLabel {
                color: rgba(255, 255, 255, 0.68);
                font-size: 12px;
                padding: 0px 12px;
            }
            QLineEdit {
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 6px;
                padding: 6px 10px;
                color: rgba(255,255,255,0.88);
                selection-background-color: rgba(128,180,255,0.35);
            }
        """)
        
        # Mostrar paleta flotante
        self._show_customization_palette()
        
        # Hacer widgets arrastrables
        self._setup_draggable_widgets()

    def _exit_customization_mode(self) -> None:
        """Salir del modo personalización y guardar configuración."""
        if not self._customization_mode:
            return
        
        # Guardar configuración
        config = {
            "items": self._current_items.copy(),
            "version": 1
        }
        self._service.save_header_config(config)
        
        # Aplicar cambios al layout
        self._apply_configuration(self._current_items)
        
        # Restaurar señales
        all_widgets = [
            self._back_button, self._forward_button, self._grid_button,
            self._list_button, self._search, self._state_button
        ]
        for widget in all_widgets:
            if widget:
                widget.blockSignals(self._signal_states.get(id(widget), False))
        self._signal_states.clear()
        
        # Desactivar drag & drop
        self.setAcceptDrops(False)
        
        # Ocultar botón Listo y mostrar Personalizar
        if self._done_button:
            self._done_button.setVisible(False)
            # Remover del layout
            self._layout.removeWidget(self._done_button)
        if self._customize_button:
            self._customize_button.setVisible(True)
        
        # Restaurar estilo normal
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.02);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QLabel {
                color: rgba(255, 255, 255, 0.68);
                font-size: 12px;
                padding: 0px 12px;
            }
            QLineEdit {
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 6px;
                padding: 6px 10px;
                color: rgba(255,255,255,0.88);
                selection-background-color: rgba(128,180,255,0.35);
            }
        """)
        
        # Ocultar paleta
        if self._customization_palette:
            self._customization_palette.hide()
            self._customization_palette = None
        
        self._customization_mode = False
        
        # Recalcular estados después de restaurar
        self._update_button_states()

    def _show_customization_palette(self) -> None:
        """Mostrar paleta de personalización flotante."""
        if self._customization_palette:
            return
        
        self._customization_palette = HeaderCustomizationPalette(self.window())
        palette = self._customization_palette
        
        # Posicionar paleta cerca del header
        header_pos = self.mapToGlobal(QPoint(0, 0))
        palette.move(header_pos.x() + self.width() - palette.width() - 20, header_pos.y() + self.height() + 10)
        palette.show()

    def _setup_draggable_widgets(self) -> None:
        """Configurar widgets del header para ser arrastrables."""
        for control_id, widget in self._control_instances.items():
            if widget and control_id in self._current_items:
                widget.setCursor(Qt.CursorShape.OpenHandCursor)
                # Guardar referencia al control_id en el widget
                widget.setProperty("control_id", control_id)

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter event."""
        if not self._customization_mode:
            event.ignore()
            return
        
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        """Handle drag move event."""
        if not self._customization_mode:
            event.ignore()
            return
        
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """Handle drop event."""
        if not self._customization_mode:
            event.ignore()
            return
        
        mime_data = event.mimeData()
        if not mime_data.hasFormat(self.MIME_TYPE):
            event.ignore()
            return
        
        # Verificar si el drop está dentro del header
        drop_pos = event.pos()
        if not self.rect().contains(drop_pos):
            # Drop fuera del header = eliminar control
            try:
                data = json.loads(mime_data.data(self.MIME_TYPE).data().decode('utf-8'))
                control_id = data.get("type")
                source = data.get("source", "palette")
                
                if source == "header" and control_id:
                    self._remove_control(control_id)
                
                event.acceptProposedAction()
            except (json.JSONDecodeError, KeyError, ValueError):
                event.ignore()
            return
        
        try:
            data = json.loads(mime_data.data(self.MIME_TYPE).data().decode('utf-8'))
            control_id = data.get("type")
            source = data.get("source", "palette")
            
            if source == "palette":
                # Añadir nuevo control desde paleta
                self._add_control_from_palette(control_id, drop_pos)
            elif source == "header":
                # Reordenar control existente
                self._reorder_control(control_id, drop_pos)
            
            event.acceptProposedAction()
        except (json.JSONDecodeError, KeyError, ValueError):
            event.ignore()

    def _add_control_from_palette(self, control_id: str, drop_pos: QPoint) -> None:
        """
        Añadir control desde paleta al header.
        
        Args:
            control_id: ID del control a añadir.
            drop_pos: Posición donde se soltó el control.
        """
        # Validar que el control no esté ya presente
        if control_id in self._current_items:
            return
        
        # Validar que sea un control válido
        if control_id not in self._service.get_valid_control_ids():
            return
        
        # Encontrar posición de inserción basada en drop_pos
        insert_index = self._find_insert_index(drop_pos)
        
        # Insertar en la posición calculada
        self._current_items.insert(insert_index, control_id)
        
        # Aplicar cambios visualmente (sin salir del modo)
        # Durante personalización, solo actualizar visualmente sin cambiar layout real
        self._update_layout_during_customization()
        self._setup_draggable_widgets()

    def _reorder_control(self, control_id: str, drop_pos: QPoint) -> None:
        """
        Reordenar control existente dentro del header.
        
        Args:
            control_id: ID del control a reordenar.
            drop_pos: Posición donde se soltó el control.
        """
        if control_id not in self._current_items:
            return
        
        # Remover de posición actual
        self._current_items.remove(control_id)
        
        # Encontrar nueva posición
        insert_index = self._find_insert_index(drop_pos)
        
        # Insertar en nueva posición
        self._current_items.insert(insert_index, control_id)
        
        # Aplicar cambios visualmente
        self._update_layout_during_customization()
        self._setup_draggable_widgets()

    def _find_insert_index(self, pos: QPoint) -> int:
        """
        Encontrar índice de inserción basado en posición del mouse.
        
        Args:
            pos: Posición del mouse en coordenadas del widget.
        
        Returns:
            Índice donde insertar el control.
        """
        # Calcular posición relativa en el layout
        x = pos.x()
        margin = self._layout.contentsMargins().left()
        
        # Recorrer items del layout para encontrar posición
        current_x = margin
        insert_index = 0
        
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            if not item:
                continue
            
            widget = item.widget()
            if not widget or widget == self._workspace_label or widget == self._customize_button or widget == self._done_button:
                continue
            
            # Calcular posición del widget
            widget_x = current_x
            widget_width = widget.width() if widget.isVisible() else 0
            
            # Si el mouse está antes de este widget, insertar aquí
            if x < widget_x + widget_width / 2:
                return insert_index
            
            # Si el widget es visible y está en current_items, incrementar índice
            control_id = widget.property("control_id")
            if control_id and control_id in self._current_items:
                insert_index += 1
            
            current_x += widget_width + self._layout.spacing()
        
        # Si llegamos aquí, insertar al final
        return len(self._current_items)
    
    def _remove_control(self, control_id: str) -> None:
        """
        Remover control del header.
        
        Args:
            control_id: ID del control a remover.
        """
        # Validar que se puede remover
        can_remove, error_msg = self._service.can_remove_control(control_id, self._current_items)
        if not can_remove:
            # Mostrar mensaje de error si no se puede remover
            if error_msg:
                QMessageBox.warning(self, "No se puede eliminar", error_msg)
            return
        
        # Remover de la lista
        if control_id in self._current_items:
            self._current_items.remove(control_id)
        
        # Aplicar cambios visualmente
        self._update_layout_during_customization()
        self._setup_draggable_widgets()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press to start drag for header controls."""
        if not self._customization_mode:
            super().mousePressEvent(event)
            return
        
        # Buscar widget bajo el cursor
        widget = self.childAt(event.pos())
        if not widget:
            super().mousePressEvent(event)
            return
        
        # Buscar control_id en el widget o sus padres
        control_id = None
        current = widget
        while current:
            control_id = current.property("control_id")
            if control_id:
                break
            current = current.parent()
        
        if not control_id or control_id not in self._current_items:
            super().mousePressEvent(event)
            return
        
        # Iniciar drag
        mime_data = QMimeData()
        drag_data = {
            "type": control_id,
            "source": "header"
        }
        mime_data.setData(self.MIME_TYPE, json.dumps(drag_data).encode('utf-8'))
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(widget.grab())
        drag.setHotSpot(event.pos() - widget.pos())
        
        # Ejecutar drag
        drag.exec(Qt.DropAction.MoveAction)

    def closeEvent(self, event) -> None:
        """Handle close event - exit customization mode if active."""
        if self._customization_mode:
            # Preguntar si guardar cambios
            reply = QMessageBox.question(
                self, "Personalización",
                "¿Guardar cambios en el header?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._exit_customization_mode()
            elif reply == QMessageBox.StandardButton.No:
                # Descartar cambios y restaurar configuración anterior
                self._load_configuration()
                self._customization_mode = False
                if self._customization_palette:
                    self._customization_palette.hide()
                    self._customization_palette = None
            else:
                event.ignore()
                return
        
        super().closeEvent(event)

    def update_workspace(self, workspace_name_or_path: Optional[str]) -> None:
        """
        Update displayed workspace name.
        
        Accepts either a workspace name (string) or a folder path.
        If it's a path, extracts the folder name.
        """
        if not self._workspace_label:
            return
            
        if not workspace_name_or_path:
            self._workspace_label.setText("")
            return

        # Si parece un path (contiene separadores de directorio), extraer nombre
        if os.sep in workspace_name_or_path or (os.altsep and os.altsep in workspace_name_or_path):
            workspace_name = os.path.basename(workspace_name_or_path)
            if not workspace_name:
                # Si es raíz de unidad (ej: C:\), usar el path completo
                workspace_name = workspace_name_or_path.rstrip(os.sep)
        else:
            # Es un nombre de workspace directamente
            workspace_name = workspace_name_or_path
        
        self._workspace_label.setText(workspace_name)

    # Métodos de compatibilidad para FileViewContainer
    def get_grid_button(self) -> QPushButton:
        """Exponer botón Grid para conectar acciones de vista."""
        return self._grid_button

    def get_list_button(self) -> QPushButton:
        """Exponer botón Lista para conectar acciones de vista."""
        return self._list_button

    def set_nav_enabled(self, can_back: bool, can_forward: bool) -> None:
        """Activar/desactivar navegación según historial del TabManager."""
        if self._back_button:
            self._back_button.setEnabled(can_back)
        if self._forward_button:
            self._forward_button.setEnabled(can_forward)

    def update_button_styles(self, grid_checked: bool) -> None:
        """Actualizar estilos de botones de vista según selección actual."""
        if self._grid_button and self._list_button:
            self._grid_button.setStyleSheet(get_view_button_style(grid_checked))
            self._list_button.setStyleSheet(get_view_button_style(not grid_checked))

    def _update_layout_during_customization(self) -> None:
        """Actualizar layout visualmente durante personalización."""
        # Durante personalización, reconstruir layout según current_items
        # pero manteniendo altura fija y sin ejecutar acciones
        # Guardar widgets especiales
        special_widgets = []
        if self._workspace_label:
            special_widgets.append(self._workspace_label)
        if self._customize_button:
            special_widgets.append(self._customize_button)
        if self._done_button:
            special_widgets.append(self._done_button)
        
        # Remover widgets no especiales del layout
        widgets_to_remove = []
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget not in special_widgets:
                    widgets_to_remove.append(widget)
        
        for widget in widgets_to_remove:
            self._layout.removeWidget(widget)
            widget.hide()
        
        # Reconstruir según current_items
        for item_id in self._current_items:
            if item_id == "separator":
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setStyleSheet("background-color: rgba(255,255,255,0.1); max-width: 1px;")
                separator.setFixedWidth(1)
                separator.setFixedHeight(32)
                self._layout.addWidget(separator, 0)
            elif item_id == "flexible_space":
                self._layout.addStretch(1)
            else:
                widget = self._control_instances.get(item_id)
                if widget:
                    widget.show()
                    self._layout.addWidget(widget, 0)
        
        # Añadir widgets especiales al final
        if self._workspace_label:
            self._layout.addWidget(self._workspace_label, 0)
        if self._done_button and self._done_button.isVisible():
            self._layout.addWidget(self._done_button, 0)
        if self._customize_button and self._customize_button.isVisible():
            self._layout.addWidget(self._customize_button, 0)
    
    def _update_button_states(self) -> None:
        """Actualizar estados de botones después de salir del modo personalización."""
        # Este método puede ser extendido para recalcular estados
        # Por ahora, solo asegurar que los botones estén en estado correcto
        pass

    def _attach_state_menu(self, button: QPushButton) -> None:
        """Crear menú contextual de estados con las opciones existentes.
        
        Mantiene la lógica: emite `state_button_clicked` con la constante de estado
        o `None` para limpiar. """
        from PySide6.QtWidgets import QMenu
        menu = QMenu(button)
        try:
            from app.ui.widgets.state_badge_widget import (
                STATE_CORRECTED,
                STATE_DELIVERED,
                STATE_PENDING,
                STATE_REVIEW,
            )
        except ImportError:
            # Si no hay estados definidos aún, no adjuntar menú
            return
        actions = [
            ("Pendiente", STATE_PENDING),
            ("Entregado", STATE_DELIVERED),
            ("Corregido", STATE_CORRECTED),
            ("Revisar", STATE_REVIEW),
        ]
        for label, state in actions:
            act = menu.addAction(label)
            act.triggered.connect(lambda checked=False, s=state: self.state_button_clicked.emit(s))
        menu.addSeparator()
        clear = menu.addAction("Quitar estado")
        clear.triggered.connect(lambda: self.state_button_clicked.emit(None))
        button.setMenu(menu)
