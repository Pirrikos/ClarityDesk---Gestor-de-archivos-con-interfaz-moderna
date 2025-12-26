# Orden de Creación de Tiles y Layout - MainWindow

Documento que describe el flujo completo de creación de tiles y cálculo del layout cuando se inicia por primera vez la MainWindow.

---

## 1. Inicio de la Aplicación

**Archivo:** `main.py`

```python
main() → QApplication(sys.argv)
       → DesktopWindow() (auto-start)
       → MainWindow() (cuando usuario lo solicita)
```

**Nota:** MainWindow se crea cuando el usuario lo solicita, no al inicio.

---

## 2. Creación de MainWindow

**Archivo:** `app/ui/windows/main_window.py`

### 2.1. `MainWindow.__init__()` (línea 40)

```
1. super().__init__(parent)
2. Configuración de ventana (flags, atributos, tamaño mínimo)
3. Inicialización de servicios:
   - _tab_manager (TabManager)
   - _workspace_manager (WorkspaceManager)
   - _icon_service (IconService)
   - _preview_service (PreviewPdfService)
   - _state_label_manager (StateLabelManager)
4. _setup_ui() → Crea FileViewContainer
5. _connect_signals()
6. _setup_shortcuts()
7. _load_workspace_state()
```

### 2.2. `_setup_ui()` (línea 109)

```
setup_ui() → Crea:
  - _file_view_container (FileViewContainer)
  - _sidebar
  - _window_header
  - _app_header
  - _secondary_header
  - _workspace_selector
  - _history_panel
  - _content_splitter
  - _current_file_box_panel
```

---

## 3. Creación de FileViewContainer

**Archivo:** `app/ui/widgets/file_view_container.py`

### 3.1. `FileViewContainer.__init__()` (línea 71)

```
1. super().__init__(parent)
2. Inicialización de servicios:
   - _tab_manager
   - _icon_service (IconService)
   - _files_manager (FilesManager)
   - _state_manager (FileStateManager)
   - _handlers (FileViewHandlers)
3. setup_ui(self) → Crea FileGridView y FileListView
4. connect_tab_signals(self, tab_manager)
5. _setup_selection_timer()
6. ⚠️ WARM-UP DE PRIMER PAINT:
   - self.setVisible(False)  (línea 102)
   - QTimer.singleShot(0, self._activate_first_paint)  (línea 103)
7. update_files(self)  (línea 105) → Llama a _grid_view.update_files()
8. update_nav_buttons_state(self)
```

**Estado:** FileViewContainer está invisible durante la construcción inicial.

---

## 4. Creación de FileGridView

**Archivo:** `app/ui/widgets/file_grid_view.py`

### 4.1. `FileGridView.__init__()` (línea 60)

```
1. super().__init__(parent)
2. Inicialización de variables:
   - _files = []
   - _stacks = []
   - _icon_service
   - _tab_manager
   - _selected_tiles = set()
   - _expanded_stacks = {}
   - _state_manager
   - _is_desktop_window = False
   - _cached_columns = None  ⚠️ Sin columnas cacheadas aún
   - _cached_width = 0
   - _grid_state = {}
   - _tile_manager = None
   - _previous_files = None
3. _setup_ui()  (línea 110)
```

**Estado:** FileGridView aún no tiene tamaño real (`width() == 0`).

### 4.2. `_setup_ui()` (línea 112)

```
1. Configuración de estilos
2. Creación de layout principal (QVBoxLayout)
3. Creación de scroll area (create_scroll_area)
4. Creación de _content_widget (GridContentWidget)
5. Configuración de scroll area
6. Creación de _grid_layout (setup_grid_layout)  (línea 129)
7. Inicialización de TileManager  (línea 132-138):
   - tile_manager = TileManager(
       view=self,
       icon_service=_icon_service,
       state_manager=_state_manager,
       grid_layout=_grid_layout,
       content_widget=_content_widget
     )
8. scroll.setWidget(_content_widget)
9. layout.addWidget(scroll)
```

**Estado:** Layout creado pero widget aún sin tamaño real.

---

## 5. Primera Actualización de Archivos

**Archivo:** `app/ui/widgets/file_view_sync.py`

### 5.1. `update_files(container)` (línea 22)

```
1. Activar top-level detector (workspace switch)
2. Obtener carpeta activa: active_folder = tab_manager.get_active_folder()
3. Obtener archivos: items = tab_manager.get_files(use_stacks=use_stacks)
4. container._grid_view.update_files(items)  (línea 41)
5. container._list_view.update_files(items)
6. Limpiar estados de archivos que ya no existen
```

---

## 6. Actualización de FileGridView

**Archivo:** `app/ui/widgets/file_grid_view.py`

