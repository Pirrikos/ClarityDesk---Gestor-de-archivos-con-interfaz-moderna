# ANÁLISIS PROFUNDO: Source of Truth del Icono en GridView

## 1. CADENA DE RENDERIZADO COMPLETA

### Flujo desde datos hasta pixel en pantalla:

```
FileGridView.update_files(file_list)
  ↓
FileGridView._refresh_tiles()
  ↓
grid_layout_engine.build_normal_grid(view, items_to_render, grid_layout)
  ↓
grid_tile_positions.add_tile_to_normal_grid(view, items_to_render, grid_layout, columns, col_offset)
  ↓
grid_tile_builder.create_file_tile(file_path, parent_view, icon_service, state_manager, dock_style=False)
  ↓
FileTile.__init__(file_path, parent_view, icon_service, dock_style=False, initial_state=state)
  ↓
file_tile_setup.setup_ui(tile)
  ↓
file_tile_setup.setup_layout(tile)
  ↓
file_tile_setup.add_icon_zone(tile, icon_layout, tile._icon_service)
  ↓
icon_render_service.get_file_preview(tile._file_path, QSize(96, 96))
  ↓
preview_service.get_file_preview(path, size, icon_provider) → QPixmap
  ↓
IconWidget.__init__(tile, parent=icon_container)
  ↓
IconWidget.set_pixmap(pixmap) → almacena en self._icon_pixmap
  ↓
layout.addWidget(icon_widget, 0, AlignHCenter) → añade IconWidget al icon_layout
  ↓
icon_container añadido al layout principal de FileTile
  ↓
FileTile añadido al QGridLayout de FileGridView
  ↓
Qt renderiza FileTile → renderiza icon_container → renderiza IconWidget
  ↓
IconWidget.paintEvent(event) → QPainter.drawPixmap() → PIXEL EN PANTALLA
```

## 2. QUIÉN CREA EL WIDGET VISIBLE

**Archivo:** `app/ui/widgets/file_tile_icon.py`  
**Función:** `add_icon_zone()`  
**Líneas:** 87-100

```python
if is_grid_view:
    icon_widget = IconWidget(tile)  # Línea 89
    icon_widget.setFixedSize(icon_width, icon_height)  # Línea 90
    icon_widget.set_pixmap(pixmap)  # Línea 91
    tile._icon_label = icon_widget  # Línea 99
```

**Condición de creación:** `is_grid_view = not tile._dock_style and _is_grid_view(tile)`

## 3. QUÉ CLASE HACE setPixmap() O PINTA CON QPainter

### setPixmap():
**Archivo:** `app/ui/widgets/file_tile_icon.py`  
**Clase:** `IconWidget`  
**Método:** `set_pixmap(pixmap: QPixmap)`  
**Línea:** 32-35

```python
def set_pixmap(self, pixmap: QPixmap) -> None:
    self._icon_pixmap = pixmap
    self.update()  # Trigger repaint
```

### QPainter (pintado):
**Archivo:** `app/ui/widgets/file_tile_icon.py`  
**Clase:** `IconWidget`  
**Método:** `paintEvent(event)`  
**Línea:** 37-43

```python
def paintEvent(self, event) -> None:
    super().paintEvent(event)
    painter = QPainter(self)
    painter.fillRect(self.rect(), QColor(0, 0, 0))  # PRUEBA ACTUAL: rectángulo negro
    painter.end()
```

## 4. CONFIRMACIÓN: ¿tile._icon_label ES EL WIDGET MOSTRADO?

### En qué layout se añade:

**Archivo:** `app/ui/widgets/file_tile_setup.py`  
**Función:** `setup_layout()`  
**Líneas:** 67-74

```python
# Contenedor para icono
icon_container = QWidget()  # Línea 68
icon_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
icon_layout = QVBoxLayout(icon_container)  # Línea 70
icon_layout.setContentsMargins(0, 0, 0, 0)
icon_layout.setSpacing(0)
add_icon_zone(tile, icon_layout, tile._icon_service)  # Línea 73 - aquí se añade IconWidget
layout.addWidget(icon_container, 0, Qt.AlignmentFlag.AlignHCenter)  # Línea 74
```

**Jerarquía de layouts:**
1. `FileTile.layout` (QVBoxLayout) → contiene `icon_container`
2. `icon_container.icon_layout` (QVBoxLayout) → contiene `IconWidget` (tile._icon_label)

### Parent real del IconWidget:

**En runtime:**
- `IconWidget.parent()` → `icon_container` (QWidget)
- `IconWidget.parentWidget()` → `icon_container` (QWidget)
- `icon_container.parent()` → `FileTile` (QWidget)

### Contenedores intermedios:

**SÍ existe contenedor intermedio:**
- `icon_container` (QWidget) creado en `file_tile_setup.py:68`
- `icon_container` contiene `icon_layout` (QVBoxLayout)
- `icon_layout` contiene `IconWidget` (tile._icon_label)

**Estructura completa:**
```
FileTile (QWidget)
  └─ layout (QVBoxLayout)
      └─ icon_container (QWidget)
          └─ icon_layout (QVBoxLayout)
              └─ IconWidget (tile._icon_label) ← WIDGET QUE PINTA
```

## 5. RENDER ALTERNATIVO O CACHE

### ❌ NO hay delegate:
- FileGridView NO usa `QStyledItemDelegate`
- Los tiles son widgets directos (`FileTile` = `QWidget`)
- Se añaden directamente con `grid_layout.addWidget(tile, row, col)`

