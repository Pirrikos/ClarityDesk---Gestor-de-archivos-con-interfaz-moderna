# Reglas de Drag & Drop - ClarityDesk Pro

**Fecha:** 2025-11-29  
**Objetivo:** Documentar todas las reglas y comportamientos del sistema de drag & drop

---

## Resumen Ejecutivo

El sistema de drag & drop en ClarityDesk Pro tiene reglas específicas para diferentes contextos:
- **Desktop Focus**: Reglas especiales para el dock del escritorio
- **Carpetas normales**: Comportamiento estándar de mover archivos
- **Trash Focus**: Eliminación permanente
- **Drag externo**: Soporte para arrastrar desde aplicaciones externas

---

## Reglas Principales

### 1. Prevención de Dock-to-Dock Drop

**Regla:** No se puede arrastrar archivos desde el dock (Desktop Focus) hacia el mismo dock.

**Implementación:**
- Función: `should_reject_dock_to_dock_drop()` en `drag_common.py`
- Verifica si el folder activo es Desktop Focus
- Verifica si algún archivo arrastrado está en el dock (`is_file_in_dock()`)
- Si ambas condiciones son verdaderas, rechaza el drop

**Código relevante:**
```python
# drag_common.py línea 19-45
def should_reject_dock_to_dock_drop(mime_data, tab_manager):
    # Si estamos en Desktop Focus y arrastramos desde dock, rechazar
```

**Justificación:** Evita duplicación innecesaria de archivos en el dock.

---

### 2. Same-Folder Drop Prevention

**Regla:** No se puede hacer drop de un archivo/carpeta en la misma carpeta donde ya está.

**Implementación:**
- Función: `is_same_folder_drop()` en `drag_common.py`
- Compara el directorio del archivo fuente con el folder activo
- Maneja Desktop Focus correctamente (usa ruta real del escritorio)
- Rechaza el drop si son iguales

**Código relevante:**
```python
# drag_common.py línea 48-82
def is_same_folder_drop(source_path, tab_manager):
    # Compara directorios normalizados
```

**Justificación:** Evita operaciones innecesarias (mover archivo a su propia ubicación).

---

### 3. Move vs Copy Action

**Regla:** La acción por defecto es **MoveAction**, pero Windows puede proponer CopyAction.

**Comportamiento:**
- **Drag interno (dentro de ClarityDesk):** Siempre MoveAction
- **Drag externo (desde otras apps):** Windows propone acción (generalmente CopyAction)
- **Desktop Focus:** MoveAction por defecto
- **Archivos desde dock:** MoveAction cuando se suelta en carpetas

**Implementación:**
- `tile_drag_handler.py`: Permite ambas acciones, Windows decide
- `container_drag_handler.py`: Usa `event.proposedAction()` o MoveAction como fallback
- `list_drag_handler.py`: Mismo comportamiento que container

**Código relevante:**
```python
# container_drag_handler.py línea 99-103
if event.proposedAction() != Qt.DropAction.IgnoreAction:
    event.setDropAction(event.proposedAction())
else:
    event.setDropAction(Qt.DropAction.MoveAction)
```

**Justificación:** 
- MoveAction es más intuitivo para operaciones internas
- CopyAction permite arrastrar a aplicaciones externas (email, web, etc.)

---

### 4. Folder Inside Itself Prevention

**Regla:** No se puede mover una carpeta dentro de sí misma.

**Implementación:**
- Función: `is_folder_inside_itself()` en `drag_common.py`
- Verifica si la ruta fuente está dentro de la ruta destino
- Usa comparación de rutas absolutas

**Código relevante:**
```python
# drag_common.py línea 112-125
def is_folder_inside_itself(source_path, target_path):
    # Verifica si source está dentro de target
```

**Justificación:** Previene errores del sistema de archivos y bucles infinitos.

---

### 5. Desktop Focus Special Handling

**Regla:** Desktop Focus tiene reglas especiales para drag & drop.

**Comportamiento:**
- **Desde dock a carpeta:** MoveAction (mueve fuera del dock)
- **Desde carpeta a dock:** MoveAction (mueve al dock)
- **Dock a dock:** Rechazado (regla 1)
- **Archivos en dock:** Se detectan con `is_file_in_dock()`

**Implementación:**
- `file_tile_drag.py`: Detecta si archivo viene del dock
- `desktop_operations.py`: Maneja operaciones especiales del dock

**Código relevante:**
```python
# file_tile_drag.py línea 81-87
if is_file_in_dock(file_path):
    result = move_file(file_path, tile._file_path, watcher=watcher)
elif is_desktop_focus(file_dir):
    result = move_out_of_desktop(file_path, tile._file_path, watcher=watcher)
```

**Justificación:** El dock es un espacio especial que requiere manejo diferente.

---

### 6. Trash Focus Handling

**Regla:** En Trash Focus, el drop elimina permanentemente (no mueve).

