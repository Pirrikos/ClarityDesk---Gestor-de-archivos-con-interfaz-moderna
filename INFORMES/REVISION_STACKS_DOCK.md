# REVISIÓN COMPLETA: STACKS DEL DOCK

## 📋 RESUMEN EJECUTIVO

Los **stacks del dock** son agrupaciones de archivos por tipo/familia que se muestran en la ventana `DesktopWindow` (Dock). Esta funcionalidad permite organizar visualmente los archivos del escritorio en categorías como PDFs, Documentos, Imágenes, etc.

**Estado general**: ✅ **Funcionalidad completa y bien estructurada**

---

## 🏗️ ARQUITECTURA DE STACKS

### 1. MODELO DE DATOS

**Archivo**: `app/models/file_stack.py`

```python
@dataclass
class FileStack:
    stack_type: str  # Familia: 'folder', 'pdf', 'documents', etc.
    files: List[str]  # Lista de rutas de archivos en el stack
```

**Familias de stacks** (orden fijo):
1. `folder` - Carpetas
2. `pdf` - PDFs
3. `documents` - Documentos (.doc, .docx, .odt, .rtf, .txt)
4. `sheets` - Hojas de cálculo (.xls, .xlsx, .csv)
5. `slides` - Presentaciones (.ppt, .pptx)
6. `images` - Imágenes (.jpg, .jpeg, .png, .gif, .webp, .svg)
7. `video` - Videos (.mp4, .avi, .mkv, .mov)
8. `audio` - Audio (.mp3, .wav, .flac)
9. `archives` - Archivos comprimidos (.zip, .rar, .7z)
10. `executables` - Ejecutables (.exe, .msi, .bat, .cmd, .com, .scr, .ps1, .lnk)
11. `others` - Otros

**✅ Cumple reglas**:
- Modelo puro (sin lógica, sin Qt, sin I/O) ✅
- Type hints completos ✅
- Nombres descriptivos ✅

---

### 2. SERVICIO DE CREACIÓN DE STACKS

**Archivo**: `app/services/file_stack_service.py`

**Funciones principales**:
- `get_file_family(file_path, is_executable_func) -> str`: Determina la familia de un archivo
- `create_file_stacks(files, is_executable_func) -> List[FileStack]`: Agrupa archivos en stacks

**Lógica de agrupación**:
1. Itera sobre todos los archivos
2. Determina la familia de cada archivo (por extensión o función `is_executable`)
3. Agrupa archivos por familia en un diccionario
4. Crea objetos `FileStack` en el orden fijo de `FAMILY_ORDER`
5. Solo incluye stacks no vacíos

**✅ Cumple reglas**:
- Servicio puro (sin UI) ✅
- Lógica centralizada (DRY) ✅
- Type hints completos ✅
- Sin dependencias de UI ✅

---

### 3. INTEGRACIÓN CON TAB MANAGER

**Archivo**: `app/managers/tab_manager.py` (línea 148)

```python
def get_files(self, extensions: Optional[set] = None, use_stacks: bool = False) -> List:
    """Get filtered file list from active folder."""
    return get_files_from_active_tab(
        self.get_active_folder(), extensions or self.SUPPORTED_EXTENSIONS, use_stacks
    )
```

**Flujo**:
1. `TabManager.get_files(use_stacks=True)` → 
2. `get_files_from_active_tab(..., use_stacks=True)` → 
3. `file_list_service.get_files(..., use_stacks=True)` → 
4. `file_stack_service.create_file_stacks(...)`

**✅ Cumple reglas**:
- Separación de capas correcta ✅
- Inyección de dependencias ✅
- Parámetro explícito `use_stacks` ✅

---

### 4. WIDGET DE STACK TILE

**Archivo**: `app/ui/widgets/file_stack_tile.py`

**Características**:
- Tamaño fijo: 70x85px (70x70 contenedor + texto debajo)
- Icono del primer archivo del stack (48x48px)
- Badge con contador de archivos (overlay flotante)
- Texto con nombre amigable (elide middle)
- Estilo Dock: fondo blanco translúcido, bordes redondeados
- Sombra sutil en icono y texto

**Señales**:
- `stack_clicked(FileStack)`: Emitida al hacer clic (expande/contrae)
- `open_file(str)`: Emitida al doble clic (abre primer archivo)

**Eventos**:
- `mousePressEvent`: Inicia drag
- `mouseReleaseEvent`: Emite `stack_clicked` si no hubo drag
- `mouseMoveEvent`: Inicia drag de todos los archivos del stack
- `mouseDoubleClickEvent`: Abre primer archivo

**✅ Cumple reglas**:
- Widget UI puro ✅
- Señales a nivel de clase ✅
- Gestión de recursos (badge cleanup) ✅
- Parent siempre pasado ✅

