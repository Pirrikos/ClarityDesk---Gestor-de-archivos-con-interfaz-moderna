# Análisis de Colisiones y Problemas - Vistas por Estado

## Resumen Ejecutivo

Análisis exhaustivo del código actual para identificar colisiones y problemas potenciales al implementar vistas por estado con paths virtuales `@state://pending`.

**Total de problemas encontrados: 8 críticos, 5 importantes**

---

## Problemas Críticos (Deben Resolverse)

### 1. FileSystemWatcher intentará observar paths virtuales

**Ubicación**: `app/services/filesystem_watcher_service.py:49`

**Problema**: 
```python
def watch_folder(self, folder_path: str) -> bool:
    if not folder_path:
        return False
    # ...
    if self._watcher.addPath(folder_path):  # ❌ Fallará con @state://pending
```

**Impacto**: Si `TabManager.set_state_context()` llama a `watch_and_emit()` con `@state://pending`, el watcher intentará añadir un path que no existe en el filesystem.

**Solución**: 
- Verificar si el path es virtual antes de observar
- Crear función helper: `is_virtual_path(path: str) -> bool`
- En `watch_folder()`, retornar `True` sin observar si es virtual

**Archivos afectados**:
- `app/services/filesystem_watcher_service.py`
- `app/managers/tab_manager_signals.py:29` (watch_and_emit)

---

### 2. validate_folder() no reconoce paths virtuales de estado

**Ubicación**: `app/services/tab_helpers.py:66`

**Problema**:
```python
def validate_folder(folder_path: str) -> bool:
    # Solo maneja Desktop Focus y Trash Focus
    if is_desktop_focus(folder_path):
        return True
    if folder_path == TRASH_FOCUS_PATH:
        return True
    # ❌ No maneja @state://pending
    return validate_folder_base(folder_path)
```

**Impacto**: Si algún código intenta validar `@state://pending`, fallará y podría rechazar operaciones válidas.

**Solución**:
- Añadir verificación: `if folder_path.startswith("@state://"): return True`
- O crear función centralizada: `is_virtual_path(path: str) -> bool`

**Archivos afectados**:
- `app/services/tab_helpers.py`
- Cualquier código que valide paths antes de operar

---

### 3. normalize_path() puede normalizar incorrectamente paths virtuales

**Ubicación**: `app/services/path_utils.py:11`

**Problema**:
```python
def normalize_path(path: str) -> str:
    if not path:
        return ""
    return os.path.normcase(os.path.normpath(path))  # ❌ Puede alterar @state://pending
```

**Impacto**: `os.path.normpath()` podría alterar `@state://pending` de forma inesperada (aunque probablemente no, es mejor ser explícito).

**Solución**:
- Verificar si es path virtual antes de normalizar
- Si es virtual, retornar tal cual (o normalizar solo la parte del estado)

**Archivos afectados**:
- `app/services/path_utils.py`
- Todos los lugares que normalizan paths (muchos)

---

### 4. Drag & Drop asume get_active_folder() siempre retorna path válido

**Ubicación**: `app/ui/widgets/file_drop_handler.py:42`, `app/ui/widgets/drag_common.py:41`

**Problema**:
```python
# file_drop_handler.py:42
active_folder = tab_manager.get_active_folder()
if not active_folder:  # ✅ Ya maneja None
    return False, source_file_path, None
# Pero luego usa active_folder sin verificar si es virtual
real_dest_folder = active_folder  # ❌ Puede ser @state://pending
```

**Impacto**: Si hay contexto de estado activo, `get_active_folder()` retorna `None`, pero si algún código futuro asume que siempre hay path, podría fallar.

**Solución**:
- Ya maneja `None` correctamente ✅
- Añadir verificación explícita: `if tab_manager.has_state_context(): return False`
- Documentar que drag & drop NO funciona en vistas por estado (según requerimientos)

**Archivos afectados**:
- `app/ui/widgets/file_drop_handler.py`
- `app/ui/widgets/drag_common.py`
- `app/ui/widgets/container_drag_handler.py`

---

### 5. Historial puede almacenar paths virtuales sin validación

**Ubicación**: `app/services/tab_history_manager.py:29`

**Problema**:
```python
def update_on_navigate(self, folder_path: str, normalize_func) -> None:
    normalized_path = normalize_func(folder_path)  # ❌ Normaliza @state://pending
    # Almacena en historial sin verificar si es válido
    self._history.append(normalized_path)
```

**Impacto**: El historial almacenará `@state://pending` (o su versión normalizada), pero al restaurar, podría intentar navegar a un path que no existe.

**Solución**:
- El historial ya funciona con strings, así que técnicamente funciona ✅
- Pero necesitamos asegurar que `TabManager.select_tab()` maneje paths virtuales correctamente
- O filtrar paths virtuales del historial si no queremos que sean navegables desde historial

**Archivos afectados**:
- `app/services/tab_history_manager.py`
- `app/managers/tab_manager_actions.py:229` (select_tab)

---

### 6. select_tab() no maneja paths virtuales