### 6.1. `update_files(file_list)` (línea 156)

```
1. Si file_list contiene FileStack:
   - Guardar expanded_stacks anteriores
   - self._stacks = file_list
   - self._files = []
   - Restaurar expanded_stacks
   - Limpiar cache de categorización
2. Si file_list contiene archivos normales:
   - Si NO es desktop_window:
     * Categorizar archivos: get_categorized_files_with_labels(file_list)
     * Cachear resultado si lista no cambió
   - Si es desktop_window:
     * self._files = file_list (sin categorizar)
   - self._stacks = []
   - self._expanded_stacks = {}
3. Guardar estado anterior: self._previous_files = self._files.copy()
4. self._refresh_tiles()  (línea 194)
```

---

## 7. Refresco de Tiles

**Archivo:** `app/ui/widgets/file_grid_view.py`

### 7.1. `_refresh_tiles()` (línea 197)

```
1. items_to_render = self._stacks if self._stacks else self._files
2. clear_selection(self)
3. Si es desktop_window:
   - build_dock_layout(...)
4. Si NO es desktop_window:
   - build_normal_grid(self, items_to_render, self._grid_layout)  (línea 214)
5. QTimer.singleShot(0, lambda: self._content_widget.adjustSize())
6. QTimer.singleShot(0, lambda: self._content_widget.updateGeometry())
```

---

## 8. Construcción del Layout Normal (Grid)

**Archivo:** `app/ui/widgets/grid_layout_engine.py`

### 8.1. `build_normal_grid(view, items_to_render, grid_layout)` (línea 76)

**PRIMERA LLAMADA (con width() == 0):**

```
1. current_width = view.width()  → Retorna 0 (widget aún sin tamaño)
2. ⚠️ VERIFICACIÓN DE ANCHO VÁLIDO:
   if current_width <= 0:
       return  # Retorna temprano, NO construye layout
```

**Estado:** No se construye nada porque el widget aún no tiene tamaño real.

---

## 9. Activación del Primer Paint

**Archivo:** `app/ui/widgets/file_view_container.py`

### 9.1. `_activate_first_paint()` (línea 109)

```
QTimer.singleShot(0) ejecuta:
  self.setVisible(True)  (línea 111)
```

**Estado:** FileViewContainer ahora es visible.

**Efecto:** Qt calcula el layout y emite `resizeEvent` en FileGridView.

---

## 10. ResizeEvent - Primera Vez con Ancho Válido

**Archivo:** `app/ui/widgets/file_grid_view_events.py`

### 10.1. `resize_event(view, event)` (línea 13)

```
1. view.__class__.__bases__[0].resizeEvent(view, event)
2. Si es desktop_window: return
3. new_width = event.size().width()  → Ahora tiene ancho válido (> 0)
4. new_columns = calculate_columns_for_normal_grid(new_width)
5. cached_columns = getattr(view, '_cached_columns', None)  → None (primera vez)
6. ⚠️ CONSTRUCCIÓN INMEDIATA:
   if cached_columns is None and (view._files or view._stacks):
       view._refresh_tiles()  (línea 39)
       return  # Sin debounce en primera vez
```

**Estado:** Se llama `_refresh_tiles()` inmediatamente porque no hay columnas cacheadas.

---

## 11. Construcción del Layout Normal (Grid) - Segunda Llamada

**Archivo:** `app/ui/widgets/grid_layout_engine.py`

### 11.1. `build_normal_grid(view, items_to_render, grid_layout)` (línea 76)

**SEGUNDA LLAMADA (con width() > 0):**

