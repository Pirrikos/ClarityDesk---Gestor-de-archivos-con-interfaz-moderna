# Análisis de Tests Necesarios - ClarityDesk Pro

**Fecha:** 29/11/2025  
**Regla aplicada:** R11 - Testing (MANDATORY)

---

## 📊 Resumen Ejecutivo

**Tests existentes:** 16 tests en 4 archivos  
**Tests necesarios:** ~45-60 tests adicionales según R11  
**Cobertura actual:** ~25% de componentes críticos  
**Cobertura objetivo:** 100% de Managers + Services con I/O + Lógica de negocio

---

## ✅ Tests Existentes

### 1. `tests/test_files_controller.py` (5 tests)
- ✅ `test_delete_files_calls_service`
- ✅ `test_delete_files_with_trash_focus`
- ✅ `test_rename_batch_executes_without_exception`
- ✅ `test_rename_batch_handles_exception`
- ✅ `test_move_files_executes_movements`

**Cubre:** `FilesManager` parcialmente

### 2. `tests/test_tabs_controller.py` (6 tests)
- ✅ `test_activate_tab_calls_select_tab`
- ✅ `test_activate_tab_validates_index`
- ✅ `test_go_back_calls_manager`
- ✅ `test_go_forward_calls_manager`
- ✅ `test_can_go_back_returns_manager_value`
- ✅ `test_can_go_forward_returns_manager_value`

**Cubre:** `TabManager` parcialmente

### 3. `tests/test_focus_controller.py` (3 tests)
- ✅ `test_open_focus_with_valid_path`
- ✅ `test_open_focus_rejects_empty_path`
- ✅ `test_close_focus_does_not_break_execution`

**Cubre:** Funcionalidad de focus básica

### 4. `tests/test_workspace_switching.py` (2 tests)
- ✅ `test_workspace_switching_maintains_state`
- ✅ `test_empty_workspace_switching`

**Cubre:** `WorkspaceManager` parcialmente

### 5. `app/tests/test_sidebar_double_click.py` (test manual)
- ✅ Test de UI para sidebar

---

## ❌ Tests Faltantes (Según R11)

### 🔴 CRÍTICO: Managers sin tests completos

#### 1. `FileStateManager` - ⚠️ SIN TESTS
**Responsabilidad:** Gestiona estados de archivos con SQLite  
**Razón:** Manager con I/O (SQLite) + lógica de negocio  
**Tests necesarios (mínimo 3):**
- `test_get_file_state_success` - Obtener estado existente
- `test_set_file_state_persists` - Guardar estado en DB
- `test_get_file_state_nonexistent` - Archivo sin estado
- `test_set_states_batch` - Operación batch
- `test_cleanup_missing_files` - Limpieza de archivos eliminados
- `test_state_changed_signal` - Señal emitida correctamente

#### 2. `WorkspaceManager` - ⚠️ TESTS PARCIALES
**Responsabilidad:** Gestiona workspaces y estado  
**Tests faltantes:**
- `test_create_workspace_success` - Crear workspace
- `test_delete_workspace_success` - Eliminar workspace
- `test_switch_workspace_success` - Cambiar workspace activo
- `test_load_workspace_state` - Cargar estado de workspace
- `test_save_workspace_state` - Guardar estado
- `test_workspace_created_signal` - Señal emitida
- `test_workspace_deleted_signal` - Señal emitida

#### 3. `FileClipboardManager` - ⚠️ SIN TESTS
**Responsabilidad:** Gestiona clipboard de archivos  
**Tests necesarios:**
- `test_copy_files_to_clipboard` - Copiar archivos
- `test_cut_files_to_clipboard` - Cortar archivos
- `test_paste_files_from_clipboard` - Pegar archivos
- `test_clipboard_empty` - Clipboard vacío
- `test_clipboard_operations_signal` - Señales emitidas

#### 4. `FocusManager` - ⚠️ SIN TESTS
**Responsabilidad:** Gestiona focus de archivos  
**Tests necesarios:**
- `test_set_focus_success` - Establecer focus
- `test_clear_focus_success` - Limpiar focus
- `test_focus_changed_signal` - Señal emitida

#### 5. `StateLabelManager` - ⚠️ SIN TESTS
**Responsabilidad:** Gestiona etiquetas de estado  
**Tests necesarios:**
- `test_get_state_labels` - Obtener etiquetas
- `test_set_state_label` - Establecer etiqueta
- `test_remove_state_label` - Eliminar etiqueta