**Ubicación**: `app/managers/tab_manager_actions.py:209`

**Problema**:
```python
def select_tab(manager, index: int, tabs: List[str], ...):
    folder_path = tabs[index]  # ❌ Puede ser @state://pending
    # ...
    watch_and_emit_callback(folder_path)  # ❌ Intentará observar path virtual
```

**Impacto**: Si un tab contiene un path virtual `@state://pending`, `select_tab()` intentará observarlo y fallará.

**Solución**:
- Verificar si es path virtual antes de observar
- Si es virtual, activar contexto de estado en lugar de observar

**Archivos afectados**:
- `app/managers/tab_manager_actions.py`
- `app/managers/tab_manager.py:117` (select_tab)

---

### 7. Tabs no deberían contener paths virtuales

**Problema Conceptual**: Según el diseño, las vistas por estado NO son tabs. Son contextos temporales que se activan desde el sidebar.

**Impacto**: Si accidentalmente se añade `@state://pending` a la lista de tabs, causará problemas en múltiples lugares.

**Solución**:
- `add_tab()` debe rechazar paths virtuales explícitamente
- `validate_folder()` debe retornar `False` para paths virtuales de estado (solo válidos como contexto, no como tabs)

**Archivos afectados**:
- `app/managers/tab_manager_actions.py:55` (add_tab)
- `app/services/tab_helpers.py:66` (validate_folder)

---

### 8. get_files_from_active_tab() ya maneja None correctamente

**Ubicación**: `app/managers/tab_manager_actions.py:240`

**Estado**: ✅ **YA ESTÁ BIEN**
```python
def get_files_from_active_tab(active_folder: Optional[str], ...):
    if not active_folder:
        return []  # ✅ Maneja None correctamente
```

**Nota**: Este código ya está preparado para cuando `get_active_folder()` retorne `None`.

---

## Problemas Importantes (Revisar)

### 9. MainWindow usa get_active_folder() en múltiples lugares

**Ubicación**: `app/ui/windows/main_window.py:398, 779, 790`

**Problema**: Varios lugares usan `get_active_folder()` y podrían asumir que siempre retorna un path.

**Revisar**:
- Línea 398: `active_folder = self._tab_manager.get_active_folder()` - ¿Qué hace con None?
- Línea 779: Similar
- Línea 790: Similar

**Solución**: Revisar cada uso y añadir verificaciones si es necesario.

---

### 10. file_view_sync.py usa get_active_folder() pero no lo necesita

**Ubicación**: `app/ui/widgets/file_view_sync.py:37`

**Estado**: ✅ **YA ESTÁ BIEN**
```python
active_folder = container._tab_manager.get_active_folder()  # Se obtiene pero no se usa críticamente
items = container._tab_manager.get_files(use_stacks=use_stacks)  # ✅ Usa get_files() que maneja contexto
```

**Nota**: Este código obtiene `active_folder` pero no lo usa de forma crítica. `get_files()` ya maneja el contexto de estado internamente.

---

### 11. folder_tree_sidebar.py usa get_active_folder() para resaltar

**Ubicación**: `app/ui/widgets/folder_tree_sidebar.py:612`

**Problema**: Usa `get_active_folder()` para resaltar el item activo en el sidebar.

**Impacto**: Si hay contexto de estado activo, `get_active_folder()` retorna `None`, y no se resaltará ningún item (correcto, pero hay que asegurar que el estado se resalte en la sección ESTADOS).

**Solución**: Añadir lógica para resaltar el estado activo en la sección ESTADOS cuando `has_state_context()` es `True`.

---

### 12. Persistencia de estado puede incluir paths virtuales

**Ubicación**: `app/services/tab_state_manager.py:65`

**Problema**: `build_app_state()` puede incluir `@state://pending` en `active_tab` si se guarda el estado mientras hay contexto de estado activo.

**Impacto**: Al restaurar, podría intentar activar un tab con path virtual.

**Solución**: 
- `build_app_state()` debe verificar si hay contexto de estado y guardarlo separadamente
- O no guardar `active_tab` si es virtual (solo guardar contexto de estado)

---

### 13. on_folder_changed() compara paths normalizados

**Ubicación**: `app/managers/tab_manager_signals.py:22`

**Problema**:
```python
def on_folder_changed(manager, folder_path: str, files_changed_signal):
    normalized_path = normalize_path(folder_path)
    active_folder = manager.get_active_folder()  # ❌ Puede ser None
    if active_folder and normalize_path(active_folder) == normalized_path:
        files_changed_signal.emit()
```

**Impacto**: Si hay contexto de estado activo, `active_folder` es `None`, y nunca se emitirá el signal (correcto, pero hay que manejar cambios de estado de otra forma).

**Solución**: 
- Si hay contexto de estado activo, escuchar cambios de estado desde `FileStateManager.state_changed`
- O simplemente ignorar eventos del watcher cuando hay contexto de estado (ya que no hay carpeta observada)

---

## Funciones Helper Necesarias

