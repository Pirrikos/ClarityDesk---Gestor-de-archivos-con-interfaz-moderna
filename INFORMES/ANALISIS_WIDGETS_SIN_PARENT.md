# Análisis: Widgets creados sin parent

## Objetivo
Detectar widgets que puedan convertirse temporalmente en ventanas top-level, causando flashes visuales al cambiar de workspace o refrescar vistas.

---

## 🔴 CRÍTICOS: Widgets embebidos en tablas/grids

### ✅ CORREGIDO: `app/ui/widgets/list_row_factory.py`
- **Línea 31**: `CustomCheckBox()` → ✅ Ya corregido con parent
- **Línea 44**: `QWidget()` (contenedor) → ✅ Ya corregido con parent
- **Línea 140**: `ListStateCell(state)` → ✅ Ya corregido con parent

### ⚠️ PENDIENTE: `app/ui/widgets/file_tile_setup.py`
- **Línea 47**: `container_widget = QWidget()` 
  - **Uso**: Contenedor embebido en FileTile (grid view)
  - **Problema**: Se crea sin parent, luego se añade al layout
  - **Corrección**: Pasar `tile` como parent: `QWidget(tile)`

- **Línea 79**: `bottom_band = QWidget()`
  - **Uso**: Banda inferior embebida en FileTile (list view)
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `tile` como parent: `QWidget(tile)`

- **Línea 95**: `name_label = QLabel()`
  - **Uso**: Label embebido en FileTile
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `tile` como parent: `QLabel(tile)`

### ⚠️ PENDIENTE: `app/ui/widgets/file_tile_icon.py`
- **Línea 172**: `icon_label = QLabel()`
  - **Uso**: Label de icono embebido en FileTile
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `tile` como parent: `QLabel(tile)`

### ⚠️ PENDIENTE: `app/ui/widgets/file_stack_tile.py`
- **Línea 72**: `container_widget = QWidget()`
  - **Uso**: Contenedor embebido en FileStackTile (grid view)
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

- **Línea 141**: `self._icon_label = QLabel()`
  - **Uso**: Label de icono embebido en FileStackTile
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QLabel(self)`

- **Línea 248**: `name_label = QLabel()`
  - **Uso**: Label de nombre embebido en FileStackTile
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QLabel(self)`

### ⚠️ PENDIENTE: `app/ui/widgets/desktop_stack_tile.py`
- **Línea 67**: `container_widget = QWidget()`
  - **Uso**: Contenedor embebido en DesktopStackTile
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

- **Línea 118**: `self._icon_label = QLabel()`
  - **Uso**: Label de icono embebido
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QLabel(self)`

- **Línea 135**: `name_label = QLabel()`
  - **Uso**: Label de nombre embebido
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QLabel(self)`

### ⚠️ PENDIENTE: `app/ui/widgets/settings_stack_tile.py`
- **Línea 55**: `container_widget = QWidget()`
  - **Uso**: Contenedor embebido en SettingsStackTile
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

- **Línea 106**: `self._icon_label = QLabel()`
  - **Uso**: Label de icono embebido
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QLabel(self)`

- **Línea 123**: `name_label = QLabel()`
  - **Uso**: Label de nombre embebido
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QLabel(self)`

---

## 🟡 MODERADOS: Headers internos y paneles

### ⚠️ PENDIENTE: `app/ui/widgets/file_box_panel.py`
- **Línea 125**: `header_widget = QWidget()`
  - **Uso**: Header interno embebido en FileBoxPanel
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

- **Línea 158**: `body_widget = QWidget()`
  - **Uso**: Body interno embebido en FileBoxPanel
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

### ⚠️ PENDIENTE: `app/ui/widgets/file_box_history_panel.py`
- **Línea 60**: `header_widget = QWidget()`
  - **Uso**: Header interno embebido en FileBoxHistoryPanel
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

- **Línea 85**: `body_widget = QWidget()`
  - **Uso**: Body interno embebido en FileBoxHistoryPanel
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

### ⚠️ PENDIENTE: `app/ui/widgets/workspace_selector.py`
- **Línea 159**: `self._workspace_button = QPushButton()`
  - **Uso**: Botón embebido en WorkspaceSelector
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QPushButton(self)`

- **Línea 171**: `self._focus_button = QPushButton()`
  - **Uso**: Botón embebido en WorkspaceSelector
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QPushButton(self)`

- **Línea 583**: `separator = QWidget()`
  - **Uso**: Separador embebido en WorkspaceSelector
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

