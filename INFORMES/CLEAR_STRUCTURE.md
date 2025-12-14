# 📐 ESTRUCTURA CLARA DEL PROYECTO - ClarityDesk Pro

**Propósito:** Documentación rápida para que cualquier IA entienda el proyecto con mínimo consumo de tokens.

---

## 🎯 VISIÓN GENERAL

**ClarityDesk Pro** es un gestor de archivos con interfaz moderna desarrollado en PySide6 (Qt).  
**Arquitectura:** Separación estricta en 4 capas (models → services → managers → ui)

---

## 📁 ESTRUCTURA DE CARPETAS

```
app/
├── models/          # Datos puros (sin lógica, sin Qt, sin I/O)
├── services/        # Lógica de negocio (operaciones, validaciones)
├── managers/        # Orquestación de alto nivel (coordinan services)
└── ui/              # Interfaz visual (widgets, ventanas)
    ├── widgets/     # Componentes reutilizables
    └── windows/     # Ventanas principales
```

### Regla de Imports (CRÍTICA)
- `models/` → Solo stdlib + typing
- `services/` → Solo `models/`
- `managers/` → `models/` + `services/`
- `ui/` → Todo (models + services + managers)

---

## 🔍 MÓDULOS PRINCIPALES

### MODELS (2 archivos)
**Responsabilidad:** Estructuras de datos puras

- `file_operation_result.py` - Resultado de operaciones (success/error)
- `file_stack.py` - Agrupación de archivos duplicados

### SERVICES (61 archivos - organizados por dominio)

#### Tab Management (~10 archivos)
- `tab_state_manager.py` - Estado de tabs (persistencia)
- `tab_storage_service.py` - Almacenamiento JSON
- `tab_history_manager.py` - Historial de navegación
- `tab_navigation_handler.py` - Navegación back/forward
- `tab_validator.py` - Validación de rutas
- `tab_utils.py` - Utilidades (consolidar con otros helpers)
- `tab_path_normalizer.py` - Normalización (consolidar)
- `tab_finder.py` - Búsqueda (consolidar)

#### File Operations (~6 archivos)
- `file_list_service.py` - Listado de archivos
- `file_move_service.py` - Movimiento
- `file_delete_service.py` - Eliminación
- `file_rename_service.py` - Renombrado
- `file_open_service.py` - Apertura con sistema
- `file_scan_service.py` - Escaneo de carpetas

#### Icons & Preview (~15 archivos)
- `icon_service.py` - Servicio principal (grande, ~260 líneas)
- `preview_service.py` - Generación de previews
- `icon_renderer.py` - Renderizado base
- `icon_renderer_pdf.py` - PDFs
- `icon_renderer_image.py` - Imágenes
- `icon_renderer_svg.py` - SVGs
- `icon_renderer_docx.py` - DOCX
- `icon_normalizer.py` - Normalización visual
- `icon_processor.py` - Procesamiento
- `icon_fallback_helper.py` - Fallbacks (⚠️ está en ui/widgets, debería estar aquí)
- `windows_icon_extractor.py` - Extracción Windows
- `windows_icon_converter.py` - Conversión HICON
- `pdf_renderer.py` - Renderizado PDFs
- `docx_converter.py` - Conversión DOCX
- `preview_scaling.py` - Escalado

#### File State (~6 archivos)
- `file_state_storage.py` - Persistencia SQLite principal
- `file_state_storage_crud.py` - CRUD básico
- `file_state_storage_batch.py` - Operaciones batch
- `file_state_storage_init.py` - Inicialización DB
- `file_state_storage_rename.py` - Renombrado
- `file_state_storage_helpers.py` - Helpers

#### Trash (~4 archivos)
- `trash_storage.py` - Almacenamiento papelera
- `trash_operations.py` - Operaciones (mover, restaurar)
- `trash_limits.py` - Límites (edad/tamaño)

#### Desktop (~3 archivos)
- `desktop_operations.py` - Operaciones escritorio
- `desktop_path_helper.py` - Detección rutas Desktop
- `desktop_drag_ops.py` - Drag & drop escritorio

