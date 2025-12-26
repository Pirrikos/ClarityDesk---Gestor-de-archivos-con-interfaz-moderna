# CLASIFICACIÓN DE TESTS - CLARITYDESK PRO

> **📋 DOCUMENTO OFICIAL DE REFERENCIA**  
> Este documento define la gobernanza del sistema de tests del proyecto.  
> **Consultar antes de modificar cualquier test.**  
> Última actualización: 2025-12-26

---

## Resumen Ejecutivo

**Total de archivos de test:** 29  
**Total de tests:** ~440

**Distribución:**
- **CRÍTICOS:** Tests que validan comportamiento visible, persistencia, robustez, reglas explícitas (R16)
- **FLEXIBLES:** Tests que validan implementación interna, estructura, secuencia, métodos privados, cache interno
- **AUXILIARES:** Fixtures, helpers, mocks, setup

**Principio fundamental:**
- **CRÍTICOS** = Contrato de Producto (qué hace la app)
- **FLEXIBLES** = Implementación Interna (cómo lo hace)
- **AUXILIARES** = Infraestructura de testing

**Regla de oro:**
- Si un test CRÍTICO falla → cambiar código de producción
- Si un test FLEXIBLE falla → evaluar si es refactor justificado
- Tests AUXILIARES pueden modificarse libremente

---

## CATEGORÍA: AUXILIARES (Infraestructura de Test)

### `tests/conftest.py`
**Categoría:** AUXILIAR  
**Qué contiene:** Fixtures compartidas (`qapp`, `temp_folder`, `temp_storage`, `temp_file`, `temp_files`)  
**Qué regla protege:** Ninguna directamente - infraestructura de testing  
**Si falla:** Cambiar el test (fixture)  
**Justificación:** Fixtures de pytest, pueden modificarse libremente para mejorar tests.

---

## CATEGORÍA: CRÍTICOS (Contrato de Producto)

### `tests/test_path_utils.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de `normalize_path()` - normalización de rutas, preservación de case, manejo de separadores  
**Qué regla protege:** 
- Regla 4 (DRY): Normalización centralizada
- Regla 19: Manejo seguro de paths en Windows
- Comportamiento visible: Paths deben normalizarse correctamente para comparaciones  
**Si falla:** Cambiar la app (el servicio debe funcionar correctamente)  
**Justificación:** La normalización de paths afecta directamente la funcionalidad visible (búsqueda, comparación, persistencia).

---

### `tests/test_file_delete_service.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de eliminación de archivos, papelera, eliminación permanente, manejo de errores  
**Qué regla protege:**
- Regla 19: Manejo seguro de operaciones de archivo
- Regla 10: Manejo explícito de errores
- Comportamiento visible: El usuario debe poder eliminar archivos correctamente  
**Si falla:** Cambiar la app (la eliminación debe funcionar)  
**Justificación:** Operación crítica visible para el usuario. Fallos aquí = pérdida de datos.

---

### `tests/test_file_move_service.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de movimiento de archivos, resolución de conflictos, integración con watcher  
**Qué regla protege:**
- Regla 19: Manejo seguro de operaciones de archivo
- Regla 21: Integración con file watcher
- Comportamiento visible: El usuario debe poder mover archivos  
**Si falla:** Cambiar la app  
**Justificación:** Operación crítica visible. Fallos = archivos perdidos o duplicados.

---

### `tests/test_file_state_storage.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de persistencia SQLite (CRUD, batch, rename handling, inicialización)  
**Qué regla protege:**
- Regla 22: Persistencia SQLite para estados de archivos
- Regla 19: Manejo seguro de base de datos
- Persistencia visible: Los estados de archivos deben persistir entre sesiones  
**Si falla:** Cambiar la app (la persistencia debe funcionar)  
**Justificación:** La persistencia es crítica - sin ella, el usuario pierde estados de archivos.

---

### `tests/test_file_state_manager.py` (CLASIFICACIÓN DETALLADA)
**Categoría:** CRÍTICO (parcial) + FLEXIBLE (parcial)  
**Qué contiene:** Tests de gestión de estados (get/set), cache, señales Qt, persistencia  