#### 6. `TabManager` - ⚠️ TESTS PARCIALES
**Tests faltantes:**
- `test_add_tab_success` - Añadir tab válido
- `test_add_tab_duplicate` - Tab duplicado
- `test_add_tab_invalid_path` - Path inválido
- `test_remove_tab_success` - Eliminar tab
- `test_remove_tab_by_path` - Eliminar por path
- `test_get_files_from_active_tab` - Obtener archivos
- `test_tabs_changed_signal` - Señal emitida
- `test_active_tab_changed_signal` - Señal emitida

#### 7. `FilesManager` - ⚠️ TESTS PARCIALES
**Tests faltantes:**
- `test_rename_file_success` - Renombrar archivo
- `test_rename_file_error` - Error al renombrar
- `test_rename_file_invalid_path` - Path inválido

---

### 🔴 CRÍTICO: Services con I/O sin tests

#### 8. `IconRenderService` - ⚠️ SIN TESTS (CRÍTICO - acabamos de modificar)
**Responsabilidad:** Renderizado de iconos con validaciones R16  
**Razón:** Lógica crítica recién modificada + validaciones complejas  
**Tests necesarios (mínimo 6):**
- `test_get_file_preview_success` - Preview válido
- `test_get_file_preview_null_pixmap` - Pixmap nulo (R16)
- `test_get_file_preview_zero_size` - Pixmap 0x0 (R16)
- `test_get_file_preview_list_folder` - Carpeta en lista
- `test_get_file_preview_list_file` - Archivo en lista
- `test_get_file_preview_fallback` - Fallback aplicado
- `test_is_valid_pixmap_valid` - Validación pixmap válido
- `test_is_valid_pixmap_null` - Validación pixmap nulo
- `test_is_valid_pixmap_zero_size` - Validación pixmap 0x0
- `test_get_folder_preview_fallbacks` - Múltiples fallbacks

#### 9. `IconService` - ⚠️ SIN TESTS
**Responsabilidad:** Servicio de iconos de Windows  
**Razón:** I/O con sistema de archivos + cache  
**Tests necesarios:**
- `test_get_file_icon_success` - Icono válido
- `test_get_file_icon_cache` - Cache funciona
- `test_get_file_icon_invalid_path` - Path inválido
- `test_get_folder_icon_success` - Icono carpeta
- `test_get_folder_icon_null` - Icono nulo (R16)
- `test_cache_invalidation` - Invalidación de cache

#### 10. `FileListService` - ⚠️ SIN TESTS
**Responsabilidad:** Listado de archivos con filtrado  
**Razón:** I/O con sistema de archivos  
**Tests necesarios:**
- `test_get_files_success` - Listar archivos
- `test_get_files_empty_folder` - Carpeta vacía
- `test_get_files_with_extensions` - Filtrado por extensión
- `test_get_files_with_stacks` - Agrupación en stacks
- `test_get_files_desktop_focus` - Desktop Focus
- `test_get_files_trash_focus` - Trash Focus
- `test_natural_sort_key` - Ordenamiento natural

#### 11. `FileScanService` - ⚠️ SIN TESTS
**Responsabilidad:** Escaneo de archivos  
**Razón:** I/O con sistema de archivos  
**Tests necesarios:**
- `test_scan_folder_files_success` - Escanear carpeta
- `test_scan_folder_files_permission_error` - Error permisos
- `test_scan_desktop_files` - Escanear escritorio
- `test_scan_trash_files` - Escanear papelera

#### 12. `FileStateStorage` (módulos) - ⚠️ SIN TESTS
**Responsabilidad:** Persistencia de estados en SQLite  
**Razón:** I/O con base de datos  
**Tests necesarios:**
- `test_initialize_database` - Inicializar DB
- `test_set_state_persists` - Guardar estado
- `test_get_state_by_path` - Obtener estado
- `test_remove_state` - Eliminar estado
- `test_batch_operations` - Operaciones batch
- `test_rename_handling` - Manejo de renombrados

#### 13. `RenameService` - ⚠️ SIN TESTS
**Responsabilidad:** Renombrado de archivos  
**Razón:** I/O con sistema de archivos  
**Tests necesarios:**
- `test_apply_rename_success` - Renombrar exitoso
- `test_apply_rename_error` - Error al renombrar
- `test_apply_rename_batch` - Renombrar múltiples
- `test_apply_rename_invalid_path` - Path inválido