#### System (~2 archivos)
- `filesystem_watcher_service.py` - Observador cambios FS
- `workspace_service.py` - Servicio workspace

### MANAGERS (7 archivos)
**Responsabilidad:** Coordinación de alto nivel

- `tab_manager.py` - Gestor de tabs (Focus) - ~250 líneas
  - Usa: `tab_manager_actions.py`, `tab_manager_signals.py`, `tab_manager_init.py`, `tab_manager_restore.py`, `tab_manager_state.py`
- `focus_manager.py` - Orquestador de Focus (wrapper ligero)
- `files_manager.py` - Coordinador de operaciones de archivos
- `file_state_manager.py` - Gestor de estados con caché

### UI/WIDGETS (73 archivos)

#### Windows (15 archivos)
- `main_window.py` - Ventana principal
- `desktop_window.py` - Ventana escritorio
- `quick_preview_window.py` - Preview rápido
- `bulk_rename_dialog.py` - Diálogo renombrado masivo
- `trash_delete_dialog.py` - Diálogo eliminación
- Setup/helpers: `main_window_setup.py`, `main_window_signals.py`, `main_window_state.py`, `main_window_file_handler.py`

#### Widgets Principales
- `file_grid_view.py` - Vista cuadrícula
- `file_list_view.py` - Vista lista
- `file_view_container.py` - Contenedor de vistas
- `focus_dock_widget.py` - Dock lateral (Focus)
- `folder_tree_sidebar.py` - Árbol de carpetas

#### FileTile (9 archivos - fragmentado pero legítimo)
- `file_tile.py` - Widget principal
- `file_tile_setup.py` - Configuración UI
- `file_tile_events.py` - Eventos mouse/drag
- `file_tile_paint.py` - Pintado personalizado
- `file_tile_icon.py` - Gestión iconos
- `file_tile_drag.py` - Drag & drop
- `file_tile_anim.py` - Animaciones
- `file_tile_states.py` - Estados visuales
- `file_tile_controller.py` - Control de selección

#### FocusStackTile (5 archivos)
- `focus_stack_tile.py` - Widget principal
- `focus_stack_tile_setup.py` - Setup
- `focus_stack_tile_events.py` - Eventos
- `focus_stack_tile_paint.py` - Pintado
- `focus_stack_tile_drag.py` - Drag

#### Grid Layout (6 archivos)
- `grid_layout_engine.py` - Motor de layout
- `grid_layout_config.py` - Configuración
- `grid_tile_builder.py` - Construcción tiles
- `grid_tile_positions.py` - Posicionamiento
- `grid_tile_animations.py` - Animaciones
- `grid_selection_logic.py` - Lógica selección
- `grid_selection_manager.py` - Gestor selección

#### Drag & Drop (6 archivos)
- `drag_common.py` - Utilidades comunes
- `drag_preview_helper.py` - Preview drag
- `tile_drag_handler.py` - Handler tiles
- `container_drag_handler.py` - Handler contenedor
- `file_drop_handler.py` - Handler drops
- `list_drag_handler.py` - Handler lista

#### Otros Widgets
- `file_stack_tile.py` - Tile para stacks
- `desktop_stack_tile.py` - Tile escritorio
- `state_badge_widget.py` - Badge de estado
- `badge_overlay_widget.py` - Overlay badges
- `subfolder_overlay.py` - Overlay subcarpetas
- `view_toolbar.py` - Barra herramientas
- `window_header.py` - Encabezado ventana

---

## 🔄 FLUJOS PRINCIPALES

### 1. Inicio de Aplicación
```
main.py
  └── QApplication
      └── DesktopWindow (auto-start)
          └── MainWindow (on demand)
              ├── TabManager
              ├── FocusManager
              └── UI Components
```

