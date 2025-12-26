# Catálogo de Servicios - ClarityDesk Pro

**Fecha:** 29/11/2025  
**Total de servicios:** 73 archivos

---

## 📊 Resumen por Categoría

### 🔴 CRÍTICOS (Con I/O - Tests OBLIGATORIOS según R11)
**Total:** 25 servicios

### 🟡 IMPORTANTES (Lógica de negocio - Tests OBLIGATORIOS según R11)
**Total:** 15 servicios

### 🟢 UTILIDADES (Tests opcionales según R11)
**Total:** 33 servicios

---

## 🔴 SERVICIOS CRÍTICOS (Con I/O)

### Iconos y Renderizado
1. **`icon_service.py`** - ⚠️ SIN TESTS
   - **Responsabilidad:** Iconos nativos de Windows con cache
   - **I/O:** Sistema de archivos + cache en memoria
   - **Tests necesarios:** 6 tests (get_file_icon, get_folder_icon, cache, validación R16)

2. **`icon_render_service.py`** - ✅ TESTS CREADOS (50 tests)
   - **Responsabilidad:** Renderizado con normalización visual
   - **I/O:** Sistema de archivos
   - **Estado:** Tests completos implementados

3. **`preview_service.py`** - ⚠️ SIN TESTS
   - **Responsabilidad:** Preview de archivos (PDF/DOCX)
   - **I/O:** Sistema de archivos
   - **Tests necesarios:** 5 tests

4. **`preview_pdf_service.py`** - ⚠️ SIN TESTS
   - **Responsabilidad:** Preview específico de PDFs
   - **I/O:** Sistema de archivos + procesamiento PDF
   - **Tests necesarios:** 4 tests

5. **`icon_renderer_pdf.py`** - ⚠️ SIN TESTS
   - **Responsabilidad:** Renderizado de iconos PDF
   - **I/O:** Sistema de archivos
   - **Tests necesarios:** 3 tests

6. **`icon_renderer_docx.py`** - ⚠️ SIN TESTS
   - **Responsabilidad:** Renderizado de iconos DOCX
   - **I/O:** Sistema de archivos
   - **Tests necesarios:** 3 tests

7. **`icon_renderer_image.py`** - ⚠️ SIN TESTS
   - **Responsabilidad:** Renderizado de imágenes
   - **I/O:** Sistema de archivos
   - **Tests necesarios:** 3 tests

### Operaciones de Archivos
8. **`file_list_service.py`** - ⚠️ SIN TESTS
   - **Responsabilidad:** Listado de archivos con filtrado
   - **I/O:** Sistema de archivos
   - **Tests necesarios:** 7 tests (get_files, filtrado, stacks, Desktop/Trash Focus)

9. **`file_scan_service.py`** - ⚠️ SIN TESTS
   - **Responsabilidad:** Escaneo de archivos
   - **I/O:** Sistema de archivos
   - **Tests necesarios:** 4 tests (scan_folder_files, scan_desktop_files, scan_trash_files, errores)

10. **`file_delete_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Eliminación de archivos
    - **I/O:** Sistema de archivos
    - **Tests necesarios:** 4 tests (delete_file, trash, permanente, errores)

11. **`file_deletion_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Eliminación alternativa (¿duplicado?)
    - **I/O:** Sistema de archivos
    - **Tests necesarios:** 3 tests

12. **`file_move_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Movimiento de archivos
    - **I/O:** Sistema de archivos
    - **Tests necesarios:** 3 tests (move_file, errores, destino existe)

13. **`file_rename_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Renombrado de archivos
    - **I/O:** Sistema de archivos
    - **Tests necesarios:** 3 tests

14. **`rename_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Renombrado masivo con patrones
    - **I/O:** Sistema de archivos + JSON (templates)
    - **Tests necesarios:** 6 tests (generate_preview, apply_rename, patrones, errores)

15. **`file_creation_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Creación de archivos
    - **I/O:** Sistema de archivos
    - **Tests necesarios:** 3 tests

16. **`folder_creation_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Creación de carpetas
    - **I/O:** Sistema de archivos
    - **Tests necesarios:** 3 tests

17. **`file_open_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Apertura de archivos
    - **I/O:** Sistema de archivos + ejecución externa
    - **Tests necesarios:** 3 tests

### Persistencia (SQLite/JSON)
18. **`file_state_storage.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Persistencia de estados en SQLite
    - **I/O:** Base de datos SQLite
    - **Tests necesarios:** 6 tests (CRUD, batch, rename handling)

19. **`file_state_storage_crud.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Operaciones CRUD de estados
    - **I/O:** Base de datos SQLite
    - **Tests necesarios:** 4 tests