**Tests CRÍTICOS:**
- `TestGetFileState` (todos) - Comportamiento visible (obtener estado)
- `TestSetFileState` (todos) - Comportamiento visible (establecer estado)
- `TestSetFilesState` (todos) - Comportamiento visible (establecer múltiples)
- `TestCleanupMissingFiles` (todos) - Robustez (limpieza de archivos faltantes)
- `TestSetFileState::test_set_file_state_emits_signal` - Regla 16 (señales Qt)
- `TestSetFilesState::test_set_files_state_emits_signal` - Regla 16 (señales Qt)
- `TestEdgeCases` (todos) - Robustez ante edge cases

**Tests FLEXIBLES:**
- `TestCache::test_cache_stores_states` - Inspecciona `_state_cache` (estructura interna)
- `TestCache::test_cache_invalidates_on_file_change` - Inspecciona `_state_cache`, usa `time.sleep()`, llama a `_get_file_id()` (método privado)
- `TestCache::test_cache_invalidates_on_file_change` - Depende de implementación interna de cache

**Qué regla protege:**
- Regla 16: Señales Qt correctas - CRÍTICO
- Regla 22: Persistencia de estados - CRÍTICO
- Regla 23: Cache de estados - FLEXIBLE (optimización interna)
- Comportamiento visible: Los estados de archivos deben funcionar correctamente - CRÍTICO

**Si falla:** 
- Tests CRÍTICOS: Cambiar la app
- Tests FLEXIBLES: Evaluar si es refactor justificado

**Justificación:** La gestión de estados es CRÍTICA (comportamiento visible). El cache es FLEXIBLE porque es optimización interna que puede refactorizarse sin cambiar el comportamiento visible.

---

### `tests/test_tab_storage_service.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de guardado/carga de estado de tabs en JSON  
**Qué regla protege:**
- Regla 22: Persistencia JSON para tabs
- Persistencia visible: Los tabs deben restaurarse entre sesiones  
**Si falla:** Cambiar la app  
**Justificación:** Persistencia crítica - sin ella, el usuario pierde sus tabs abiertos.

---

### `tests/test_tab_manager_complete.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de `add_tab`, `remove_tab`, `select_tab`, `get_files`, señales Qt  
**Qué regla protege:**
- Regla 16: Señales Qt correctas
- Regla 1: Separación de capas (manager)
- Comportamiento visible: Los tabs deben funcionar correctamente  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad core visible - gestión de tabs es la interfaz principal.

---

### `tests/test_workspace_storage_service.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de persistencia de workspaces (guardado/carga de estado)  
**Qué regla protege:**
- Regla 22: Persistencia de workspaces
- Persistencia visible: Los workspaces deben persistir entre sesiones  
**Si falla:** Cambiar la app  
**Justificación:** Persistencia crítica - sin ella, el usuario pierde sus workspaces.

---

### `tests/test_workspace_manager_complete.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de creación, eliminación, cambio de workspace, señales Qt  
**Qué regla protege:**
- Regla 16: Señales Qt correctas
- Regla 1: Separación de capas (manager)
- Comportamiento visible: Los workspaces deben funcionar correctamente  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad core visible - workspaces son una feature principal.

---

### `tests/test_workspace_switching.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de cambio entre workspaces, mantenimiento de estado independiente  
**Qué regla protege:**
- Regla 22: Persistencia de estado por workspace
- Comportamiento visible: El cambio de workspace debe mantener estados independientes  
**Si falla:** Cambiar la app  
**Justificación:** Feature crítica visible - los workspaces deben mantener estados separados.

---

### `tests/test_file_list_service.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de listado de archivos, filtrado por extensiones, orden natural, Desktop/Trash focus  
**Qué regla protege:**
- Regla 1: Separación de capas (service)
- Comportamiento visible: El listado de archivos debe funcionar correctamente  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad core visible - sin listado correcto, la app no funciona.

---

