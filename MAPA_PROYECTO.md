# MAPA ARQUITECTÓNICO EXHAUSTIVO - ClarityDesk Pro

**Fecha:** 2025-12-29 (Actualizado despues de escaneo estructural)
**Objetivo:** Mapa completo del proyecto  
**Ultima actualizacion:** Escaneo estructural y recuento de modulos

---

## 📋 ÍNDICE

1. [Árbol Completo de Estructura](#árbol-completo)
2. [Análisis por Capas](#análisis-por-capas)
3. [Análisis Detallado de Archivos](#análisis-detallado)
4. [Problemas Arquitectónicos Detectados](#problemas-arquitectónicos)
5. [Evaluación de Diseño](#evaluación-de-diseño)

---

## 🌳 ÁRBOL COMPLETO DE ESTRUCTURA

```
ClarityDesk_29-11-25/
│
├── main.py                          # Punto de entrada principal
├── main.spec                        # Especificación PyInstaller
├── requirements.txt                 # Dependencias Python
├── README.md                        # Documentación del proyecto
├── arbol.txt                        # ⚠️ DUPLICADO - Documentación antigua
│
├── .trae/
│   └── rules/
│       └── project_rules.md         # Reglas de arquitectura (v2.1)
│
├── INFORMES/                        # 📁 Documentación y auditorías (40+ archivos)
│   ├── ANALISIS_CODIGO_MUERTO.md
│   ├── ANALISIS_PROYECTO.md
│   ├── AUDITORIA_*.md               # Múltiples auditorías
│   ├── FASE*.md                     # Informes de fases
│   └── Reglas Principales/
│
├── app/                             # 📁 Paquete principal
│   │
│   ├── __init__.py
│   │
│   ├── assets/                      # 📁 Recursos locales de app
│   │   └── icons/
│   │       ├── README.md
│   │       └── folder_sidebar.svg
│   │
│   ├── core/                        # 📁 Core - Configuración y utilidades base
│   │   ├── __init__.py
│   │   ├── constants.py             # Constantes globales (timers, debounce, límites)
│   │   └── logger.py                # Configuración centralizada de logging
│   │   └── top_level_detector.py    # Deteccion de ventanas top-level
│   │
│   ├── data/                        # 📁 Datos de configuración
│   │   └── rename_templates.json    # Plantillas de renombrado masivo
│   │
│   ├── models/                      # 📁 Models - Datos puros (5 archivos)
│   │   ├── __init__.py
│   │   ├── file_operation_result.py # Resultado de operaciones (success/error)
│   │   ├── file_stack.py            # Agrupación de archivos por tipo
│   │   ├── file_box_session.py      # Sesión de FileBox (temporal)
│   │   └── workspace.py             # Modelo de workspace (tabs, sidebar state)
│   │
│   ├── services/                    # 📁 Services - Lógica de negocio (71 archivos)
│   │   ├── __init__.py
│   │   │
│   │   ├── Tab Management (9 archivos)
│   │   │   ├── tab_state_manager.py        # Gestión de estado de tabs
│   │   │   ├── tab_storage_service.py      # Persistencia JSON de tabs
│   │   │   ├── tab_history_manager.py      # Historial de navegación back/forward
│   │   │   ├── tab_helpers.py              # Utilidades (normalización, búsqueda, validación)
│   │   │   └── tab_manager_init.py         # ⚠️ DUPLICADO - Inicialización (existe en managers/)
│   │   │
│   │   ├── File Operations (10 archivos)
│   │   │   ├── file_list_service.py        # Listado de archivos con filtrado
│   │   │   ├── file_scan_service.py         # Escaneo de carpetas
│   │   │   ├── file_filter_service.py      # Filtrado por extensiones
│   │   │   ├── file_stack_service.py       # Agrupación de archivos por tipo
│   │   │   ├── file_move_service.py        # Movimiento de archivos
│   │   │   ├── file_delete_service.py      # Eliminación con lógica contextual (Desktop/Trash/Normal)
│   │   │   ├── file_deletion_service.py    # ✅ Utilidad: is_folder_empty() (función redundante eliminada)
│   │   │   ├── file_rename_service.py      # Renombrado de archivos
│   │   │   ├── file_open_service.py        # Apertura con sistema
│   │   │   ├── file_path_utils.py          # Utilidades de rutas
│   │   │   └── file_extensions.py          # Extensiones soportadas
│   │   │
│   │   ├── File Creation (3 archivos)
│   │   │   ├── file_creation_service.py    # Creación de archivos (text, markdown, docx)
│   │   │   └── folder_creation_service.py  # Creación de carpetas
│   │   │
│   │   ├── Icons & Preview (25 archivos)
│   │   │   ├── icon_service.py             # Servicio principal de iconos Windows (373 líneas)
│   │   │   ├── icon_render_service.py      # Renderizado con normalización
│   │   │   ├── preview_service.py          # ✅ Utilidades de preview (get_file_preview, get_windows_shell_icon)
│   │   │   ├── preview_pdf_service.py      # Servicio de previews PDF/DOCX (357 líneas) - Servicio principal
│   │   │   ├── icon_renderer.py            # Renderizador base
│   │   │   ├── icon_renderer_pdf.py        # Renderizado PDFs
│   │   │   ├── icon_renderer_image.py      # Renderizado imágenes
│   │   │   ├── icon_renderer_svg.py        # Renderizado SVGs
│   │   │   ├── icon_renderer_docx.py       # Renderizado DOCX
│   │   │   ├── icon_renderer_constants.py  # Constantes de renderizado
│   │   │   ├── icon_batch_worker.py        # Worker para generación batch de iconos
│   │   │   ├── pdf_render_worker.py        # Worker para renderizado PDF
│   │   │   ├── pdf_thumbnails_worker.py    # Worker para thumbnails PDF
│   │   │   ├── docx_convert_worker.py      # Worker para conversión DOCX
│   │   │   ├── icon_normalizer.py          # Normalización visual
│   │   │   ├── icon_processor.py           # Procesamiento de iconos
│   │   │   ├── icon_path_utils.py          # Utilidades de rutas de iconos
│   │   │   ├── icon_fallback_helper.py     # Fallbacks de iconos
│   │   │   ├── icon_conversion_helper.py   # Conversión de iconos
│   │   │   ├── icon_extraction_fallbacks.py # Fallbacks de extracción
│   │   │   ├── preview_scaling.py          # Escalado de previews
│   │   │   ├── pixel_analyzer.py           # Análisis de píxeles
│   │   │   ├── windows_icon_extractor.py   # Extracción de iconos Windows
│   │   │   ├── windows_icon_converter.py   # Conversión HICON
│   │   │   ├── windows_recycle_bin_utils.py # Utilidades Recycle Bin Windows
│   │   │   ├── pdf_renderer.py             # Renderizado PDFs
│   │   │   └── docx_converter.py           # Conversión DOCX
│   │   │
│   │   ├── File State Storage (7 archivos)
│   │   │   ├── file_state_storage.py       # Módulo principal (re-exporta APIs)
│   │   │   ├── file_state_storage_helpers.py # Helpers (DB path, conexión, file ID)
│   │   │   ├── file_state_storage_init.py  # Inicialización y schema SQLite
│   │   │   ├── file_state_storage_crud.py # Operaciones CRUD individuales
│   │   │   ├── file_state_storage_batch.py # Operaciones batch
│   │   │   ├── file_state_storage_query.py # Consultas y lectura
│   │   │   └── file_state_storage_rename.py # Operaciones de renombrado
│   │   │
│   │   ├── Trash (3 archivos)
│   │   │   ├── trash_storage.py            # Almacenamiento de papelera
│   │   │   ├── trash_operations.py         # Operaciones (mover, restaurar, eliminar)
│   │   │   └── trash_limits.py             # Límites (edad/tamaño)
│   │   │
│   │   ├── Desktop (5 archivos)
│   │   │   ├── desktop_operations.py       # Operaciones de escritorio
│   │   │   ├── desktop_operations_scan.py # Escaneo de escritorio
│   │   │   ├── desktop_path_helper.py     # Detección de rutas Desktop
│   │   │   ├── desktop_drag_ops.py        # Operaciones drag & drop escritorio
│   │   │   └── desktop_visibility.py      # Visibilidad de escritorio
│   │   │
│   │   ├── FileBox (5 archivos)
│   │   │   ├── file_box_service.py         # Servicio principal FileBox
│   │   │   ├── file_box_history_service.py # Historial de FileBox
│   │   │   ├── file_box_icon_helper.py    # Helpers de iconos
│   │   │   └── file_box_utils.py           # Utilidades FileBox
│   │   │
│   │   ├── File Category (1 archivo)
│   │   │   └── file_category_service.py   # Categorización de archivos
│   │   │
│   │   ├── Header Customization (1 archivo)
│   │   │   └── header_customization_service.py # Personalización de headers
│   │   │
│   │   ├── Rename (1 archivo)
│   │   │   └── rename_service.py           # Servicio de renombrado masivo
│   │   │
│   │   ├── System Services (6 archivos)
│   │   │   ├── filesystem_watcher_service.py # Observador de cambios del sistema de archivos
│   │   │   ├── workspace_service.py        # Servicio de workspace
│   │   │   ├── workspace_storage_service.py # Persistencia de workspaces
│   │   │   └── settings_service.py         # Gestión de configuración
│   │   │   └── state_label_storage.py       # Persistencia de etiquetas de estado
│   │   │   └── state_view_mode_storage.py   # Persistencia de modos de vista
│   │   │   └── search_service.py            # Busqueda y filtrado
│   │   │
│   │   └── Utils (2 archivos)
│   │       ├── path_utils.py               # Utilidades de rutas (normalización)
│   │       └── preview_file_extensions.py # Extensiones para preview
│   │
│   ├── managers/                    # 📁 Managers - Orquestación (15 archivos)
│   │   ├── __init__.py
│   │   ├── tab_manager.py                  # Gestor central de tabs (358 líneas)
│   │   ├── tab_manager_actions.py         # Acciones de tabs (254 líneas)
│   │   ├── tab_manager_init.py            # ⚠️ DUPLICADO - Inicialización (existe en services/)
│   │   ├── tab_manager_restore.py         # Restauración de estado
│   │   ├── tab_manager_signals.py         # Manejo de señales
│   │   ├── tab_manager_state.py           # Gestión de estado persistente
│   │   ├── app_settings.py                # Orquestacion de settings
│   │   ├── file_clipboard_manager.py      # Clipboard de archivos
│   │   ├── files_manager.py               # Orquestador de operaciones de archivos
│   │   ├── focus_manager.py               # Orquestador de Focus (wrapper ligero)
│   │   ├── file_state_manager.py           # Gestor de estados con caché SQLite
│   │   ├── search_manager.py              # Orquestador de busqueda
│   │   ├── state_label_manager.py         # Orquestador de etiquetas de estado
│   │   └── workspace_manager.py            # Gestor de workspaces
│   │
│   ├── storage/                     # 📁 Estado simple (JSON)
│   │   ├── dock_tabs.json
│   │   └── trash_tabs.json
│   │
│   ├── tests/                       # 📁 Tests de app
│   │   ├── test_sidebar_double_click_sequence.py
│   │   └── test_sidebar_double_click.py
│   │
│   └── ui/                          # 📁 UI - Interfaz de usuario (Qt)
│       ├── __init__.py
│       │
│       ├── utils/                   # 📁 Utilidades UI
│       │   ├── __init__.py
│       │   ├── file_box_ui_utils.py # Utilidades UI de FileBox
│       │   └── font_manager.py     # Gestión de fuentes
│       │   └── rounded_background_painter.py # Pintado de fondos redondeados
│       │
│       ├── widgets/                 # 📁 Componentes reutilizables (98 archivos)
│       │   ├── __init__.py
│       │   │
│       │   ├── FileGridView (9 archivos)
│       │   │   ├── file_grid_view.py           # Widget principal de vista cuadrícula
│       │   │   ├── grid_content_widget.py     # Widget de contenido del grid
│       │   │   ├── grid_layout_engine.py      # Motor de layout del grid
│       │   │   ├── grid_layout_config.py      # Configuración del layout
│       │   │   ├── file_grid_view_layout.py   # Setup de layout
│       │   │   ├── file_grid_view_events.py   # Manejo de eventos
│       │   │   ├── file_grid_view_drag.py     # Drag & drop
│       │   │   ├── file_grid_view_scroll.py   # Scroll area
│       │   │   └── grid_tile_builder.py        # Construcción de tiles
│       │   │
│       │   ├── FileTile (9 archivos)
│       │   │   ├── file_tile.py                # Widget principal de tile de archivo
│       │   │   ├── file_tile_setup.py         # Setup de UI
│       │   │   ├── file_tile_events.py        # Eventos mouse/drag
│       │   │   ├── file_tile_paint.py         # Pintado personalizado
│       │   │   ├── file_tile_icon.py          # Gestión de iconos
│       │   │   ├── file_tile_drag.py          # Drag & drop
│       │   │   ├── file_tile_anim.py          # Animaciones
│       │   │   ├── file_tile_states.py        # Estados visuales
│       │   │   ├── file_tile_controller.py    # Control de selección
│       │   │   └── file_tile_utils.py         # Utilidades de tiles
│       │   │
│       │   ├── FileListView (8 archivos)
│       │   │   ├── file_list_view.py          # Widget principal de vista lista
│       │   │   ├── file_list_renderer.py      # Renderizado de filas
│       │   │   ├── file_list_handlers.py      # Manejo de eventos
│       │   │   ├── list_row_factory.py        # Factory de filas
│       │   │   ├── list_icon_delegate.py      # Delegate de iconos
│       │   │   ├── list_state_cell.py         # Celda de estado
│       │   │   ├── list_checkbox.py           # Checkbox de lista
│       │   │   └── list_styles.py             # Estilos de lista
│       │   │
│       │   ├── FileViewContainer (6 archivos)
│       │   │   ├── file_view_container.py    # Contenedor principal (grid + list)
│       │   │   ├── file_view_setup.py         # Setup de UI
│       │   │   ├── file_view_sync.py          # Sincronización entre vistas
│       │   │   ├── file_view_tabs.py           # Manejo de tabs
│       │   │   ├── file_view_handlers.py      # Handlers de eventos
│       │   │   └── file_view_context_menu.py  # Menú contextual
│       │   │
│       │   ├── FileView Utils (2 archivos)
│       │   │   ├── file_view_utils.py         # Utilidades de FileView
│       │   │   └── file_state_migration.py   # Migración de estados
│       │   │
│       │   ├── FocusDockWidget (6 archivos)
│       │   │   ├── focus_header_panel.py     # Panel de encabezado
│       │   │   └── subfolder_overlay.py       # Overlay de subcarpetas
│       │   │   # ⚠️ NOTA: focus_dock_widget.py no encontrado en listado
│       │   │
│       │   ├── FocusStackTile (1 archivo)
│       │   │   └── file_stack_tile.py        # Tile para stacks
│       │   │
│       │   ├── FolderTreeSidebar (11 archivos)
│       │   │   ├── folder_tree_sidebar.py     # Widget principal del árbol
│       │   │   ├── folder_tree_model.py      # Modelo del árbol
│       │   │   ├── folder_tree_delegate.py   # Delegate del árbol (565 líneas)
│       │   │   ├── folder_tree_handlers.py   # Handlers de eventos
│       │   │   ├── folder_tree_drag_handler.py # Drag & drop
│       │   │   ├── folder_tree_styles.py     # Estilos del árbol
│       │   │   ├── folder_tree_animations.py # Animaciones
│       │   │   ├── folder_tree_icon_utils.py # Utilidades de iconos
│       │   │   ├── folder_tree_index_utils.py # Utilidades de índices
│       │   │   ├── folder_tree_menu_utils.py # Utilidades de menú
│       │   │   ├── folder_tree_reorder_handler.py # Reordenamiento
│       │   │   └── folder_tree_widget_utils.py # Utilidades de widget
│       │   │
│       │   ├── Grid Layout & Selection (6 archivos)
│       │   │   ├── grid_layout_engine.py     # Motor de layout (duplicado arriba)
│       │   │   ├── grid_layout_config.py     # Configuración (duplicado arriba)
│       │   │   ├── grid_selection_logic.py   # Lógica de selección
│       │   │   ├── grid_selection_manager.py # Gestor de selección
│       │   │   ├── grid_tile_positions.py    # Posicionamiento
│       │   │   └── grid_tile_animations.py   # Animaciones
│       │   │
│       │   ├── Drag & Drop (6 archivos)
│       │   │   ├── drag_common.py            # Utilidades comunes de drag
│       │   │   ├── drag_preview_helper.py    # Preview de drag
│       │   │   ├── tile_drag_handler.py      # Handler de drag de tiles
│       │   │   ├── container_drag_handler.py # Handler de drag de contenedor
│       │   │   ├── file_drop_handler.py      # Handler de drop de archivos
│       │   │   └── list_drag_handler.py     # Handler de drag de lista
│       │   │
│       │   ├── FileBox UI (3 archivos)
│       │   │   ├── file_box_panel.py         # Panel de FileBox
│       │   │   ├── file_box_history_panel.py # Panel de historial
│       │   │   └── file_box_history_panel_sidebar.py # Panel sidebar
│       │   │
│       │   ├── Otros Widgets (13 archivos)
│       │   │   ├── desktop_stack_tile.py     # Tile de escritorio
│       │   │   ├── settings_stack_tile.py   # Tile de configuración
│       │   │   ├── state_badge_widget.py     # Badge de estado
│       │   │   ├── badge_overlay_widget.py  # Overlay de badges
│       │   │   ├── view_toolbar.py          # Barra de herramientas
│       │   │   ├── window_header.py         # Encabezado de ventana
│       │   │   ├── app_header.py            # Encabezado de aplicación
│       │   │   ├── secondary_header.py      # Encabezado secundario
│       │   │   ├── category_section_header.py # Encabezado de categoría
│       │   │   ├── raycast_panel.py         # Panel raycast
│       │   │   ├── dock_separator.py         # Separador de dock
│       │   │   ├── text_elision.py          # Elisión de texto
│       │   │   ├── header_customization_palette.py # Paleta de personalización
│       │   │   ├── workspace_selector.py    # Selector de workspace
│       │   │   ├── list_table_style.py       # Estilos de tabla
│       │   │   └── list_viewport.py         # Viewport de lista
│       │   │
│       │   └── Toolbar (3 archivos)
│       │       ├── toolbar_button_styles.py  # Estilos de botones
│       │       ├── toolbar_navigation_buttons.py # Botones de navegación
│       │       └── toolbar_state_buttons.py # Botones de estado
│       │
│       └── windows/                 # 📁 Ventanas principales (28 archivos)
│           ├── __init__.py
│           │
│           ├── MainWindow (5 archivos)
│           │   ├── main_window.py           # Ventana principal de la aplicación
│           │   ├── main_window_setup.py     # Setup de UI
│           │   ├── main_window_signals.py   # Conexión de señales
│           │   ├── main_window_state.py     # Gestión de estado
│           │   └── main_window_file_handler.py # Manejo de archivos
│           │
│           ├── DesktopWindow (1 archivo)
│           │   └── desktop_window.py        # Ventana de escritorio (auto-start)
│           │
│           ├── QuickPreviewWindow (11 archivos)
│           │   ├── quick_preview_window.py  # Ventana principal de preview rápido
│           │   ├── quick_preview_ui_setup.py # Setup de UI
│           │   ├── quick_preview_loader.py  # Carga de previews
│           │   ├── quick_preview_cache.py  # Caché de previews
│           │   ├── quick_preview_pdf_handler.py # Manejo de PDFs
│           │   ├── quick_preview_thumbnails.py # Thumbnails de preview
│           │   ├── quick_preview_thumbnail_widget.py # Widget de thumbnail
│           │   ├── quick_preview_navigation.py # Navegación
│           │   ├── quick_preview_animations.py # Animaciones
│           │   ├── quick_preview_header.py  # Encabezado
│           │   ├── quick_preview_styles.py  # Estilos
│           │   └── quick_preview_constants.py # Constantes
│           │
│           └── Diálogos (2 archivos)
│               ├── bulk_rename_dialog.py   # Diálogo de renombrado masivo
│               └── trash_delete_dialog.py   # Diálogo de confirmación de eliminación
│
├── assets/                          # 📁 Recursos globales
│   ├── icons/                       # Iconos SVG genéricos
│   │   ├── README.md
│   │   ├── ajustes.svg
│   │   ├── archive.svg
│   │   ├── code.svg
│   │   ├── config.svg
│   │   ├── doc.svg
│   │   ├── escritorio.svg
│   │   ├── exe.svg
│   │   ├── folder icon.svg
│   │   ├── folder_sidebar.svg
│   │   ├── generic.svg
│   │   ├── media.svg
│   │   ├── sheet.svg
│   │   ├── slide.svg
│   │   └── text.svg
│   │
│   └── poppler/                     # Binarios Poppler (PDF rendering)
│       └── bin/
│           [archivos DLL y ejecutables de Poppler]
│
├── build/                           # 📁 Build de PyInstaller
│   └── main/
│       [archivos de build]
│
├── dist/                            # 📁 Distribución
│   └── main/
│       └── main.exe
│
├── scripts/                         # 📁 Automatización
│   └── build_release.bat            # Script de build para release
│
├── storage/                         # 📁 Datos persistentes
│   ├── claritydesk.db               # Base de datos SQLite (estados de archivos)
│   ├── tabs.json                    # Estado de tabs (JSON)
│   ├── header_config.json           # Configuración de headers
│   ├── settings.json                # Configuración de la aplicación
│   ├── workspaces.json              # Lista de workspaces
│   ├── workspace_*.json              # Estados de workspaces individuales
│   ├── dock_files/                  # Archivos del dock
│   └── trash/                       # Papelera
│       ├── files/                   # Archivos eliminados
│       └── metadata.json            # Metadata de papelera
│
└── tests/                           # 📁 Pruebas unitarias
    ├── __init__.py
    ├── test_files_controller.py
    ├── test_focus_controller.py
    ├── test_tabs_controller.py
    └── test_workspace_switching.py```

---

## 🔍 ANÁLISIS POR CAPAS

### 📁 `app/core/` - Core (Infraestructura Base)

**Responsabilidad:** Configuración global y utilidades base del sistema.

**Tipo de capa:** Infraestructura (Core)

**Archivos:**
- `constants.py` - ✅ **NECESARIO** - Centraliza valores mágicos (timers, debounce, límites). Bien diseñado.
- `logger.py` - ✅ **NECESARIO** - Configuración centralizada de logging. Buen diseño.
- `top_level_detector.py` - ? **NECESARIO** - Deteccion de ventanas top-level.

**Evaluación:** ✅ **BUEN DISEÑO** - Capa limpia, sin dependencias circulares.

---

### 📁 `app/models/` - Models (Datos Puros)

**Responsabilidad:** Estructuras de datos puras sin lógica de negocio.

**Tipo de capa:** Model (Datos)

**Archivos:**
- `file_operation_result.py` - ✅ **NECESARIO** - Resultado estructurado de operaciones. Bien diseñado.
- `file_stack.py` - ✅ **NECESARIO** - Modelo de agrupación de archivos. Incluye lógica de display (método `get_display_name()`), pero aceptable.
- `file_box_session.py` - ⚠️ **DUDOSO** - Modelo de sesión temporal. Solo usado en FileBox. Podría ser parte de `file_box_service.py`.
- `workspace.py` - ✅ **NECESARIO** - Modelo de workspace. Bien diseñado.

**Evaluación:** ✅ **BUEN DISEÑO** - Capa limpia, sin dependencias externas. Solo `file_box_session.py` es dudoso.

---

### 📁 `app/services/` - Services (Lógica de Negocio)

**Responsabilidad:** Operaciones de negocio y lógica de dominio.

**Tipo de capa:** Service (Lógica de Negocio)

**Total:** 77 archivos organizados en dominios.

#### Tab Management (9 archivos)
- `tab_state_manager.py` - ✅ **NECESARIO** - Gestión de estado de tabs.
- `tab_storage_service.py` - ✅ **NECESARIO** - Persistencia JSON.
- `tab_history_manager.py` - ✅ **NECESARIO** - Historial de navegación.
- `tab_helpers.py` - ✅ **NECESARIO** - Utilidades consolidadas.
- `tab_manager_init.py` - ⚠️ **DUPLICADO** - Existe también en `managers/tab_manager_init.py`. Confusión de nombres.

#### File Operations (10 archivos)
- `file_list_service.py` - ✅ **NECESARIO** - Orquesta listado, filtrado y stacking.
- `file_scan_service.py` - ✅ **NECESARIO** - Escaneo de carpetas.
- `file_filter_service.py` - ✅ **NECESARIO** - Filtrado por extensiones.
- `file_stack_service.py` - ✅ **NECESARIO** - Agrupación por tipo.
- `file_move_service.py` - ✅ **NECESARIO** - Movimiento de archivos.
- `file_delete_service.py` - ✅ **NECESARIO** - Eliminación con lógica contextual (Desktop/Trash/Normal). **Servicio fuente de verdad para borrados.**
- `file_deletion_service.py` - ✅ **NECESARIO** - Solo contiene `is_folder_empty()`. Función redundante `move_to_windows_recycle_bin()` eliminada.
- `file_rename_service.py` - ✅ **NECESARIO** - Renombrado individual.
- `file_open_service.py` - ✅ **NECESARIO** - Apertura con sistema.
- `file_path_utils.py` - ✅ **NECESARIO** - Validación de rutas.
- `file_extensions.py` - ✅ **NECESARIO** - Constantes de extensiones.

#### File Creation (3 archivos)
- `file_creation_service.py` - ✅ **NECESARIO** - Creación de archivos (text, markdown, docx).
- `folder_creation_service.py` - ✅ **NECESARIO** - Creación de carpetas.

#### Icons & Preview (25 archivos)
- `icon_service.py` - ✅ **NECESARIO** - Servicio principal (373 líneas). Bien estructurado.
- `icon_render_service.py` - ✅ **NECESARIO** - Renderizado con normalización.
- `preview_service.py` - ✅ **NECESARIO** - Utilidades de preview (`get_file_preview`, `get_windows_shell_icon`). Alias eliminado.
- `preview_pdf_service.py` - ✅ **NECESARIO** - Servicio principal de previews PDF/DOCX (357 líneas). **Usado directamente en UI.**
- `icon_renderer.py` - ✅ **NECESARIO** - Renderizador base.
- `icon_renderer_pdf.py` - ✅ **NECESARIO** - Renderizado PDFs.
- `icon_renderer_image.py` - ✅ **NECESARIO** - Renderizado imágenes.
- `icon_renderer_svg.py` - ✅ **NECESARIO** - Renderizado SVGs.
- `icon_renderer_docx.py` - ✅ **NECESARIO** - Renderizado DOCX.
- `icon_renderer_constants.py` - ✅ **NECESARIO** - Constantes.
- `icon_batch_worker.py` - ✅ **NECESARIO** - Worker batch.
- `pdf_render_worker.py` - ✅ **NECESARIO** - Worker PDF.
- `pdf_thumbnails_worker.py` - ✅ **NECESARIO** - Worker thumbnails.
- `docx_convert_worker.py` - ✅ **NECESARIO** - Worker DOCX.
- `icon_normalizer.py` - ✅ **NECESARIO** - Normalización visual.
- `icon_processor.py` - ✅ **NECESARIO** - Procesamiento.
- `icon_path_utils.py` - ? **NECESARIO** - Utilidades de rutas para iconos.
- `icon_fallback_helper.py` - ✅ **NECESARIO** - Fallbacks.
- `icon_conversion_helper.py` - ✅ **NECESARIO** - Conversión.
- `icon_extraction_fallbacks.py` - ✅ **NECESARIO** - Fallbacks de extracción.
- `preview_scaling.py` - ✅ **NECESARIO** - Escalado.
- `pixel_analyzer.py` - ✅ **NECESARIO** - Análisis de píxeles.
- `windows_icon_extractor.py` - ✅ **NECESARIO** - Extracción Windows.
- `windows_icon_converter.py` - ✅ **NECESARIO** - Conversión HICON.
- `windows_recycle_bin_utils.py` - ? **NECESARIO** - Utilidades de Recycle Bin.
- `pdf_renderer.py` - ✅ **NECESARIO** - Renderizado PDFs.
- `docx_converter.py` - ✅ **NECESARIO** - Conversión DOCX.

**Evaluación Icons & Preview:** ✅ **BUEN DISEÑO** - Bien separado por responsabilidades. Alias confuso eliminado.

#### File State Storage (7 archivos)
- `file_state_storage.py` - ✅ **NECESARIO** - Módulo principal (re-exporta APIs).
- `file_state_storage_helpers.py` - ✅ **NECESARIO** - Helpers (DB path, conexión).
- `file_state_storage_init.py` - ✅ **NECESARIO** - Inicialización y schema.
- `file_state_storage_crud.py` - ✅ **NECESARIO** - CRUD individual.
- `file_state_storage_batch.py` - ✅ **NECESARIO** - Operaciones batch.
- `file_state_storage_query.py` - ? **NECESARIO** - Consultas y lectura.
- `file_state_storage_rename.py` - ✅ **NECESARIO** - Renombrado.

**Evaluación File State:** ✅ **BUEN DISEÑO** - Separación clara por operaciones.

#### Trash (3 archivos)
- `trash_storage.py` - ✅ **NECESARIO** - Almacenamiento.
- `trash_operations.py` - ✅ **NECESARIO** - Operaciones.
- `trash_limits.py` - ✅ **NECESARIO** - Límites.

#### Desktop (5 archivos)
- `desktop_operations.py` - ✅ **NECESARIO** - Operaciones.
- `desktop_operations_scan.py` - ✅ **NECESARIO** - Escaneo.
- `desktop_path_helper.py` - ✅ **NECESARIO** - Detección de rutas.
- `desktop_drag_ops.py` - ✅ **NECESARIO** - Drag & drop.
- `desktop_visibility.py` - ✅ **NECESARIO** - Visibilidad.

#### FileBox (5 archivos)
- `file_box_service.py` - ✅ **NECESARIO** - Servicio principal.
- `file_box_history_service.py` - ✅ **NECESARIO** - Historial.
- `file_box_icon_helper.py` - ✅ **NECESARIO** - Helpers de iconos.
- `file_box_utils.py` - ✅ **NECESARIO** - Utilidades.

#### Otros Services (7 archivos)
- `file_category_service.py` - ✅ **NECESARIO** - Categorización.
- `header_customization_service.py` - ✅ **NECESARIO** - Personalización.
- `rename_service.py` - ✅ **NECESARIO** - Renombrado masivo.
- `filesystem_watcher_service.py` - ✅ **NECESARIO** - Observador de cambios.
- `workspace_service.py` - ✅ **NECESARIO** - Servicio de workspace.
- `workspace_storage_service.py` - ✅ **NECESARIO** - Persistencia.
- `settings_service.py` - ✅ **NECESARIO** - Configuración.
- `state_label_storage.py` - ? **NECESARIO** - Persistencia de etiquetas de estado.
- `state_view_mode_storage.py` - ? **NECESARIO** - Persistencia de modos de vista.
- `search_service.py` - ? **NECESARIO** - Busqueda y filtrado.
- `path_utils.py` - ✅ **NECESARIO** - Utilidades de rutas.
- `preview_file_extensions.py` - ✅ **NECESARIO** - Constantes de extensiones.

**Evaluación Services:** ✅ **BUEN DISEÑO GENERAL** - Bien organizado por dominios. Problemas menores:
- ⚠️ `tab_manager_init.py` - Duplicado con `managers/tab_manager_init.py` (responsabilidades distintas, mal nombrado).

---

### 📁 `app/managers/` - Managers (Orquestación)

**Responsabilidad:** Coordinación de alto nivel entre servicios.

**Tipo de capa:** Manager (Orquestación)

**Total:** 15 archivos.

**Archivos:**
- `tab_manager.py` - ✅ **NECESARIO** - Gestor central (358 líneas). Bien estructurado, usa módulos auxiliares.
- `tab_manager_actions.py` - ✅ **NECESARIO** - Acciones de tabs (254 líneas). Extracción correcta.
- `tab_manager_init.py` - ⚠️ **DUPLICADO** - Existe también en `services/tab_manager_init.py`. Confusión de nombres.
- `tab_manager_restore.py` - ✅ **NECESARIO** - Restauración de estado.
- `tab_manager_signals.py` - ✅ **NECESARIO** - Manejo de señales.
- `tab_manager_state.py` - ✅ **NECESARIO** - Gestión de estado persistente.
- `app_settings.py` - ? **NECESARIO** - Orquesta settings de app.
- `file_clipboard_manager.py` - ? **NECESARIO** - Clipboard de archivos.
- `files_manager.py` - ✅ **NECESARIO** - Orquestador de operaciones de archivos. Wrapper ligero pero necesario.
- `focus_manager.py` - ⚠️ **WRAPPER LIGERO** - Solo delega a `TabManager`. Podría eliminarse si no agrega valor.
- `file_state_manager.py` - ✅ **NECESARIO** - Gestor de estados con caché.
- `search_manager.py` - ? **NECESARIO** - Orquesta busqueda.
- `state_label_manager.py` - ? **NECESARIO** - Orquesta etiquetas de estado.
- `workspace_manager.py` - ✅ **NECESARIO** - Gestor de workspaces.

**Evaluación:** ✅ **BUEN DISEÑO** - Separación clara. Problemas:
- ⚠️ `tab_manager_init.py` - Duplicado con `services/tab_manager_init.py`.
- ⚠️ `focus_manager.py` - Wrapper muy ligero, posible eliminación.

---

### 📁 `app/ui/` - UI (Interfaz de Usuario)

**Responsabilidad:** Componentes visuales y presentación.

**Tipo de capa:** UI (Presentación)

#### `app/ui/utils/` (3 archivos)
- `file_box_ui_utils.py` - ✅ **NECESARIO** - Utilidades UI de FileBox.
- `font_manager.py` - ✅ **NECESARIO** - Gestión de fuentes.
- `rounded_background_painter.py` - ? **NECESARIO** - Pintado de fondos redondeados.

#### `app/ui/widgets/` (83 archivos)

**FileGridView (9 archivos)** - ✅ **BUEN DISEÑO** - Separación clara por responsabilidades.

**FileTile (10 archivos)** - ✅ **BUEN DISEÑO** - Separación clara. `file_tile_utils.py` podría consolidarse.

**FileListView (8 archivos)** - ✅ **BUEN DISEÑO** - Separación clara.

**FileViewContainer (6 archivos)** - ✅ **BUEN DISEÑO** - Separación clara.

**FolderTreeSidebar (11 archivos)** - ⚠️ **FRAGMENTADO** - Muchos archivos de utilidades. Podría consolidarse parcialmente.

**Grid Layout & Selection (6 archivos)** - ⚠️ **DUPLICADOS** - `grid_layout_engine.py` y `grid_layout_config.py` aparecen también en FileGridView.

**Drag & Drop (6 archivos)** - ✅ **BUEN DISEÑO** - Separación clara por contexto.

**Otros Widgets (13 archivos)** - ✅ **NECESARIO** - Componentes diversos bien organizados.

**Evaluación Widgets:** ✅ **BUEN DISEÑO GENERAL** - Separación clara. Problemas menores:
- ⚠️ Duplicación de `grid_layout_engine.py` y `grid_layout_config.py`.
- ⚠️ FolderTreeSidebar muy fragmentado (11 archivos).

#### `app/ui/windows/` (28 archivos)

**MainWindow (5 archivos)** - ✅ **BUEN DISEÑO** - Separación clara por responsabilidades.

**QuickPreviewWindow (11 archivos)** - ✅ **BUEN DISEÑO** - Separación clara.

**Diálogos (2 archivos)** - ✅ **NECESARIO** - Diálogos bien separados.

**Evaluación Windows:** ✅ **BUEN DISEÑO** - Separación clara.

---

## 🚨 PROBLEMAS ARQUITECTÓNICOS DETECTADOS

### 1. **DUPLICACIÓN DE ARCHIVOS**

#### ⚠️ `tab_manager_init.py` (DUPLICADO)
- **Ubicaciones:** 
  - `app/services/tab_manager_init.py`
  - `app/managers/tab_manager_init.py`
- **Problema:** Mismo nombre, diferentes responsabilidades. Confusión de nombres.
- **Solución:** Renombrar uno de ellos o consolidar.

#### ✅ `file_deletion_service.py` vs `file_delete_service.py` (RESUELTO)
- **Estado:** Función redundante `move_to_windows_recycle_bin()` eliminada de `file_deletion_service.py`.
- **Actual:** `file_deletion_service.py` solo contiene `is_folder_empty()` (utilidad necesaria).
- **Actual:** `file_delete_service.py` es el servicio fuente de verdad para borrados (lógica contextual).
- **Cambio:** `file_view_context_menu.py` ahora usa `delete_file()` con lógica contextual.

#### ✅ `preview_service.py` (ALIAS ELIMINADO)
- **Estado:** Alias `PreviewService = PreviewPdfService` eliminado.
- **Actual:** `preview_service.py` contiene solo utilidades (`get_file_preview`, `get_windows_shell_icon`).
- **Actual:** UI usa directamente `PreviewPdfService` (4 archivos actualizados).

#### ⚠️ `grid_layout_engine.py` y `grid_layout_config.py` (DUPLICADOS)
- **Problema:** Aparecen en múltiples lugares del árbol.
- **Solución:** Verificar si son realmente duplicados o solo referencias.

### 2. **WRAPPERS SIN LÓGICA**

#### ⚠️ `focus_manager.py`
- **Problema:** Wrapper muy ligero que solo delega a `TabManager`.
- **Evaluación:** Si no agrega valor (señales, validación, etc.), podría eliminarse.
- **Solución:** Verificar si las señales `focus_opened` y `focus_removed` son necesarias.

### 3. **FRAGMENTACIÓN EXCESIVA**

#### ⚠️ `FolderTreeSidebar` (11 archivos)
- **Problema:** Muchos archivos de utilidades (`folder_tree_icon_utils.py`, `folder_tree_index_utils.py`, `folder_tree_menu_utils.py`, `folder_tree_widget_utils.py`).
- **Evaluación:** Podría consolidarse parcialmente sin violar regla de 800 líneas.
- **Solución:** Consolidar utilidades relacionadas.

### 4. **CÓDIGO INFLADO POR IA**

#### ⚠️ Separación excesiva en algunos widgets
- **Problema:** Algunos widgets tienen muchos archivos auxiliares que podrían consolidarse.
- **Ejemplos:** FileTile (10 archivos), FileGridView (9 archivos).
- **Evaluación:** Aunque sigue reglas de arquitectura, podría optimizarse.
- **Solución:** Consolidar archivos relacionados si no superan 800 líneas.

### 5. **ARCHIVOS DUDOSOS**

#### ⚠️ `file_box_session.py` (Model)
- **Problema:** Solo usado en FileBox. Podría ser parte de `file_box_service.py`.
- **Solución:** Evaluar si debe ser modelo o parte del servicio.

#### `file_list_view.py.backup`
- **Problema:** Backup dentro de `app/ui/widgets/` mezclado con codigo activo.
- **Solucion:** Mover a `backups/` o eliminar si ya no se usa.

#### ⚠️ `arbol.txt`
- **Problema:** Documentación antigua duplicada. Este mapa lo sustituye.
- **Solución:** Eliminar o mover a INFORMES/.

---

## ✅ EVALUACIÓN DE DISEÑO

### **BUEN DISEÑO QUE NO DEBE TOCARSE**

1. **Separación de capas** - ✅ Estricta: models → services → managers → ui
2. **TabManager modular** - ✅ Bien estructurado con módulos auxiliares
3. **File State Storage** - ✅ Separación clara por operaciones (CRUD, batch, rename)
4. **Icons & Preview** - ✅ Bien separado por tipo de renderizado
5. **Widgets principales** - ✅ Separación clara por responsabilidades (setup, events, paint, etc.)
6. **Core** - ✅ Limpio, sin dependencias circulares

### **COMPLEJIDAD INNECESARIA**

1. **Fragmentación excesiva** - Algunos widgets tienen demasiados archivos auxiliares
2. **Duplicación de nombres** - `tab_manager_init.py` en dos lugares (responsabilidades distintas)
3. ~~**Alias confusos**~~ - ✅ **RESUELTO** - Alias `PreviewService` eliminado

### **CÓDIGO CLARAMENTE INFLADO POR IA**

1. **Separación excesiva** - Algunos widgets podrían consolidar archivos relacionados
2. **Archivos de utilidades múltiples** - FolderTreeSidebar tiene 4 archivos `*_utils.py`
3. **Wrappers innecesarios** - `focus_manager.py` es muy ligero

---

## 📊 ESTADÍSTICAS FINALES

- **Total archivos Python (repo, excluye backups/build/dist):** 339 archivos
- **Models:** 5 archivos
- **Services:** 77 archivos (incluye query/state/search a?adidos)
- **Managers:** 15 archivos
- **UI Widgets:** 98 archivos
- **UI Windows:** 28 archivos
- **Core:** 4 archivos

### **Problemas Detectados:**
- ⚠️ Duplicados: 1 archivo (`tab_manager_init.py` en services/ y managers/ - responsabilidades distintas)
- ✅ **RESUELTO:** Función redundante `move_to_windows_recycle_bin()` eliminada
- ✅ **RESUELTO:** Alias confuso `PreviewService` eliminado
- ⚠️ Wrappers ligeros: 1 archivo (`focus_manager.py`)
- ⚠️ Fragmentación excesiva: FolderTreeSidebar (11 archivos)

### **Cambios Aplicados (Limpieza P0):**
- ✅ Eliminado alias `PreviewService` → UI usa directamente `PreviewPdfService`
- ✅ Eliminada función redundante `move_to_windows_recycle_bin()` → Unificado en `delete_file()`
- ✅ `file_view_context_menu.py` ahora usa `delete_file()` con lógica contextual
- ✅ `file_deletion_service.py` simplificado (solo `is_folder_empty()`)

### **Evaluación General:**
✅ **BUEN DISEÑO** - Arquitectura sólida con separación clara de capas. Limpieza P0 aplicada exitosamente. Problemas menores restantes: duplicación de nombres y fragmentación excesiva en algunos widgets.

---

## 📝 HISTORIAL DE CAMBIOS

### Limpieza Arquitectónica P0 (2025-01-29)

**Objetivo:** Eliminar duplicación real, alias innecesarios y unificar flujo de borrado.

**Cambios aplicados:**

1. **Eliminación de alias `PreviewService`**
   - Eliminado alias `PreviewService = PreviewPdfService` de `preview_service.py`
   - Actualizados 4 archivos UI para usar directamente `PreviewPdfService`:
     - `main_window.py`
     - `quick_preview_window.py`
     - `quick_preview_pdf_handler.py`
     - `quick_preview_thumbnails.py`
   - `preview_service.py` ahora solo contiene utilidades (`get_file_preview`, `get_windows_shell_icon`)

2. **Unificación de borrado de archivos**
   - Eliminada función redundante `move_to_windows_recycle_bin()` de `file_deletion_service.py`
   - `file_view_context_menu.py` ahora usa `delete_file()` con lógica contextual
   - Todos los borrados pasan por `file_delete_service.py` (servicio fuente de verdad)
   - `file_deletion_service.py` simplificado (solo contiene `is_folder_empty()`)

3. **Corrección de bug de diseño**
   - `file_view_context_menu.py` ahora respeta Desktop Focus y Trash Focus
   - Comportamiento unificado en toda la aplicación

**Resultado:**
- ✅ Código más claro y sin ambigüedades
- ✅ Bug silencioso corregido (borrados ahora respetan contexto)
- ✅ Arquitectura más limpia y profesional
- ✅ Sin imports rotos, sin cambios de comportamiento visible

---

**FIN DEL MAPA**
