# Análisis: Ventanas Top-Level durante cambio de workspace

## Objetivo
Identificar llamadas a `show()`, `exec()`, `QToolTip`, `QMenu` o creación de `QDialog` que se ejecutan durante:
- Reconstrucción de vistas
- Carga inicial de archivos
- Cambio de workspace

---

## 🔴 CRÍTICOS: show() durante reconstrucción de vistas

### 1. `app/ui/widgets/file_tile_anim.py` - Línea 24
- **Widget**: `FileTile` (tile individual)
- **Llamada**: `tile.show()`
- **Cuándo se ejecuta**: Durante `animate_enter()` cuando se construyen tiles en dock layout
- **Flujo**: 
  - `update_files()` → `FileGridView.update_files()` → `_refresh_tiles()` → `build_dock_layout()` → `animate_tiles_entrance()` → `tile.animate_enter()` → `tile.show()`
- **Problema**: Los tiles se muestran con `setWindowOpacity(0)` y luego `show()`, lo que puede causar que Qt los trate como ventanas top-level temporalmente
- **Impacto**: Flash de ventanas top-level al cambiar workspace con dock style activo

### 2. `app/ui/widgets/file_stack_tile.py` - Línea 241
- **Widget**: `BadgeOverlayWidget` (badge flotante)
- **Llamada**: `self._badge_overlay.show()`
- **Cuándo se ejecuta**: Durante `_update_badge_position()` cuando se actualiza posición del badge
- **Flujo**:
  - `update_files()` → `FileGridView.update_files()` → `_refresh_tiles()` → `build_dock_layout()` → `_build_stack_tiles()` → `create_stack_tile()` → `_setup_badge_overlay()` → `_update_badge_position()` → `badge_overlay.show()`
- **Problema**: Badge overlay se muestra durante reconstrucción de tiles
- **Impacto**: Flash de overlay top-level al cambiar workspace

### 3. `app/ui/widgets/state_badge_widget.py` - Línea 99
- **Widget**: `StateBadgeWidget` (badge de estado)
- **Llamada**: `self.show()`
- **Cuándo se ejecuta**: Durante `_animate_show()` cuando se cambia el estado de un archivo
- **Flujo**:
  - `update_files()` → `FileGridView.update_files()` → `_refresh_tiles()` → tiles creados con estado → `StateBadgeWidget.set_state()` → `_animate_show()` → `self.show()`
- **Problema**: Badge se muestra durante carga inicial de archivos
- **Impacto**: Flash de badge top-level al cambiar workspace

### 4. `app/ui/widgets/file_list_renderer.py` - Línea 75
- **Widget**: `QWidget` (contenedor del checkbox del header)
- **Llamada**: `container.show()`
- **Cuándo se ejecuta**: Durante `_update_header_checkbox_visibility()` cuando scroll horizontal cambia
- **Flujo**:
  - `update_files()` → `FileListView.update_files()` → `_refresh_table()` → `refresh_table()` → scroll events → `_update_header_checkbox_visibility()` → `container.show()`
- **Problema**: Contenedor se muestra durante reconstrucción de tabla
- **Impacto**: Flash menor de contenedor al cambiar workspace

---

## 🟡 MODERADOS: show() en overlays y paneles

### 5. `app/ui/widgets/subfolder_overlay.py` - Línea 170
- **Widget**: `SubfolderOverlay` (overlay de navegación)
- **Llamada**: `self.show()`
- **Cuándo se ejecuta**: Durante `show_at_position()` cuando se muestra overlay de subcarpetas
- **Flujo**: 
  - Usuario arrastra archivo sobre carpeta → `show_at_position()` → `self.show()`
- **Problema**: Overlay se muestra como ventana popup top-level
- **Impacto**: Flash de overlay al mostrar (pero NO durante cambio de workspace, solo durante drag)