### `tests/test_file_scan_service.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de escaneo de carpetas, Desktop, Trash, manejo de errores  
**Qué regla protege:**
- Regla 19: Manejo seguro de operaciones de archivo
- Regla 10: Manejo explícito de errores
- Comportamiento visible: El escaneo debe funcionar correctamente  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad core visible - el escaneo es necesario para mostrar archivos.

---

### `tests/test_file_box_service.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de preparación de archivos para drag & drop, manejo de errores  
**Qué regla protege:**
- Regla 19: Manejo seguro de operaciones de archivo
- Comportamiento visible: El drag & drop debe funcionar correctamente  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad visible - drag & drop es una feature principal.

---

### `tests/test_file_clipboard_manager.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de clipboard (copy/cut), singleton pattern, estado compartido  
**Qué regla protege:**
- Regla 5: Dependency Injection (singleton)
- Comportamiento visible: El clipboard debe funcionar correctamente  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad visible - copy/paste es crítica.

---

### `tests/test_state_label_manager.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de etiquetas personalizadas de estados, señales Qt  
**Qué regla protege:**
- Regla 16: Señales Qt correctas
- Comportamiento visible: Las etiquetas personalizadas deben funcionar  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad visible - las etiquetas se muestran al usuario.

---

### `tests/test_rename_service.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de renombrado de archivos, preview de renombrado, patrones  
**Qué regla protege:**
- Regla 19: Manejo seguro de operaciones de archivo
- Comportamiento visible: El renombrado debe funcionar correctamente  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad visible - renombrado es una operación crítica.

---

### `tests/test_files_manager_complete.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de operaciones de archivos (delete, rename, move, restore), integración  
**Qué regla protege:**
- Regla 1: Separación de capas (manager)
- Regla 19: Manejo seguro de operaciones
- Comportamiento visible: Las operaciones de archivos deben funcionar  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad core visible - operaciones de archivos son críticas.

---

### `tests/test_focus_manager.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de gestión de focus (open/close/reopen), señales Qt  
**Qué regla protege:**
- Regla 16: Señales Qt correctas
- Regla 1: Separación de capas (manager)
- Comportamiento visible: El focus debe funcionar correctamente  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad visible - el focus es parte de la navegación.

---

### `tests/test_tab_history_manager.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de historial de navegación (back/forward), restauración de estado  
**Qué regla protege:**
- Regla 22: Persistencia de historial
- Comportamiento visible: El historial debe funcionar correctamente  
**Si falla:** Cambiar la app  
**Justificación:** Funcionalidad visible - back/forward es una feature principal.

---

### `tests/test_icon_service.py` (CLASIFICACIÓN DETALLADA)
**Categoría:** CRÍTICO (parcial) + FLEXIBLE (parcial)  
**Qué contiene:** Tests de obtención de iconos Windows, validación de pixmaps (R16), cache, métodos privados  

**Tests CRÍTICOS:**
- `TestIsValidPixmap` - Validación R16 (comportamiento visible: evita iconos rotos)
- `TestGetFileIcon::test_get_file_icon_success` - Comportamiento visible
- `TestGetFileIcon::test_get_file_icon_invalid_path` - Robustez (fallback visible)
- `TestGetFileIcon::test_get_file_icon_validates_pixmap` - Regla R16 explícita
- `TestGetFileIcon::test_get_file_icon_no_size` - Robustez
- `TestGetFolderIcon` (todos) - Comportamiento visible
- `TestEdgeCases` (todos) - Robustez ante edge cases

**Tests FLEXIBLES:**
- `TestGetFileIcon::test_get_file_icon_cache` - Inspecciona `_icon_cache` (estructura interna)
- `TestCache` (todos) - Inspecciona estructura interna de cache
- `TestGetBestQualityPixmap` (todos) - Llama a método privado `_get_best_quality_pixmap`

**Qué regla protege:**
- Regla 16: Validación de pixmaps (no null, no 0x0) - CRÍTICO
- Comportamiento visible: Los iconos deben mostrarse correctamente - CRÍTICO
- Regla 23: Cache de iconos - FLEXIBLE (optimización interna)