### 1. `is_virtual_path(path: str) -> bool`
```python
def is_virtual_path(path: str) -> bool:
    """Verificar si un path es virtual (no existe en filesystem)."""
    if not path:
        return False
    # Desktop Focus y Trash Focus ya tienen helpers
    if is_desktop_focus(path) or path == TRASH_FOCUS_PATH:
        return True
    # Paths virtuales de estado
    if path.startswith("@state://"):
        return True
    return False
```

**Ubicación sugerida**: `app/services/path_utils.py`

---

### 2. `is_state_context_path(path: str) -> bool`
```python
def is_state_context_path(path: str) -> bool:
    """Verificar si un path es un contexto de estado."""
    return path and path.startswith("@state://")
```

**Ubicación sugerida**: `app/services/path_utils.py`

---

### 3. `extract_state_from_path(path: str) -> Optional[str]`
```python
def extract_state_from_path(path: str) -> Optional[str]:
    """Extraer el estado de un path virtual @state://pending -> pending."""
    if not is_state_context_path(path):
        return None
    return path.replace("@state://", "")
```

**Ubicación sugerida**: `app/services/path_utils.py`

---

## Plan de Acción

### Fase 1: Preparación (Antes de implementar)
1. ✅ Crear funciones helper en `path_utils.py`
2. ✅ Extender `validate_folder()` para reconocer paths virtuales de estado
3. ✅ Modificar `normalize_path()` para preservar paths virtuales
4. ✅ Añadir verificación en `add_tab()` para rechazar paths virtuales

### Fase 2: Implementación Core
5. ✅ Modificar `FileSystemWatcherService` para ignorar paths virtuales
6. ✅ Modificar `TabManager` para manejar contexto de estado
7. ✅ Modificar `select_tab()` para detectar y manejar paths virtuales

### Fase 3: Integración UI
8. ✅ Añadir verificaciones en drag & drop para rechazar en vistas por estado
9. ✅ Modificar sidebar para resaltar estado activo
10. ✅ Asegurar que persistencia maneje contexto de estado correctamente

### Fase 4: Testing
11. ✅ Probar navegación entre carpetas y estados
12. ✅ Probar historial con paths virtuales
13. ✅ Probar que drag & drop se rechaza en vistas por estado
14. ✅ Probar persistencia y restauración de estado

---

## Resumen de Archivos a Modificar

### Críticos (Deben modificarse):
1. `app/services/path_utils.py` - Añadir helpers y modificar normalize_path
2. `app/services/tab_helpers.py` - Extender validate_folder
3. `app/services/filesystem_watcher_service.py` - Ignorar paths virtuales
4. `app/managers/tab_manager_actions.py` - Rechazar paths virtuales en add_tab, manejar en select_tab
5. `app/managers/tab_manager_signals.py` - Manejar contexto de estado en watch_and_emit

### Importantes (Revisar y ajustar):
6. `app/ui/windows/main_window.py` - Revisar usos de get_active_folder()
7. `app/ui/widgets/folder_tree_sidebar.py` - Resaltar estado activo
8. `app/services/tab_state_manager.py` - Manejar contexto de estado en persistencia
9. `app/ui/widgets/file_drop_handler.py` - Añadir verificación explícita de contexto de estado
10. `app/ui/widgets/drag_common.py` - Similar

---

## Notas Finales

- La mayoría del código ya maneja `None` correctamente cuando `get_active_folder()` retorna `None`
- El problema principal es que algunos lugares asumen que si hay un path, es un path del filesystem válido
- Necesitamos ser explícitos: paths virtuales NO son paths del filesystem, son contextos lógicos
- La separación debe ser clara: tabs = paths físicos, contexto de estado = paths virtuales

---

## Comportamiento del Grid - Categorías

### Creación de Categorías

Las categorías del Grid se crean de la siguiente forma:

1. **Lista fija con orden predefinido**: 
   - Las categorías se definen en `app/services/file_category_service.py` mediante `CATEGORY_ORDER`
   - Orden fijo: folder, pdf, documents, sheets, slides, images, video, audio, archives, executables, others
   - Este orden se mantiene siempre, independientemente de qué archivos existan

2. **Creación dinámica solo cuando llega el primer archivo**:
   - La función `get_categorized_files_with_labels()` solo incluye categorías que tienen archivos
   - Si una categoría no tiene archivos, no se muestra en el Grid (línea 160: `if cat in categorized`)
   - Las categorías vacías no ocupan espacio ni se renderizan

**Implementación**:
```146:161:app/services/file_category_service.py
def get_categorized_files_with_labels(file_list: List[str]) -> List[Tuple[str, List[str]]]:
    """
    Group files by category and return as list of (label, files) tuples.
    
    Args:
        file_list: List of file/folder paths.
    
    Returns:
        List of tuples (category_label, file_paths) in fixed order.
    """
    categorized = group_files_by_category(file_list)
    return [
        (get_category_label(cat), categorized[cat])
        for cat in CATEGORY_ORDER
        if cat in categorized
    ]
```

**Ubicación**: `app/services/file_category_service.py:146-161`