20. **`file_state_storage_batch.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Operaciones batch de estados
    - **I/O:** Base de datos SQLite
    - **Tests necesarios:** 3 tests

21. **`file_state_storage_init.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Inicialización de DB
    - **I/O:** Base de datos SQLite
    - **Tests necesarios:** 2 tests

22. **`file_state_storage_rename.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Manejo de renombrados
    - **I/O:** Base de datos SQLite
    - **Tests necesarios:** 3 tests

23. **`tab_storage_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Persistencia de tabs
    - **I/O:** Archivos JSON
    - **Tests necesarios:** 3 tests (save_tabs, load_tabs, save_active_tab)

24. **`workspace_storage_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Persistencia de workspaces
    - **I/O:** Archivos JSON
    - **Tests necesarios:** 4 tests (save/load workspaces, save/load state)

25. **`state_label_storage.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Persistencia de etiquetas de estado
    - **I/O:** Archivos JSON
    - **Tests necesarios:** 3 tests

### Monitoreo
26. **`filesystem_watcher_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Monitoreo de cambios en sistema de archivos
    - **I/O:** Sistema de archivos + señales Qt
    - **Tests necesarios:** 4 tests (start_watching, stop_watching, señales, detección cambios)

### File Box
27. **`file_box_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Gestión de File Box
    - **I/O:** Sistema de archivos (copia temporal)
    - **Tests necesarios:** 4 tests (create_session, add_files, get_files, cleanup)

28. **`file_box_history_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Historial de File Box
    - **I/O:** Sistema de archivos
    - **Tests necesarios:** 3 tests (save_session, get_recent, cleanup)

---

## 🟡 SERVICIOS IMPORTANTES (Lógica de negocio)

### Filtrado y Categorización
29. **`file_filter_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Filtrado de archivos por extensión
    - **Lógica:** Condicionales complejas
    - **Tests necesarios:** 4 tests (filter_files, includes_folders, includes_executables, empty_extensions)

30. **`file_stack_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Agrupación de archivos en stacks
    - **Lógica:** Algoritmo de agrupación
    - **Tests necesarios:** 3 tests (create_stacks, stack_by_type, empty_list)

31. **`file_category_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Categorización de archivos
    - **Lógica:** Clasificación por tipo
    - **Tests necesarios:** 3 tests (categorize_files, get_categorized, edge_cases)

### Utilidades de Paths
32. **`path_utils.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Utilidades de paths (normalización)
    - **Lógica:** Normalización y validación
    - **Tests necesarios:** 4 tests (normalize_path, case_preservation, separators, edge_cases)

33. **`file_path_utils.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Utilidades específicas de paths de archivos
    - **Lógica:** Validación y transformación
    - **Tests necesarios:** 3 tests

### Tabs y Workspaces
34. **`tab_helpers.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Utilidades de tabs
    - **Lógica:** Validación y búsqueda
    - **Tests necesarios:** 3 tests (validate_folder, find_tab_index, get_tab_display_name)

35. **`tab_history_manager.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Gestión de historial de navegación
    - **Lógica:** Navegación forward/back
    - **Tests necesarios:** 5 tests (go_back, go_forward, update_on_navigate, can_go_back, can_go_forward)

36. **`tab_state_manager.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Gestión de estado de tabs
    - **Lógica:** Construcción y validación de estado
    - **Tests necesarios:** 4 tests (build_app_state, save_app_state, load_app_state, validación)

37. **`workspace_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Lógica de negocio de workspaces
    - **Lógica:** Operaciones de workspaces
    - **Tests necesarios:** 3 tests

### Desktop y Trash
38. **`desktop_path_helper.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Utilidades para Desktop Focus
    - **Lógica:** Detección de Desktop Focus
    - **Tests necesarios:** 3 tests (is_desktop_focus, get_desktop_path, edge_cases)

39. **`desktop_operations.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Operaciones en Desktop
    - **Lógica:** Operaciones específicas de Desktop
    - **Tests necesarios:** 3 tests

40. **`desktop_operations_scan.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Escaneo de Desktop
    - **Lógica:** Escaneo específico
    - **Tests necesarios:** 3 tests

41. **`trash_operations.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Operaciones en Papelera
    - **Lógica:** Operaciones específicas de Trash
    - **Tests necesarios:** 3 tests

42. **`trash_storage.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Gestión de Papelera
    - **Lógica:** Operaciones de Trash Focus
    - **Tests necesarios:** 3 tests

43. **`trash_limits.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Límites de Papelera
    - **Lógica:** Validación de límites
    - **Tests necesarios:** 3 tests