```
1. current_width = view.width()  → Ahora tiene ancho válido (> 0)
2. if current_width <= 0: return  → NO retorna (ancho válido)
3. _emit_expansion_height(view)
4. setup_normal_grid_config(grid_layout)
5. col_offset = get_col_offset_for_desktop_window(view._is_desktop_window)
6. ⚠️ CÁLCULO DE COLUMNAS:
   if (view._cached_columns is None or 
       view._cached_width is None or 
       abs(current_width - view._cached_width) > 10):
       view._cached_columns = calculate_columns_for_normal_grid(current_width)
       view._cached_width = current_width
7. columns = view._cached_columns
8. ⚠️ VERIFICACIÓN DE COLUMNAS VÁLIDAS:
   if columns is None or columns <= 0:
       return
9. ⚠️ CONVERSIÓN DE ITEMS:
   is_categorized = items_to_render and isinstance(items_to_render[0], tuple)
   Si es categorizado:
     - ordered_ids, header_rows = _items_to_tile_ids_with_headers(items_to_render, columns)
     - new_state_with_headers = _calculate_positions_with_headers(...)
   Si NO es categorizado:
     - ordered_ids = _items_to_tile_ids(items_to_render, view)
     - Calcular posiciones: row = index // columns, col = index % columns
10. ⚠️ CÁLCULO DE DIFFS:
    old_state = getattr(view, '_grid_state', {}) or {}  → {} (primera vez)
    old_ids = set(old_state.keys())  → set() (vacío)
    new_ids = set(new_state_with_headers.keys())
    added = list(new_ids - old_ids)  → Todos los tiles son "added"
    removed = []
    moved = {}
    unchanged = []
11. diff = GridDiff(added=added, removed=[], moved={}, unchanged=[], new_state=...)
12. tile_manager = view._tile_manager
13. ⚠️ CONSTRUCCIÓN MASIVA (con updates deshabilitados):
    content_widget.setUpdatesEnabled(False)
    try:
        ⚠️ AÑADIR HEADERS ANTES DE TILES:
        if is_categorized and header_rows:
            _add_category_headers_at_rows(...)  (línea 170)
        
        ⚠️ APLICAR CAMBIOS INCREMENTALMENTE:
        1. Detach removed + moved  → Nada (primera vez)
        2. Destroy removed  → Nada (primera vez)
        3. Attach unchanged  → Nada (primera vez)
        4. Attach moved  → Nada (primera vez)
        5. ⚠️ CREATE + ATTACH ADDED:
           for tile_id in diff.added:
               tile = tile_manager.get_or_create(tile_id)  → Crea tile
               row, col = diff.new_state[tile_id]
               tile_manager.attach(tile, row, col + col_offset)  → Añade al layout
    finally:
        content_widget.setUpdatesEnabled(True)
14. ⚠️ FORZAR CÁLCULO DEL LAYOUT:
    grid_layout.activate()
    content_widget.updateGeometry()
15. view._grid_state = diff.new_state
```

---

## 12. Creación de Tiles Individuales

**Archivo:** `app/ui/widgets/grid_tile_manager.py`

### 12.1. `get_or_create(tile_id)` → `_create_tile(tile_id)` (línea 171)

```
Si tile_id.startswith("stack:"):
  - Crear FileStackTile
Si NO:
  - Llamar create_file_tile(file_path, ...)
```

---

## 13. Creación de FileTile

**Archivo:** `app/ui/widgets/grid_tile_builder.py`

### 13.1. `create_file_tile(file_path, parent_view, icon_service, state_manager, dock_style)` (línea 21)

```
1. Obtener estado del archivo: state = state_manager.get_file_state(file_path)
2. Crear FileTile:
   tile = FileTile(
       file_path, parent_view, icon_service,
       dock_style=dock_style,
       initial_state=state
   )
3. ⚠️ SOFT REVEAL (si NO es dock_style):
   if not dock_style:
       from app.ui.widgets.file_tile_anim import soft_reveal
       soft_reveal(tile)  (línea 54)
4. return tile
```

---

## 14. Soft Reveal de Tiles

**Archivo:** `app/ui/widgets/file_tile_anim.py`

### 14.1. `soft_reveal(tile)` (línea 10)

```
1. Si tile._dock_style: return
2. ⚠️ CREAR TILE OCULTO:
   tile.setVisible(False)  (línea 22)
3. ⚠️ PROGRAMAR REVELADO:
   QTimer.singleShot(0, lambda: _reveal_with_fade(tile))  (línea 25)
```

**Estado:** Tile está completamente invisible cuando se añade al layout.

### 14.2. `_reveal_with_fade(tile)` (línea 28)

**Ejecutado en siguiente ciclo del event loop:**

```
1. tile.setVisible(True)  (línea 31)
2. tile.setWindowOpacity(0.0)  (línea 32)
3. Crear animación:
   fade_anim = QPropertyAnimation(tile, b"windowOpacity", tile)
   fade_anim.setDuration(100)  # ≤120ms
   fade_anim.setStartValue(0.0)
   fade_anim.setEndValue(1.0)
   fade_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
   fade_anim.start()
```

**Estado:** Tile ahora es visible y se anima la opacidad de 0.0 a 1.0.

---

## 15. Añadir Tile al Layout

**Archivo:** `app/ui/widgets/grid_tile_manager.py`

### 15.1. `attach(tile, row, col)` (línea 84)

```
1. Verificar si tile ya está en layout en esa posición
2. Remover tile de posición anterior si existe
3. Establecer parent: tile.setParent(self._content_widget)
4. ⚠️ AÑADIR AL LAYOUT:
   self._grid_layout.addWidget(tile, row, col)  (línea 114)
```

**Estado:** Tile añadido al layout (invisible con `setVisible(False)`).

