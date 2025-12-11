# 📋 MAPEO DE MÉTODOS - TabManager

## CLASIFICACIÓN POR RESPONSABILIDAD

### A) CORE TAB FLOW (crear, abrir, cerrar, activar)
- `__init__` (líneas 33-60) - Inicialización
- `add_tab` (líneas 62-80) - Crear tab
- `remove_tab` (líneas 82-104) - Cerrar tab por índice
- `remove_tab_by_path` (líneas 106-120) - Cerrar tab por path
- `select_tab` (líneas 122-136) - Activar tab
- `activate_tab` (líneas 269-274) - Wrapper de activación

### B) ESTADO (guardar, restaurar, cambios)
- `_load_state` (líneas 170-181) - Cargar estado
- `_save_state` (líneas 184-186) - Guardar estado
- `restore_state` (líneas 276-291) - Restaurar estado completo
- `_restore_tabs` (líneas 293-295) - Restaurar tabs
- `_restore_history` (líneas 297-299) - Restaurar history
- `_restore_active_tab` (líneas 301-312) - Restaurar tab activo
- `_emit_restored_signals` (líneas 314-318) - Emitir señales

### C) VALIDACIÓN
- No hay validadores locales (todo usa services)

### D) SEÑALES Y CALLBACKS UI
- `_on_folder_changed` (líneas 188-200) - Handler cambios carpeta
- `_watch_and_emit` (líneas 202-206) - Watch y emitir señales

### E) UTILS INTERNOS (getters, navegación)
- `get_active_folder` (líneas 138-142) - Getter
- `get_tabs` (líneas 144-146) - Getter
- `get_active_index` (líneas 148-150) - Getter
- `get_state_manager` (líneas 152-159) - Getter
- `get_watcher` (líneas 208-215) - Getter
- `get_files` (líneas 161-167) - Obtener archivos
- `can_go_back` (líneas 217-219) - Navegación
- `can_go_forward` (líneas 221-223) - Navegación
- `go_back` (líneas 225-236) - Navegación
- `go_forward` (líneas 238-249) - Navegación
- `get_history` (líneas 251-258) - Getter
- `get_history_index` (líneas 260-267) - Getter

---

## PLAN DE EXTRACCIÓN

### Módulo 1: `tab_manager_state.py` (B - ESTADO)
**Métodos a extraer:**
- `_load_state`
- `_save_state`
- `restore_state`
- `_restore_tabs`
- `_restore_history`
- `_restore_active_tab`
- `_emit_restored_signals`

**Dependencias necesarias:**
- `TabStateManager`
- `TabHistoryManager`
- `find_tab_index` (service)
- `normalize_path` (service)
- Acceso a `self._tabs`, `self._active_index`, `self._watcher`
- Acceso a señales: `self.tabsChanged`, `self.activeTabChanged`

### Módulo 2: `tab_manager_navigation.py` (E - NAVEGACIÓN)
**Métodos a extraer:**
- `can_go_back`
- `can_go_forward`
- `go_back`
- `go_forward`
- `get_history`
- `get_history_index`

**Dependencias necesarias:**
- `TabNavigationHandler`
- Acceso a `self._active_index`

---

## MÉTODOS QUE PERMANECEN EN TabManager

### Core Tab Flow (A):
- `__init__`
- `add_tab`
- `remove_tab`
- `remove_tab_by_path`
- `select_tab`
- `activate_tab`

### Señales y Callbacks (D):
- `_on_folder_changed`
- `_watch_and_emit`

### Utils (E):
- `get_active_folder`
- `get_tabs`
- `get_active_index`
- `get_state_manager`
- `get_watcher`
- `get_files`

---

## ESTIMACIÓN DE LÍNEAS

**Actual:** ~318 líneas

**Después de extracción:**
- `tab_manager.py`: ~150 líneas (mantiene core flow + utils + señales)
- `tab_manager_state.py`: ~80 líneas (métodos de estado)
- `tab_manager_navigation.py`: ~30 líneas (métodos de navegación)

**Total:** ~260 líneas (distribuidas en 3 archivos)