**Comportamiento:**
- Drop en Trash Focus = Eliminación permanente
- Requiere confirmación del usuario
- No se puede restaurar después

**Implementación:**
- `file_delete_service.py`: Maneja eliminación permanente
- `trash_operations.py`: Operaciones de papelera

**Justificación:** Trash Focus es para eliminación definitiva, no para mover archivos.

---

## Flujo de Drag & Drop

### Flujo General

```
1. Usuario inicia drag (mouseDown + move)
   ↓
2. handle_drag_enter() - Verifica si drop es válido
   ↓
3. handle_drag_move() - Actualiza feedback visual mientras arrastra
   ↓
4. Usuario suelta (mouseUp)
   ↓
5. handle_drop() - Procesa el drop
   ├─ Verifica reglas (dock-to-dock, same-folder, etc.)
   ├─ Determina acción (move/copy)
   ├─ Ejecuta operación de archivo
   └─ Emite señales (file_deleted, folder_moved, etc.)
```

### Casos Especiales

#### Caso 1: Drag desde Dock
```
Archivo en dock → Carpeta normal
├─ Verifica: ¿Es dock-to-dock? NO
├─ Verifica: ¿Es same-folder? NO
├─ Acción: MoveAction
└─ Resultado: Archivo movido fuera del dock
```

#### Caso 2: Drag a Desktop Focus
```
Archivo en carpeta → Desktop Focus
├─ Verifica: ¿Es dock-to-dock? NO (archivo no está en dock)
├─ Verifica: ¿Es same-folder? NO
├─ Acción: MoveAction
└─ Resultado: Archivo movido al dock
```

#### Caso 3: Drag Dock-to-Dock (Rechazado)
```
Archivo en dock → Desktop Focus
├─ Verifica: ¿Es dock-to-dock? SÍ
└─ Resultado: Drop rechazado (event.ignore())
```

#### Caso 4: Same-Folder Drop (Rechazado)
```
Archivo en Carpeta A → Carpeta A
├─ Verifica: ¿Es same-folder? SÍ
└─ Resultado: Drop rechazado (event.ignore())
```

---

## Archivos Involucrados

### Handlers de Drag & Drop
- `app/ui/widgets/drag_common.py` - Utilidades comunes
- `app/ui/widgets/tile_drag_handler.py` - Drag desde tiles
- `app/ui/widgets/container_drag_handler.py` - Drop en contenedor principal
- `app/ui/widgets/list_drag_handler.py` - Drop en vista de lista
- `app/ui/widgets/file_tile_drag.py` - Drop en tile de carpeta
- `app/ui/widgets/folder_tree_drag_handler.py` - Drop en árbol de carpetas
- `app/ui/widgets/file_drop_handler.py` - Handler principal de drop

### Servicios Relacionados
- `app/services/file_move_service.py` - Operación de mover archivo
- `app/services/desktop_operations.py` - Operaciones del dock
- `app/services/file_delete_service.py` - Eliminación de archivos

---

## Comentarios en Código

Las reglas críticas están documentadas en `drag_common.py` con comentarios explicativos. Las funciones principales tienen docstrings que explican su propósito y comportamiento.

---

## Notas de Implementación

1. **Debouncing:** No se aplica debounce en drag & drop (operación síncrona del usuario)

2. **Watcher Events:** Los eventos del filesystem watcher se bloquean durante operaciones de archivo para evitar loops infinitos

3. **Señales Emitidas:**
   - `file_deleted`: Cuando archivo se mueve fuera de la vista actual
   - `folder_moved`: Cuando carpeta se mueve (actualiza sidebar)
   - `file_dropped`: Cuando archivo se suelta en una vista

4. **Compatibilidad Windows:**
   - Usa `QMimeData` con URLs locales
   - Respeta acciones propuestas por Windows (CopyAction para servicios externos)
   - Maneja correctamente drag desde explorador de Windows

---

## Testing Recomendado

Para validar el comportamiento correcto:

1. **Dock-to-Dock:** Intentar arrastrar archivo del dock al mismo dock → Debe rechazarse
2. **Same-Folder:** Arrastrar archivo a su propia carpeta → Debe rechazarse
3. **Move Action:** Arrastrar archivo entre carpetas → Debe moverse (no copiarse)
4. **Copy Action:** Arrastrar archivo a aplicación externa → Debe copiarse
5. **Folder Inside Itself:** Intentar mover carpeta dentro de sí misma → Debe rechazarse
6. **Desktop Focus:** Arrastrar archivo al dock → Debe moverse al dock

---

## Cambios Futuros

Posibles mejoras identificadas:
- Mejorar feedback visual durante drag (mostrar cantidad de archivos)
- Resaltar zonas de drop válidas
- Mostrar icono de acción (move/copy) según tecla modificadora
- Soporte para drag múltiple mejorado