### ⚠️ PENDIENTE: `app/ui/widgets/header_customization_palette.py`
- **Línea 105**: `separator = QFrame()`
  - **Uso**: Separador embebido en HeaderCustomizationPalette
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QFrame(self)`

---

## 🟢 BAJOS: Overlays y ventanas (menos críticos)

### ✅ CORRECTO: `app/ui/widgets/badge_overlay_widget.py`
- **Línea 18**: `__init__(self, parent: QWidget = None)` → ✅ Ya recibe parent

### ✅ CORRECTO: `app/ui/widgets/subfolder_overlay.py`
- **Línea 38**: `__init__(self, root_path: str, parent=None)` → ✅ Ya recibe parent

### ⚠️ PENDIENTE: `app/ui/windows/quick_preview_window.py`
- **Línea 125**: `self._image_label = QLabel()`
  - **Uso**: Label embebido en QuickPreviewWindow
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QLabel(self)`

- **Línea 132**: `stack_container = QWidget()`
  - **Uso**: Contenedor embebido en QuickPreviewWindow
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

- **Línea 134**: `content_widget = QWidget()`
  - **Uso**: Widget de contenido embebido
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `stack_container` como parent: `QWidget(stack_container)`

- **Línea 144**: `overlay = QWidget()`
  - **Uso**: Overlay de carga embebido
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `stack_container` como parent: `QWidget(stack_container)`

### ⚠️ PENDIENTE: `app/ui/windows/quick_preview_thumbnails.py`
- **Línea 48**: `self._panel = QWidget()`
  - **Uso**: Panel embebido en QuickPreviewThumbnails
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

- **Línea 65**: `self._container = QWidget()`
  - **Uso**: Contenedor embebido
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self._panel` como parent: `QWidget(self._panel)`

### ⚠️ PENDIENTE: `app/ui/windows/quick_preview_header.py`
- **Línea 39**: `self._header_widget = QWidget()`
  - **Uso**: Header embebido (pero se pasa como parent a QuickPreviewHeader)
  - **Problema**: Se crea sin parent explícito
  - **Corrección**: Verificar si QuickPreviewHeader recibe parent y pasarlo

- **Línea 44**: `self._name_label = QLabel()`
  - **Uso**: Label embebido en header
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self._header_widget` como parent: `QLabel(self._header_widget)`

### ⚠️ PENDIENTE: `app/ui/windows/quick_preview_thumbnail_widget.py`
- **Línea 30**: `thumb_container = QWidget()`
  - **Uso**: Contenedor de thumbnail (función factory)
  - **Problema**: Se crea sin parent
  - **Corrección**: Agregar parámetro `parent` a la función y pasarlo: `QWidget(parent)`

- **Línea 39**: `thumb_label = QLabel()`
  - **Uso**: Label embebido en thumbnail
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `thumb_container` como parent: `QLabel(thumb_container)`

### ⚠️ PENDIENTE: `app/ui/windows/desktop_window.py`
- **Línea 233**: `self._desktop_placeholder = QWidget()`
  - **Uso**: Placeholder embebido en DesktopWindow
  - **Problema**: Se crea sin parent
  - **Corrección**: Pasar `self` como parent: `QWidget(self)`

---

## 📋 Resumen por prioridad

### 🔴 Alta prioridad (causan flashes al cambiar workspace):
1. `file_tile_setup.py` - 3 widgets sin parent
2. `file_tile_icon.py` - 1 widget sin parent
3. `file_stack_tile.py` - 3 widgets sin parent
4. `desktop_stack_tile.py` - 3 widgets sin parent
5. `settings_stack_tile.py` - 3 widgets sin parent

### 🟡 Media prioridad (headers y paneles):
6. `file_box_panel.py` - 2 widgets sin parent
7. `file_box_history_panel.py` - 2 widgets sin parent
8. `workspace_selector.py` - 3 widgets sin parent
9. `header_customization_palette.py` - 1 widget sin parent

### 🟢 Baja prioridad (ventanas y overlays):
10. `quick_preview_window.py` - 4 widgets sin parent
11. `quick_preview_thumbnails.py` - 2 widgets sin parent
12. `quick_preview_header.py` - 2 widgets sin parent
13. `quick_preview_thumbnail_widget.py` - 2 widgets sin parent (factory)
14. `desktop_window.py` - 1 widget sin parent

---

## ✅ Instrucciones de corrección

Para cada caso:
1. **Identificar el parent correcto**: El widget que contiene el layout donde se añade
2. **Modificar la creación**: Cambiar `QWidget()` por `QWidget(parent)`
3. **Para factories**: Agregar parámetro `parent: Optional[QWidget] = None` y pasarlo desde el creador
4. **No cambiar**: Estilos, lógica, ni comportamiento visual

---

## Total: 33 widgets sin parent detectados

- ✅ 3 ya corregidos (list_row_factory.py)
- ⚠️ 30 pendientes de corrección