**Si falla:** 
- Tests CRÍTICOS: Cambiar la app
- Tests FLEXIBLES: Evaluar si es refactor justificado

**Justificación:** Los iconos visibles son CRÍTICOS. El cache y métodos privados son FLEXIBLES porque testean implementación interna.

---

### `tests/test_icon_render_service.py` (CLASIFICACIÓN DETALLADA)
**Categoría:** CRÍTICO (parcial) + FLEXIBLE (parcial)  
**Qué contiene:** Tests de renderizado de iconos, previews, validación de pixmaps, métodos privados  

**Tests CRÍTICOS:**
- `TestIsValidPixmap` - Validación R16 (comportamiento visible)
- `TestGetFilePreview` (todos) - Comportamiento visible (grid view)
- `TestGetFilePreviewList` (todos) - Comportamiento visible (list view)
- `TestGridVsListView::test_both_views_return_valid_pixmaps` - Regla R16 explícita
- `TestEdgeCases` (todos) - Robustez ante edge cases
- `TestErrorHandling` (todos) - Robustez sin crash

**Tests FLEXIBLES:**
- `TestGetFolderPreview` (todos) - Llama a método privado `_get_folder_preview`
- `TestScaleFolderIcon` (todos) - Llama a método privado `_scale_folder_icon`
- `TestApplyFolderFallbacks` (todos) - Llama a método privado `_apply_folder_fallbacks`
- `TestGetBestQualityPixmap` (todos) - Llama a método privado `_get_best_quality_pixmap`
- `TestGridVsListView::test_grid_preview_has_normalization` - No valida explícitamente, solo comentario
- `TestGridVsListView::test_list_preview_no_overlay` - No valida explícitamente, solo comentario

**Qué regla protege:**
- Regla 16: Validación de pixmaps - CRÍTICO
- Comportamiento visible: Los previews deben mostrarse correctamente - CRÍTICO
- Implementación interna: Métodos privados - FLEXIBLE

**Si falla:** 
- Tests CRÍTICOS: Cambiar la app
- Tests FLEXIBLES: Evaluar si es refactor justificado

**Justificación:** Los previews visibles son CRÍTICOS. Los métodos privados son FLEXIBLES porque testean implementación interna que puede refactorizarse.

---

## CATEGORÍA: FLEXIBLES (Implementación Interna)

### `tests/test_file_filter_service.py`
**Categoría:** FLEXIBLE  
**Qué contiene:** Tests de filtrado por extensiones, detección de ejecutables, inclusión de carpetas  
**Qué regla protege:**
- Regla 1: Separación de capas (service)
- Implementación interna: La lógica de filtrado puede refactorizarse  
**Si falla:** Evaluar si es refactor justificado o bug real  
**Justificación:** El filtrado es interno - mientras el resultado sea correcto, la implementación puede cambiar.

---

### `tests/test_file_stack_service.py`
**Categoría:** FLEXIBLE  
**Qué contiene:** Tests de agrupación de archivos en stacks, ordenamiento natural  
**Qué regla protege:**
- Regla 1: Separación de capas (service)
- Implementación interna: La lógica de agrupación puede refactorizarse  
**Si falla:** Evaluar si es refactor justificado  
**Justificación:** La agrupación es interna - mientras los stacks se muestren correctamente, la implementación puede cambiar.

---

### `tests/test_tab_helpers.py`
**Categoría:** FLEXIBLE  
**Qué contiene:** Tests de funciones helper (find_tab_index, validate_folder, get_tab_display_name)  
**Qué regla protege:**
- Regla 4: DRY (helpers centralizados)
- Implementación interna: Helpers pueden refactorizarse  
**Si falla:** Evaluar si es refactor justificado  
**Justificación:** Helpers son internos - mientras la funcionalidad pública funcione, pueden cambiar.

---

### `tests/test_tabs_controller.py`
**Categoría:** FLEXIBLE  
**Qué contiene:** Tests de delegación de métodos (activate_tab → select_tab, go_back → history_manager)  
**Qué regla protege:**
- Regla 1: Separación de capas (controller)
- Implementación interna: La delegación puede cambiar si hay refactor  
**Si falla:** Evaluar si es refactor justificado  
**Justificación:** Tests de delegación son internos - mientras el comportamiento público funcione, pueden cambiar.