### 2. Gestión de Tabs (Focus)
```
Usuario hace clic en Focus
  └── FocusDockWidget
      └── TabManager.add_tab(path)
          ├── TabStateManager (persistencia)
          ├── TabHistoryManager (historial)
          └── FileSystemWatcherService (monitoreo)
              └── FileGridView.update_files()
```

### 3. Renderizado de Iconos
```
FileTile necesita icono
  └── IconService.get_file_preview()
      ├── PreviewService.get_file_preview() (PDFs, imágenes)
      ├── WindowsIconExtractor (iconos Windows)
      └── IconRendererSVG (fallback)
          └── QLabel.setPixmap()
```

### 4. Operaciones de Archivos
```
Usuario ejecuta acción (mover, renombrar, eliminar)
  └── FilesManager
      └── Service específico (file_move_service, etc.)
          ├── FileSystemWatcherService (notifica cambios)
          └── FileStateManager (actualiza estados)
              └── UI actualiza visualización
```

---

## 🔗 DEPENDENCIAS CRÍTICAS

### TabManager
- Depende de: `TabStateManager`, `TabHistoryManager`, `TabNavigationHandler`, `FileSystemWatcherService`
- Usado por: `MainWindow`, `FocusDockWidget`, `FileGridView`

### IconService
- Depende de: `PreviewService`, `IconRenderer*`, `WindowsIconExtractor`
- Usado por: Todos los widgets que muestran iconos

### FileStateManager
- Depende de: `FileStateStorage` (SQLite)
- Usado por: `FileGridView`, `FileListView` (badges de estado)

---

## 📍 PUNTOS DE ENTRADA

### Para Modificar Funcionalidad

1. **Gestión de Tabs:**
   - `app/managers/tab_manager.py` (API principal)
   - `app/services/tab_*.py` (implementación)

2. **Operaciones de Archivos:**
   - `app/managers/files_manager.py` (orquestación)
   - `app/services/file_*.py` (implementación)

3. **Renderizado de Iconos:**
   - `app/services/icon_service.py` (API principal)
   - `app/services/icon_renderer_*.py` (implementaciones)

4. **UI Principal:**
   - `app/ui/windows/main_window.py` (ventana principal)
   - `app/ui/widgets/file_grid_view.py` (vista cuadrícula)
   - `app/ui/widgets/focus_dock_widget.py` (sidebar)

---

## ⚠️ PROBLEMAS CONOCIDOS

### Violaciones de Arquitectura
1. `app/managers/files_manager.py` importa desde `ui/windows/`
   - **Solución:** Mover `open_file_with_system()` a `services/file_open_service.py`

2. `app/services/icon_service.py` importa `icon_fallback_helper` desde `ui/widgets/`
   - **Solución:** Mover `icon_fallback_helper.py` a `services/`

### Archivos Grandes
1. `app/managers/tab_manager.py` - ~250 líneas
2. `app/services/icon_service.py` - ~260 líneas

### Consolidación Pendiente
1. Helpers de tabs: `tab_utils.py`, `tab_path_normalizer.py`, `tab_finder.py`
2. Algunos helpers de iconos muy pequeños

---

## 🎯 REGLAS DE MODIFICACIÓN

### Al Modificar Código
1. **Respetar capas:** No importar UI desde services/managers
2. **Mantener tamaño:** Archivos <200 líneas, métodos <40 líneas
3. **Una responsabilidad:** Cada archivo/clase hace una cosa
4. **Nombres claros:** El nombre explica el propósito

### Al Agregar Funcionalidad
1. **Identificar capa:** ¿Es modelo, servicio, manager o UI?
2. **Revisar existente:** ¿Ya existe algo similar?
3. **Inyectar dependencias:** No crear dentro de `__init__`
4. **Documentar brevemente:** 1-2 líneas explicando qué hace

---

## 📚 ARCHIVOS DE REFERENCIA

- `ANALISIS_PROYECTO.md` - Análisis detallado completo
- `INFORMES/INFORME_DE_ESTADO.md` - Estado histórico del proyecto
- `README.md` - Documentación usuario

---

**Última actualización:** 29 de noviembre de 2025