### Configuración
44. **`settings_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Gestión de configuración
    - **I/O:** Archivos JSON
    - **Tests necesarios:** 4 tests (get_setting, set_setting, load_settings, save_settings)

45. **`header_customization_service.py`** - ⚠️ SIN TESTS
    - **Responsabilidad:** Personalización de headers
    - **I/O:** Archivos JSON
    - **Tests necesarios:** 3 tests

---

## 🟢 SERVICIOS DE UTILIDADES (Tests opcionales)

### Helpers de Iconos
46. **`icon_fallback_helper.py`** - Tests opcionales
47. **`icon_normalizer.py`** - Tests opcionales
48. **`icon_processor.py`** - Tests opcionales
49. **`icon_conversion_helper.py`** - Tests opcionales
50. **`icon_extraction_fallbacks.py`** - Tests opcionales
51. **`icon_renderer.py`** - Tests opcionales
52. **`icon_renderer_svg.py`** - Tests opcionales
53. **`icon_renderer_constants.py`** - Tests opcionales (solo constantes)
54. **`icon_batch_worker.py`** - Tests opcionales (QThread worker)

### Helpers de Preview
55. **`preview_scaling.py`** - Tests opcionales
56. **`preview_file_extensions.py`** - Tests opcionales
57. **`pixel_analyzer.py`** - Tests opcionales

### Workers (QThread)
58. **`docx_convert_worker.py`** - Tests opcionales (QThread worker)
59. **`pdf_render_worker.py`** - Tests opcionales (QThread worker)
60. **`pdf_thumbnails_worker.py`** - Tests opcionales (QThread worker)

### Converters
61. **`docx_converter.py`** - Tests opcionales
62. **`pdf_renderer.py`** - Tests opcionales

### Windows Integration
63. **`windows_icon_extractor.py`** - Tests opcionales (integración Windows)
64. **`windows_icon_converter.py`** - Tests opcionales (integración Windows)
65. **`windows_recycle_bin_utils.py`** - Tests opcionales (integración Windows)

### Desktop Helpers
66. **`desktop_drag_ops.py`** - Tests opcionales
67. **`desktop_visibility.py`** - Tests opcionales

### File Box Helpers
68. **`file_box_icon_helper.py`** - Tests opcionales
69. **`file_box_utils.py`** - Tests opcionales

### Extensions y Constants
70. **`file_extensions.py`** - Tests opcionales (solo constantes)

### Init Helpers
71. **`tab_manager_init.py`** - Tests opcionales (inicialización)

---

## 📋 Priorización para Tests

### Fase 1: Críticos (Semana 1) - ~50 tests
1. ✅ `icon_render_service.py` - COMPLETADO (50 tests)
2. `icon_service.py` - 6 tests
3. `file_list_service.py` - 7 tests
4. `file_state_storage.py` (módulos) - 6 tests
5. `rename_service.py` - 6 tests

### Fase 2: I/O Crítico (Semana 2) - ~30 tests
6. `file_delete_service.py` - 4 tests
7. `file_move_service.py` - 3 tests
8. `file_scan_service.py` - 4 tests
9. `file_box_service.py` - 4 tests
10. `filesystem_watcher_service.py` - 4 tests
11. `tab_storage_service.py` - 3 tests
12. `workspace_storage_service.py` - 4 tests
13. `preview_service.py` - 5 tests
14. `preview_pdf_service.py` - 4 tests

### Fase 3: Lógica de Negocio (Semana 3) - ~25 tests
15. `file_filter_service.py` - 4 tests
16. `file_stack_service.py` - 3 tests
17. `file_category_service.py` - 3 tests
18. `path_utils.py` - 4 tests
19. `tab_helpers.py` - 3 tests
20. `tab_history_manager.py` - 5 tests
21. `tab_state_manager.py` - 4 tests
22. `desktop_path_helper.py` - 3 tests

### Fase 4: Resto de Servicios (Semana 4) - ~20 tests
23. Resto de servicios con I/O
24. Resto de servicios con lógica de negocio

---

## 📊 Estadísticas

- **Total servicios:** 73
- **Críticos (I/O):** 28 servicios
- **Importantes (Lógica):** 17 servicios
- **Utilidades:** 28 servicios

- **Tests necesarios (críticos + importantes):** ~120 tests
- **Tests creados:** 50 tests (IconRenderService)
- **Tests pendientes:** ~70 tests

---

## 🎯 Recomendación

**Implementar en este orden:**

1. ✅ **IconRenderService** - COMPLETADO
2. **IconService** - Siguiente (crítico, usado en toda la app)
3. **FileListService** - Muy usado, crítico
4. **RenameService** - I/O crítico, lógica compleja
5. **FileStateStorage** - Persistencia SQLite crítica

---

**Última actualización:** 29/11/2025