---

### `tests/test_files_controller.py`
**Categoría:** FLEXIBLE  
**Qué contiene:** Tests de delegación de operaciones de archivos a servicios  
**Qué regla protege:**
- Regla 1: Separación de capas (controller)
- Implementación interna: La delegación puede cambiar  
**Si falla:** Evaluar si es refactor justificado  
**Justificación:** Tests de delegación son internos.

---

### `tests/test_focus_controller.py`
**Categoría:** FLEXIBLE  
**Qué contiene:** Tests de delegación de operaciones de focus a FocusManager  
**Qué regla protege:**
- Regla 1: Separación de capas (controller)
- Implementación interna: La delegación puede cambiar  
**Si falla:** Evaluar si es refactor justificado  
**Justificación:** Tests de delegación son internos.

---

### `app/tests/test_sidebar_double_click.py` y `app/tests/test_sidebar_double_click_sequence.py`
**Categoría:** CRÍTICO  
**Qué contiene:** Tests de doble clic en sidebar - validan que el doble clic selecciona la carpeta correcta y emite señal `folder_selected`  
**Qué regla protege:**
- Regla 16: Señales Qt correctas (`folder_selected`)
- Comportamiento visible: El doble clic debe seleccionar la carpeta correcta  
**Si falla:** Cambiar la app  
**Justificación:** Comportamiento visible crítico - el doble clic en sidebar es una interacción principal del usuario.

---

## DECISIONES DE GOBERNANZA

### ¿Qué es Contrato de Producto?

**Contrato de Producto** = Comportamiento visible para el usuario final que define qué hace la aplicación y cómo debe funcionar.

**Ejemplos de Contrato de Producto:**
- Los iconos se muestran correctamente en la UI
- Los archivos se eliminan cuando el usuario lo solicita
- Los tabs se restauran al reiniciar la aplicación
- Los estados de archivos persisten entre sesiones
- La aplicación no crashea ante errores esperados

**Tests CRÍTICOS protegen el Contrato de Producto.**

### ¿Qué es Implementación Interna?

**Implementación Interna** = Cómo se logra el comportamiento, detalles técnicos que el usuario no ve ni le importan.

**Ejemplos de Implementación Interna:**
- Estructura interna de caché (`_icon_cache`, `_state_cache`)
- Métodos privados (`_get_*`, `_apply_*`, `_scale_*`)
- Algoritmos de agrupación o filtrado específicos
- Secuencia de llamadas internas entre componentes
- Optimizaciones de rendimiento

**Tests FLEXIBLES validan Implementación Interna.**

### ¿Por qué esta Separación Protege el Proyecto?

1. **Refactoring Seguro:**
   - Los tests CRÍTICOS permiten refactorizar implementación interna sin romper el contrato
   - Los tests FLEXIBLES pueden ajustarse cuando hay refactor justificado

2. **Detección de Bugs Reales:**
   - Si un test CRÍTICO falla = bug real en comportamiento visible
   - Si un test FLEXIBLE falla = evaluar si es bug o refactor necesario

3. **Mantenibilidad:**
   - Tests CRÍTICOS son estables y no cambian frecuentemente
   - Tests FLEXIBLES pueden evolucionar con la arquitectura

4. **Claridad de Responsabilidades:**
   - CRÍTICOS = "¿Qué hace la app?" (Product Owner)
   - FLEXIBLES = "¿Cómo lo hace?" (Desarrolladores)

---

## CAMBIOS REALIZADOS EN CLASIFICACIÓN

### Tests Reclasificados de CRÍTICO a FLEXIBLE

#### `tests/test_icon_service.py`

**Reclasificados:**
- `TestGetFileIcon::test_get_file_icon_cache` → FLEXIBLE
  - **Justificación:** Inspecciona estructura interna `_icon_cache` (línea 192). El cache es optimización interna, no comportamiento visible.