### ❌ NO hay pixmap cache que ignore IconWidget:
- `IconService` tiene cache de `QIcon` (no `QPixmap`)
- `IconRenderService` NO tiene cache de pixmaps
- El pixmap se genera cada vez en `get_file_preview()`
- El pixmap se almacena en `IconWidget._icon_pixmap` y se pinta en `paintEvent()`

### ❌ NO hay render offscreen:
- No hay `QGraphicsScene` ni `QGraphicsView`
- No hay `QOffscreenSurface`
- Render directo con `QPainter` en `paintEvent()`

### ✅ QGraphicsDropShadowEffect:
- Se aplica a `IconWidget` en línea 93-97 de `file_tile_icon.py`
- Esto NO interfiere con el pintado, solo añade sombra visual

## 6. TABLA: LUGARES DONDE SE GENERA O ASIGNA EL PIXMAP

| Archivo | Función/Método | Línea | Propósito |
|---------|---------------|-------|-----------|
| `app/services/preview_service.py` | `get_file_preview()` | 34 | Genera pixmap desde Windows shell/icons |
| `app/services/icon_render_service.py` | `get_file_preview()` | 39 | Normaliza y aplica fallbacks al pixmap |
| `app/ui/widgets/file_tile_icon.py` | `add_icon_zone()` | 76, 80 | Llama a `get_file_preview()` y obtiene pixmap |
| `app/ui/widgets/file_tile_icon.py` | `IconWidget.set_pixmap()` | 32 | **ASIGNA pixmap a IconWidget._icon_pixmap** |
| `app/ui/widgets/file_tile_icon.py` | `IconWidget.paintEvent()` | 37 | **PINTA pixmap con QPainter.drawPixmap()** |
| `app/ui/widgets/file_tile_icon.py` | `animate_icon_size()` | 153 | Escala pixmap durante animación hover |
| `app/ui/widgets/file_tile_icon.py` | `animate_icon_size()` | 160 | Actualiza pixmap escalado en IconWidget |

**Punto crítico de asignación:** `IconWidget.set_pixmap()` línea 32-35  
**Punto crítico de renderizado:** `IconWidget.paintEvent()` línea 37-43

## 7. PRUEBA DE TRAZABILIDAD (LOGS TEMPORALES)

### Logs añadidos:

**1. Constructor de IconWidget:**
- **Archivo:** `app/ui/widgets/file_tile_icon.py`
- **Línea:** 30
- **Log:** `[ICON_WIDGET] Constructor ejecutado - tile._file_path={path}, parent={parent}`

**2. Asignación de pixmap:**
- **Archivo:** `app/ui/widgets/file_tile_icon.py`
- **Líneas:** 88, 91
- **Logs:** 
  - `[ICON_ZONE] GridView detectado - creando IconWidget para {path}`
  - `[ICON_ZONE] Asignando pixmap a IconWidget - tamaño={w}x{h}, isNull={bool}`

### Verificación esperada en consola:

Al cargar una carpeta en GridView, debería verse:
```
[ICON_ZONE] GridView detectado - creando IconWidget para C:\path\to\file.pdf
[ICON_WIDGET] Constructor ejecutado - tile._file_path=C:\path\to\file.pdf, parent=<QWidget object>
[ICON_ZONE] Asignando pixmap a IconWidget - tamaño=96x96, isNull=False
```

Si estos logs NO aparecen → IconWidget NO se está creando  
Si estos logs SÍ aparecen pero no se ve el rectángulo negro → problema en paintEvent() o layout

## 8. DIAGRAMA TEXTUAL FINAL

```
FileGridView.update_files()
  ↓
grid_layout_engine.build_normal_grid()
  ↓
grid_tile_positions.add_tile_to_normal_grid()
  ↓
grid_tile_builder.create_file_tile() [Línea 42]
  ↓
FileTile.__init__() [Línea 36]
  ↓
file_tile_setup.setup_ui() [Línea 22]
  ↓
file_tile_setup.setup_layout() [Línea 36]
  ↓
file_tile_setup.add_icon_zone() [Línea 73]
  ↓
icon_render_service.get_file_preview() [Línea 80]
  ↓
preview_service.get_file_preview() → QPixmap
  ↓
IconWidget.__init__() [Línea 89] ← CREACIÓN DEL WIDGET
  ↓
IconWidget.set_pixmap(pixmap) [Línea 91] ← ASIGNACIÓN DEL PIXMAP
  ↓
layout.addWidget(icon_widget) [Línea 119] ← AÑADIDO AL LAYOUT
  ↓
Qt renderiza widget tree
  ↓
IconWidget.paintEvent(event) [Línea 37] ← ÚNICO PUNTO QUE PINTA EN PANTALLA
```

## CONCLUSIÓN: SOURCE OF TRUTH

**El único punto del código que realmente controla el icono visible es:**

**`IconWidget.paintEvent()` en `app/ui/widgets/file_tile_icon.py:37-43`**

Este método es el ÚNICO responsable de pintar el icono en pantalla. Si el rectángulo negro de prueba no aparece, significa que:
1. `IconWidget.paintEvent()` NO se está ejecutando, O
2. El widget está siendo ocultado/sobrescrito por otro widget hijo, O
3. El widget no está recibiendo eventos de pintado (problema de layout/parent)

**Evidencia:**
- No hay delegates que intercepten el renderizado
- No hay cache de pixmaps que ignore el widget
- No hay render offscreen
- El pixmap se asigna correctamente en `set_pixmap()`
- El widget se añade correctamente al layout
- El único punto de pintado es `paintEvent()`