---

## 16. Problema Identificado: Salto Visual

### 16.1. Secuencia Problemática

```
1. Tile se crea → soft_reveal() → tile.setVisible(False)
2. Tile se añade al layout mientras está invisible
3. Qt calcula layout con tile invisible → Puede usar tamaño mínimo o cero
4. QTimer.singleShot(0) → _reveal_with_fade() → tile.setVisible(True)
5. Qt recalcula layout con tamaño real del tile → SALTO VISUAL
```

### 16.2. Causa Raíz

**Cuando un widget está completamente invisible (`setVisible(False)`), Qt puede:**
- Ignorarlo en el cálculo del layout
- Usar un tamaño mínimo o cero
- Calcular posiciones incorrectas

**Cuando el widget se hace visible, Qt recalcula el layout con el tamaño real, causando el salto visual de vertical a horizontal.**

---

## 17. Soluciones Implementadas

### 17.1. Verificación de Ancho Válido

```python
# En build_normal_grid()
if current_width <= 0:
    return  # No construir layout hasta tener ancho válido
```

### 17.2. Verificación de Columnas Válidas

```python
# En build_normal_grid()
if columns is None or columns <= 0:
    return  # No construir layout con columnas inválidas
```

### 17.3. Headers Antes de Tiles

```python
# En build_normal_grid()
if is_categorized and header_rows:
    _add_category_headers_at_rows(...)  # Antes de añadir tiles
```

### 17.4. Forzar Cálculo del Layout

```python
# En build_normal_grid()
grid_layout.activate()
content_widget.updateGeometry()
```

### 17.5. Warm-up del Primer Paint

```python
# En FileViewContainer.__init__()
self.setVisible(False)
QTimer.singleShot(0, self._activate_first_paint)
```

---

## 18. Flujo Completo Resumido

```
1. main() → QApplication
2. MainWindow.__init__() → _setup_ui() → FileViewContainer.__init__()
3. FileViewContainer.__init__():
   - setup_ui() → FileGridView.__init__()
   - FileViewContainer.setVisible(False)  ⚠️
   - QTimer.singleShot(0, _activate_first_paint)  ⚠️
   - update_files() → FileGridView.update_files()
4. FileGridView.update_files():
   - Categorizar archivos
   - _refresh_tiles()
5. FileGridView._refresh_tiles():
   - build_normal_grid() (PRIMERA VEZ con width() == 0)
   - Retorna temprano (no construye)
6. QTimer.singleShot(0) → _activate_first_paint():
   - FileViewContainer.setVisible(True)
7. Qt emite resizeEvent:
   - resize_event() detecta cached_columns == None
   - Llama _refresh_tiles() inmediatamente (sin debounce)
8. FileGridView._refresh_tiles():
   - build_normal_grid() (SEGUNDA VEZ con width() > 0)
9. build_normal_grid():
   - Calcula columnas
   - Calcula posiciones
   - Añade headers primero
   - Crea tiles (con soft_reveal → setVisible(False))
   - Añade tiles al layout (invisibles)
   - grid_layout.activate()
   - content_widget.updateGeometry()
10. QTimer.singleShot(0) → _reveal_with_fade():
    - tile.setVisible(True)
    - Animación de opacidad 0.0 → 1.0
```

---

## 19. Puntos Críticos

### 19.1. Timing del Layout

- **Primera llamada:** `build_normal_grid()` con `width() == 0` → Retorna temprano
- **Segunda llamada:** `build_normal_grid()` con `width() > 0` → Construye layout
- **Problema:** Tiles se añaden invisibles, Qt puede calcular layout incorrectamente

### 19.2. Soft Reveal

- **Problema:** `setVisible(False)` hace que Qt ignore el widget en el cálculo del layout
- **Solución propuesta:** Usar `QGraphicsOpacityEffect` en lugar de `setVisible(False)`

### 19.3. Orden de Construcción

- **Headers primero:** Se añaden antes de los tiles para evitar reflow
- **Layout activation:** Se fuerza después de añadir todos los tiles
- **Warm-up:** FileViewContainer se mantiene invisible durante construcción inicial

---

## 20. Conclusión

El salto visual ocurre porque:

1. Los tiles se crean con `setVisible(False)` antes de añadirlos al layout
2. Qt calcula el layout con tiles invisibles (puede usar tamaño mínimo)
3. Cuando los tiles se hacen visibles, Qt recalcula el layout con tamaño real
4. Esto causa el salto visual de disposición vertical a horizontal

**Solución recomendada:** Usar `QGraphicsOpacityEffect` en lugar de `setVisible(False)` para mantener los tiles visibles para Qt pero transparentes visualmente.