**⚠️ Posibles mejoras**:
- El badge overlay tiene lógica compleja de posicionamiento (líneas 188-243)
- Muchos `try/except RuntimeError` sugieren posibles problemas de ciclo de vida

---

### 5. LAYOUT DEL DOCK

**Archivo**: `app/ui/widgets/grid_layout_engine.py`

**Función principal**: `build_dock_layout(...)`

**Estructura del layout**:
```
Fila 0 (stack_row = 0):
  - Columna 0: DesktopStackTile (si es DesktopWindow)
  - Columna 1: SettingsStackTile (si es DesktopWindow)
  - Columna 2: DockSeparator (si es DesktopWindow)
  - Columna 3+: FileStackTile (uno por cada stack)

Fila 1+ (archivos expandidos):
  - Archivos del stack expandido distribuidos en grid
```

**Función `_build_stack_tiles`**:
- Crea tiles para Desktop, Settings, Separator (si aplica)
- Crea `FileStackTile` para cada stack
- Conecta señal `stack_clicked` → `view._on_stack_clicked`
- Retorna `stack_col_map` (mapeo tipo → columna)

**Función `_build_expanded_files`**:
- Crea tiles de archivos para stacks expandidos
- Distribuye archivos en grid debajo del stack correspondiente
- Calcula posición basada en `stack_col_map`

**✅ Cumple reglas**:
- Separación de responsabilidades ✅
- Funciones pequeñas y enfocadas ✅
- Type hints ✅

---

### 6. EXPANSIÓN DE STACKS

**Archivo**: `app/ui/widgets/file_grid_view_events.py`

**Función `on_stack_clicked`**:
```python
def on_stack_clicked(view, file_stack: FileStack) -> None:
    stack_type = file_stack.stack_type
    
    if stack_type in view._expanded_stacks:
        # Contrae: elimina del dict
        del view._expanded_stacks[stack_type]
    else:
        # Expande: limpia otros y añade este
        view._expanded_stacks.clear()
        view._expanded_stacks[stack_type] = file_stack.files
    
    emit_expansion_height(view)
    view._refresh_tiles()
```

**Lógica**:
- Solo un stack puede estar expandido a la vez
- Al hacer clic en un stack expandido, se contrae
- Al hacer clic en un stack contraído, se expande (y contrae el anterior)

**Cálculo de altura** (`emit_expansion_height`):
- Calcula número de filas necesarias: `(total_files + total_stacks - 1) // total_stacks`
- Altura por fila: 85px (tile) + 16px (spacing) = 101px
- Altura total: `(num_rows * height_per_row) + 40px` (margen extra)

**✅ Cumple reglas**:
- Lógica clara y simple ✅
- Sin efectos secundarios inesperados ✅

---

### 7. AJUSTE DE VENTANA DEL DOCK

**Archivo**: `app/ui/windows/desktop_window.py`

**Ajuste de ancho** (`_adjust_window_width`):
- Se conecta a señal `stacks_count_changed`
- Calcula ancho basado en número de stacks:
  ```
  ancho = escritorio_width (70) + ajustes_width (70) + separator_width (1) + 
          (stacks_count * stack_width (70)) + 
          (spacing * (stacks_count + 2)) + margins (72)
  ```
- Aplica animación suave (250ms, OutCubic)

**Ajuste de altura** (`_adjust_window_height`):
- Se conecta a señal `expansion_height_changed`
- Altura base: 140px
- Altura total: `base_height + expansion_height`
- Primera expansión: sin animación (inmediata)
- Cambios posteriores: animación suave (250ms, OutCubic)

**✅ Cumple reglas**:
- Animaciones para operaciones >100ms ✅
- Gestión correcta de recursos (stop animaciones anteriores) ✅

**⚠️ Código duplicado**:
- Líneas 384-389: código duplicado de verificación de ancho (ya está en línea 357)

---

### 8. SINCRONIZACIÓN DE VISTAS

**Archivo**: `app/ui/widgets/file_view_sync.py`

**Función `update_files`**:
- Detecta si es DesktopWindow (`_cached_is_desktop`)
- Llama a `tab_manager.get_files(use_stacks=use_stacks)`
- Actualiza `grid_view` y `list_view`
- Limpia estados de archivos que ya no existen

**Expansión de stacks en lista**:
- `file_list_renderer.expand_stacks_to_files()` expande stacks a archivos individuales
- La vista de lista siempre muestra archivos individuales (no stacks)

**✅ Cumple reglas**:
- Lógica clara ✅
- Cache para evitar checks repetidos ✅

---

## 🔍 ANÁLISIS DE PROBLEMAS POTENCIALES

### 1. **Badge Overlay - Gestión de Ciclo de Vida**

**Ubicación**: `app/ui/widgets/file_stack_tile.py` (líneas 157-243)

**Problema**:
- Muchos `try/except RuntimeError` sugieren problemas de ciclo de vida
- El badge puede quedar huérfano si el tile se elimina antes de limpiarlo
- Posicionamiento complejo con múltiples verificaciones