#### 14. `FileDeleteService` - ⚠️ SIN TESTS
**Responsabilidad:** Eliminación de archivos  
**Razón:** I/O con sistema de archivos  
**Tests necesarios:**
- `test_delete_file_success` - Eliminar archivo
- `test_delete_file_trash` - Eliminar a papelera
- `test_delete_file_permanent` - Eliminación permanente
- `test_delete_file_error` - Error al eliminar

#### 15. `FileMoveService` - ⚠️ SIN TESTS
**Responsabilidad:** Movimiento de archivos  
**Razón:** I/O con sistema de archivos  
**Tests necesarios:**
- `test_move_file_success` - Mover archivo
- `test_move_file_error` - Error al mover
- `test_move_file_target_exists` - Destino existe

#### 16. `FileBoxService` - ⚠️ SIN TESTS
**Responsabilidad:** Gestión de File Box  
**Razón:** I/O con sistema de archivos  
**Tests necesarios:**
- `test_create_session_success` - Crear sesión
- `test_add_files_to_session` - Añadir archivos
- `test_get_session_files` - Obtener archivos

#### 17. `FileBoxHistoryService` - ⚠️ SIN TESTS
**Responsabilidad:** Historial de File Box  
**Razón:** I/O con sistema de archivos  
**Tests necesarios:**
- `test_save_session` - Guardar sesión
- `test_get_recent_sessions` - Obtener sesiones recientes
- `test_cleanup_old_sessions` - Limpieza de sesiones antiguas

#### 18. `WorkspaceStorageService` - ⚠️ SIN TESTS
**Responsabilidad:** Persistencia de workspaces  
**Razón:** I/O con archivos JSON  
**Tests necesarios:**
- `test_save_workspaces` - Guardar workspaces
- `test_load_workspaces` - Cargar workspaces
- `test_save_workspace_state` - Guardar estado
- `test_load_workspace_state` - Cargar estado

#### 19. `TabStorageService` - ⚠️ SIN TESTS
**Responsabilidad:** Persistencia de tabs  
**Razón:** I/O con archivos JSON  
**Tests necesarios:**
- `test_save_tabs` - Guardar tabs
- `test_load_tabs` - Cargar tabs
- `test_save_active_tab` - Guardar tab activo

#### 20. `FileSystemWatcherService` - ⚠️ SIN TESTS
**Responsabilidad:** Monitoreo de cambios en sistema de archivos  
**Razón:** I/O con sistema de archivos + señales Qt  
**Tests necesarios:**
- `test_start_watching` - Iniciar monitoreo
- `test_stop_watching` - Detener monitoreo
- `test_file_changed_signal` - Señal de cambio
- `test_folder_changed_signal` - Señal de cambio carpeta

---

### 🟡 IMPORTANTE: Services con lógica de negocio

#### 21. `FileFilterService` - ⚠️ SIN TESTS
**Responsabilidad:** Filtrado de archivos por extensión  
**Tests necesarios:**
- `test_filter_files_by_extensions` - Filtrado básico
- `test_filter_includes_folders` - Incluir carpetas
- `test_filter_includes_executables` - Incluir ejecutables
- `test_filter_empty_extensions` - Extensiones vacías

#### 22. `FileStackService` - ⚠️ SIN TESTS
**Responsabilidad:** Agrupación de archivos en stacks  
**Tests necesarios:**
- `test_create_file_stacks` - Crear stacks
- `test_stack_by_type` - Agrupar por tipo
- `test_stack_empty_list` - Lista vacía

#### 23. `FileCategoryService` - ⚠️ SIN TESTS
**Responsabilidad:** Categorización de archivos  
**Tests necesarios:**
- `test_categorize_files` - Categorizar archivos
- `test_get_categorized_files` - Obtener categorizados

#### 24. `PathUtils` - ⚠️ SIN TESTS
**Responsabilidad:** Utilidades de paths  
**Tests necesarios:**
- `test_normalize_path` - Normalizar path
- `test_normalize_path_case` - Preservar case
- `test_normalize_path_separators` - Separadores

#### 25. `TabHelpers` - ⚠️ SIN TESTS
**Responsabilidad:** Utilidades de tabs  
**Tests necesarios:**
- `test_validate_folder` - Validar carpeta
- `test_find_tab_index` - Encontrar índice
- `test_get_tab_display_name` - Nombre de tab

---

## 📋 Priorización de Tests

### 🔴 PRIORIDAD ALTA (Implementar primero)