### 6. `app/ui/widgets/file_box_history_panel_sidebar.py` - Línea 104
- **Widget**: `QLabel` (etiqueta vacía)
- **Llamada**: `self._empty_label.show()`
- **Cuándo se ejecuta**: Durante `refresh()` cuando no hay sesiones
- **Flujo**:
  - `refresh()` → `_load_sessions()` → si no hay sesiones → `self._empty_label.show()`
- **Problema**: Label se muestra durante refresh del panel
- **Impacto**: Flash menor (pero NO durante cambio de workspace principal)

---

## 🟢 BAJOS: exec() y diálogos (no durante cambio de workspace)

### 7. `app/ui/widgets/file_view_container.py` - Línea 236
- **Widget**: `BulkRenameDialog`
- **Llamada**: `dialog.exec()`
- **Cuándo se ejecuta**: Cuando usuario solicita renombrar archivos (acción manual)
- **Problema**: NO se ejecuta durante cambio de workspace
- **Impacto**: Ninguno (acción manual del usuario)

### 8. `app/ui/widgets/file_view_container.py` - Línea 270
- **Widget**: `QProgressDialog`
- **Llamada**: `progress.show()`
- **Cuándo se ejecuta**: Durante renombrado masivo de archivos (acción manual)
- **Problema**: NO se ejecuta durante cambio de workspace
- **Impacto**: Ninguno (acción manual del usuario)

### 9. `app/ui/windows/main_window.py` - Línea 1001
- **Widget**: `RenameStateDialog`
- **Llamada**: `dialog.exec()`
- **Cuándo se ejecuta**: Cuando usuario solicita renombrar etiqueta (acción manual)
- **Problema**: NO se ejecuta durante cambio de workspace
- **Impacto**: Ninguno (acción manual del usuario)

### 10. `app/ui/windows/main_window.py` - Línea 800
- **Widget**: `QToolTip`
- **Llamada**: `QToolTip.showText()`
- **Cuándo se ejecuta**: Cuando usuario quita elemento del sidebar (acción manual)
- **Problema**: NO se ejecuta durante cambio de workspace
- **Impacto**: Ninguno (acción manual del usuario)

---

## 📋 Resumen por impacto

### 🔴 Alta prioridad (causan flash durante cambio de workspace):

1. **`file_tile_anim.py:24`** - `tile.show()` en animación de entrada
   - **Solución**: Verificar que tile tenga parent antes de `show()`, o usar `setVisible(True)` en lugar de `show()`

2. **`file_stack_tile.py:241`** - `badge_overlay.show()` durante actualización
   - **Solución**: Verificar que badge tenga parent correcto antes de `show()`

3. **`state_badge_widget.py:99`** - `self.show()` en animación de badge
   - **Solución**: Verificar que badge tenga parent antes de `show()`

4. **`file_list_renderer.py:75`** - `container.show()` en header checkbox
   - **Solución**: Verificar que container tenga parent antes de `show()`

### 🟡 Media prioridad (no durante cambio de workspace pero pueden causar flashes):

5. **`subfolder_overlay.py:170`** - Overlay durante drag (acción manual)
6. **`file_box_history_panel_sidebar.py:104`** - Label durante refresh de panel

### 🟢 Baja prioridad (acción manual del usuario):

7-10. Diálogos y tooltips que solo se muestran por acción manual

---

## ✅ Recomendaciones

### Para tiles animados (`file_tile_anim.py`):
- Los tiles ya tienen parent (`parent_view`), pero `show()` puede causar flash
- **Solución**: Usar `setVisible(True)` en lugar de `show()` para widgets embebidos
- O verificar que el widget esté completamente embebido antes de mostrar

### Para badges y overlays:
- Verificar que tengan parent correcto antes de `show()`
- Considerar usar `setVisible(True)` para widgets embebidos

### Para header checkbox:
- El contenedor ya tiene parent (`header`), pero verificar visibilidad antes de `show()`

---

## Total: 4 casos críticos detectados

Todos relacionados con `show()` durante reconstrucción de vistas al cambiar workspace.