- `TestCache` (todos los tests) → FLEXIBLE
  - **Justificación:** Testean estructura interna de cache (`_icon_cache`). El usuario no ve si algo está cacheado o no. Si se cambia la implementación del cache (ej: usar otro mecanismo), estos tests fallarían aunque el comportamiento visible sea correcto.

- `TestGetBestQualityPixmap` (todos) → FLEXIBLE
  - **Justificación:** Llama a método privado `_get_best_quality_pixmap`. Si se refactoriza el método privado, el test fallaría aunque el comportamiento público funcione correctamente.

#### `tests/test_icon_render_service.py`

**Reclasificados:**
- `TestGetFolderPreview` (todos) → FLEXIBLE
  - **Justificación:** Llama a método privado `_get_folder_preview`. El comportamiento visible se testea en `TestGetFilePreview` a través de la API pública.

- `TestScaleFolderIcon` (todos) → FLEXIBLE
  - **Justificación:** Llama a método privado `_scale_folder_icon`. Si se refactoriza el método privado, el test fallaría aunque el comportamiento público funcione.

- `TestApplyFolderFallbacks` (todos) → FLEXIBLE
  - **Justificación:** Llama a método privado `_apply_folder_fallbacks`. El comportamiento visible (fallbacks funcionan) se testea indirectamente en `TestGetFilePreview` y `TestGetFilePreviewList`.

- `TestGetBestQualityPixmap` (todos) → FLEXIBLE
  - **Justificación:** Llama a método privado `_get_best_quality_pixmap`. Si se refactoriza, el test fallaría aunque el comportamiento público funcione.

- `TestGridVsListView::test_grid_preview_has_normalization` → FLEXIBLE
  - **Justificación:** Solo tiene comentario sobre normalización pero no valida explícitamente. No protege comportamiento visible de forma verificable.

- `TestGridVsListView::test_list_preview_no_overlay` → FLEXIBLE
  - **Justificación:** Solo tiene comentario sobre overlay pero no valida explícitamente. No protege comportamiento visible de forma verificable.

**Mantenidos como CRÍTICOS:**
- `TestIsValidPixmap` - Regla R16 explícita (comportamiento visible: evita iconos rotos)
- `TestGetFilePreview` (todos) - Comportamiento visible (grid view)
- `TestGetFilePreviewList` (todos) - Comportamiento visible (list view)
- `TestGridVsListView::test_both_views_return_valid_pixmaps` - Regla R16 explícita
- `TestEdgeCases` (todos) - Robustez ante edge cases sin crash
- `TestErrorHandling` (todos) - Robustez sin crash

---

#### `tests/test_file_state_manager.py`

**Reclasificados:**
- `TestCache::test_cache_stores_states` → FLEXIBLE
  - **Justificación:** Inspecciona estructura interna `_state_cache` (línea 233). El cache es optimización interna, no comportamiento visible.

- `TestCache::test_cache_invalidates_on_file_change` → FLEXIBLE
  - **Justificación:** 
    - Inspecciona estructura interna `_state_cache` indirectamente
    - Llama a método privado `_get_file_id()` (línea 246)
    - Usa `time.sleep(1.1)` (línea 241) - dependencia de tiempo real frágil
    - No valida comportamiento observable, solo estructura interna
    - Si se refactoriza el cache o cómo se calcula `file_id`, el test fallaría aunque el comportamiento público funcione

**Mantenidos como CRÍTICOS:**
- `TestGetFileState` (todos) - Comportamiento visible (obtener estado)
- `TestSetFileState` (todos) - Comportamiento visible (establecer estado)
- `TestSetFilesState` (todos) - Comportamiento visible (establecer múltiples)
- `TestCleanupMissingFiles` (todos) - Robustez (limpieza de archivos faltantes)
- `TestSetFileState::test_set_file_state_emits_signal` - Regla 16 (señales Qt)
- `TestSetFilesState::test_set_files_state_emits_signal` - Regla 16 (señales Qt)
- `TestEdgeCases` (todos) - Robustez ante edge cases