**Recomendación**:
- Considerar usar `QObject.parent()` más robustamente
- Simplificar lógica de posicionamiento
- Asegurar cleanup en `closeEvent` (ya implementado ✅)

### 2. **Código Duplicado en DesktopWindow**

**Ubicación**: `app/ui/windows/desktop_window.py` (líneas 384-389)

**Problema**:
```python
# Check if width needs to change
if current_width == target_width:
    return

# Apply smooth width animation
self._apply_width_animation(current_geometry, target_width, new_x, current_height)
```

Este código ya está ejecutado en líneas 357-364.

**Recomendación**: Eliminar líneas 384-389 (código muerto)

### 3. **Orden de Familias Hardcodeado**

**Ubicación**: `app/services/file_stack_service.py` (línea 71)

**Problema**:
- El orden de familias está hardcodeado en `FAMILY_ORDER`
- No es configurable por el usuario

**Estado**: ✅ **Correcto según diseño** (orden visual consistente)

### 4. **Expansión de Stacks - Solo Uno a la Vez**

**Ubicación**: `app/ui/widgets/file_grid_view_events.py` (línea 27)

**Problema**:
- Solo permite un stack expandido a la vez
- Al expandir uno, se contrae el anterior

**Estado**: ✅ **Diseño intencional** (evita sobrecarga visual)

---

## ✅ CUMPLIMIENTO DE REGLAS

### Regla 1: Separación de Capas ✅
- **Modelo** (`file_stack.py`): Puro, sin dependencias ✅
- **Servicio** (`file_stack_service.py`): Solo modelos ✅
- **Manager** (`tab_manager.py`): Modelos + servicios ✅
- **UI** (`file_stack_tile.py`): Todo permitido ✅

### Regla 2: Responsabilidad Única ✅
- `FileStack`: Modelo de datos ✅
- `create_file_stacks`: Agrupa archivos ✅
- `FileStackTile`: Widget visual de stack ✅
- `on_stack_clicked`: Maneja clic de expansión ✅

### Regla 3: Cohesión ✅
- Archivos bien estructurados (ninguno >800 líneas) ✅
- Lógica relacionada agrupada ✅

### Regla 4: DRY ✅
- Sin duplicación de lógica de agrupación ✅
- Servicio centralizado ✅

### Regla 5: Inyección de Dependencias ✅
- `IconService` inyectado en `FileStackTile` ✅
- `TabManager` inyectado en `FileViewContainer` ✅

### Regla 16: Señales Qt ✅
- `stack_clicked` declarada a nivel de clase ✅
- Emitida después de actualizar estado ✅

### Regla 17: Separación UI/Business ✅
- Managers no importan widgets ✅
- Servicios no importan UI ✅

### Regla 18: Gestión de Recursos ✅
- Badge cleanup en `closeEvent` ✅
- Parent siempre pasado ✅

### Regla 20: Threading ✅
- Operaciones pesadas (renderizado de iconos) en servicios ✅
- No bloquea UI thread ✅

---

## 📊 MÉTRICAS DE CÓDIGO

| Archivo | Líneas | Responsabilidad | Estado |
|---------|--------|-----------------|--------|
| `file_stack.py` | 58 | Modelo de datos | ✅ |
| `file_stack_service.py` | 144 | Creación de stacks | ✅ |
| `file_stack_tile.py` | 436 | Widget visual | ✅ |
| `grid_layout_engine.py` | 168 | Layout del dock | ✅ |
| `file_grid_view_events.py` | 75 | Eventos de expansión | ✅ |
| `desktop_window.py` | 477 | Ventana del dock | ✅ |

**Total**: ~1,358 líneas relacionadas con stacks

---

## 🎯 RECOMENDACIONES

### Prioridad Alta

1. **Eliminar código duplicado** en `desktop_window.py` (líneas 384-389)
2. **Simplificar gestión de badge overlay** en `file_stack_tile.py`

### Prioridad Media

3. **Documentar comportamiento** de expansión única (ya está claro en código)
4. **Considerar tests** para `file_stack_service.py` (agrupación de archivos)

### Prioridad Baja

5. **Optimizar cálculo de altura** de expansión (ya es eficiente)
6. **Considerar cache** de stacks si hay muchos archivos

---

## ✅ CONCLUSIÓN

Los **stacks del dock** están **bien implementados** y siguen las reglas de arquitectura del proyecto. La funcionalidad es completa y el código está bien estructurado.

**Puntos fuertes**:
- Separación clara de responsabilidades
- Modelo de datos limpio
- Servicio centralizado
- Widget visual completo
- Integración correcta con TabManager

**Áreas de mejora menores**:
- Código duplicado en DesktopWindow
- Complejidad en gestión de badge overlay

**Estado general**: ✅ **APROBADO** - Funcionalidad completa y lista para producción