1. **`IconRenderService`** - CRÍTICO (acabamos de modificar con R16)
2. **`FileStateManager`** - Manager con I/O SQLite
3. **`IconService`** - Servicio crítico de iconos
4. **`FileListService`** - Servicio usado en toda la app
5. **`TabManager`** - Completar tests existentes

### 🟡 PRIORIDAD MEDIA

6. **`WorkspaceManager`** - Completar tests existentes
7. **`RenameService`** - I/O crítico
8. **`FileDeleteService`** - I/O crítico
9. **`FileMoveService`** - I/O crítico
10. **`FileStateStorage`** - Persistencia SQLite

### 🟢 PRIORIDAD BAJA

11. Resto de services y managers
12. Utilidades simples

---

## 📝 Plantilla de Test (Según R11)

Cada test debe seguir este patrón:

```python
def test_[component]_[operation]_[scenario]():
    """
    Test [descripción breve].
    
    Escenario: [success/error/edge_case]
    """
    # Arrange
    # Act
    # Assert
```

**Mínimo 3 tests por componente:**
1. `test_*_success` - Happy path
2. `test_*_error` - Manejo de errores
3. `test_*_edge_case` - Casos límite

---

## 🎯 Plan de Implementación

### Fase 1: Tests Críticos (Semana 1)
- [ ] `IconRenderService` (10 tests)
- [ ] `FileStateManager` (6 tests)
- [ ] `IconService` (6 tests)
- [ ] `FileListService` (7 tests)
- [ ] `TabManager` (completar, 8 tests adicionales)

**Total:** ~37 tests

### Fase 2: Tests de I/O (Semana 2)
- [ ] `RenameService` (4 tests)
- [ ] `FileDeleteService` (4 tests)
- [ ] `FileMoveService` (3 tests)
- [ ] `FileStateStorage` (6 tests)
- [ ] `FileScanService` (4 tests)

**Total:** ~21 tests

### Fase 3: Tests de Managers (Semana 3)
- [ ] `WorkspaceManager` (completar, 7 tests)
- [ ] `FileClipboardManager` (5 tests)
- [ ] `FocusManager` (3 tests)
- [ ] `StateLabelManager` (3 tests)
- [ ] `FilesManager` (completar, 3 tests)

**Total:** ~21 tests

### Fase 4: Tests de Services (Semana 4)
- [ ] Resto de services con lógica de negocio
- [ ] Utilidades críticas

**Total:** ~15-20 tests

---

## 📊 Métricas Objetivo

- **Cobertura actual:** ~25%
- **Cobertura objetivo:** 80%+ (100% de componentes críticos)
- **Tests totales necesarios:** ~90-100 tests
- **Tests existentes:** 16 tests
- **Tests a crear:** ~75-85 tests

---

## ✅ Checklist de Validación

Antes de considerar un componente "testeado":

- [ ] Tiene mínimo 3 tests (success, error, edge case)
- [ ] Tests usan ≤3 mocks (según R11)
- [ ] Tests son <30 líneas cada uno (según R11)
- [ ] Setup es <5 líneas (según R11)
- [ ] Tests cubren lógica de negocio principal
- [ ] Tests validan señales Qt (si aplica)
- [ ] Tests validan I/O (si aplica)

---

## 🔧 Herramientas Necesarias

1. **pytest** - Framework de testing (añadir a requirements.txt)
2. **pytest-qt** - Para tests de Qt (opcional pero recomendado)
3. **Script de ejecución** - `run_tests.bat` para Windows

---

## 📌 Notas Importantes

1. **Tests de UI:** Los tests de UI (QWidget, QWindow) son "nice to have" según R11, pero los managers/services son MANDATORY.

2. **Mocks:** Según R11, si un test necesita >3 mocks, el componente debe refactorizarse primero.

3. **I/O:** Todos los servicios con I/O (archivos, DB, sistema) DEBEN tener tests según R11.

4. **Señales Qt:** Los managers que emiten señales deben validar que las señales se emiten correctamente.

5. **R16:** Los tests de `IconRenderService` deben validar específicamente las reglas R16 (pixmaps nulos, 0x0, etc.).

---

## 🚀 Próximos Pasos

1. Añadir `pytest` a `requirements.txt`
2. Crear `run_tests.bat` para ejecutar tests fácilmente
3. Implementar Fase 1 (tests críticos)
4. Validar que todos los tests pasan
5. Continuar con fases siguientes

---

**Última actualización:** 29/11/2025  
**Estado:** Análisis completo - Listo para implementación