**Test CRÍTICO propuesto (no implementado):**
- `TestFileStateConsistency::test_file_state_remains_accessible_after_file_modification`
  - **Propósito:** Validar contrato de producto: "Si un archivo cambia, el estado debe seguir siendo accesible correctamente"
  - **Diseño:** Ver `PROPUESTA_TEST_CRITICO_FILE_STATE.md`
  - **Características:**
    - Solo usa API pública (`get_file_state()`, `set_file_state()`)
    - No inspecciona cache ni métodos privados
    - No usa `time.sleep()` (usa mocks o acepta variabilidad natural)
    - Valida comportamiento observable, no implementación interna

---

## RESUMEN POR CATEGORÍA

### CRÍTICOS (~22 archivos completos + parciales)
- Tests de persistencia (storage, state)
- Tests de operaciones de archivo visibles (delete, move, rename)
- Tests de funcionalidad core visible (tabs, workspaces, focus)
- Tests de señales Qt (comportamiento visible)
- Tests de validación de datos (R16: pixmaps válidos)
- Tests de comportamiento visible de iconos/previews (API pública)
- Tests de robustez ante edge cases sin crash

**Regla de oro:** Si falla un test CRÍTICO, cambiar la app, no el test.

### FLEXIBLES (~8 archivos completos + parciales)
- Tests de delegación (controllers)
- Tests de helpers internos
- Tests de lógica de agrupación/filtrado interno
- Tests de estructura interna de cache
- Tests de métodos privados
- Tests que inspeccionan implementación interna

**Regla de oro:** Si falla un test FLEXIBLE, evaluar si es refactor justificado antes de cambiar.

### AUXILIARES (1 archivo)
- Fixtures compartidas

**Regla de oro:** Pueden modificarse libremente para mejorar tests.

---

## PROTOCOLO DE USO

### 🔒 PROMPT PERMANENTE (Guardar para uso futuro)

**Antes de ejecutar o modificar tests:**

1. **Consultar `CLASIFICACION_TESTS.md`**
   - Verificar categoría del test (CRÍTICO / FLEXIBLE / AUXILIAR)

2. **Si el test es CRÍTICO:**
   - ✅ Define el contrato del producto
   - ❌ NO debe modificarse
   - ✅ Si falla → cambiar código de producción
   - ✅ Si falla → es un bug real en comportamiento visible

3. **Si el test es FLEXIBLE:**
   - ✅ Puede ajustarse por refactor justificado
   - ✅ Si falla → evaluar si es bug o refactor necesario
   - ✅ Puede testear implementación interna

4. **Si el test es AUXILIAR:**
   - ✅ Puede modificarse libremente
   - ✅ Son fixtures, helpers, mocks

### Ejemplos de Aplicación

**Ejemplo 1: Test CRÍTICO falla**
```
Test: test_get_file_icon_success
Categoría: CRÍTICO
Acción: Cambiar código de producción (IconService)
NO cambiar el test
```

**Ejemplo 2: Test FLEXIBLE falla**
```
Test: test_cache_stores_icons
Categoría: FLEXIBLE
Acción: Evaluar si es refactor justificado
Si se cambió implementación de cache → ajustar test
Si es bug real → cambiar código
```

**Ejemplo 3: Refactor de método privado**
```
Método: _get_best_quality_pixmap (privado)
Tests afectados: TestGetBestQualityPixmap (FLEXIBLE)
Acción: Ajustar tests FLEXIBLES si es necesario
Verificar que tests CRÍTICOS (API pública) siguen pasando
```

---

## CONFLICTOS DETECTADOS

### Ninguno detectado
Todos los tests CRÍTICOS validan comportamiento correcto y visible.

---

## RECOMENDACIONES

1. **Mantener tests CRÍTICOS intactos** - Son el contrato de producto
2. **Documentar tests FLEXIBLES** - Indicar que pueden ajustarse en refactors
3. **Consultar clasificación antes de modificar tests** - Usar protocolo de uso
4. **Separar tests por responsabilidad** - CRÍTICOS = comportamiento, FLEXIBLES = implementación

