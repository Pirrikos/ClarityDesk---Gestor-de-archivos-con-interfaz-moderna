# INFORME DE ESTADO - ClarityDesk Pro

**Fecha:** 29 de noviembre de 2025 (Actualizado)  
**Proyecto:** ClarityDesk Pro - Gestor de archivos con sistema de tabs (Focus)

---

## 📋 ÍNDICE

1. [Estructura del Proyecto](#estructura-del-proyecto)
2. [Árbol de Archivos y Funciones](#árbol-de-archivos-y-funciones)
3. [Flujo Principal](#flujo-principal)
4. [Dependencias Principales](#dependencias-principales)
5. [Puntos de Entrada](#puntos-de-entrada)

---

## 📁 ESTRUCTURA DEL PROYECTO

```
ClarityDesk_29-11-25/
├── main.py                          # Punto de entrada principal
├── arbol.tx                         # Árbol de estructura (legacy)
│
├── app/                             # Paquete principal
│   ├── __init__.py                  # Descripción del paquete
│   │
│   ├── core/                        # Core (vacío actualmente)
│   │   └── __init__.py
│   │
│   ├── managers/                    # Gestores de alto nivel
│   │   ├── tab_manager.py           # Gestor de tabs (Focus)
│   │   ├── focus_manager.py         # Orquestador de Focus
│   │   ├── file_state_manager.py    # Gestor de estados de archivos
│   │   └── __init__.py
│   │
│   ├── models/                      # Modelos de datos
│   │   ├── file_operation_result.py # Resultado de operaciones
│   │   └── __init__.py
│   │
│   ├── services/                    # Servicios de lógica de negocio
│   │   ├── Tab Management
│   │   │   ├── tab_manager_init.py      # Inicialización de TabManager
│   │   │   ├── tab_state_manager.py     # Gestión de estado de tabs
│   │   │   ├── tab_storage_service.py   # Persistencia de tabs
│   │   │   ├── tab_finder.py            # Búsqueda de tabs
│   │   │   ├── tab_validator.py         # Validación de carpetas
│   │   │   ├── tab_path_normalizer.py   # Normalización de rutas
│   │   │   ├── tab_index_helper.py      # Ayuda con índices
│   │   │   ├── tab_history_manager.py   # Historial de navegación
│   │   │   └── tab_navigation_handler.py # Navegación back/forward
│   │   │
│   │   ├── File Operations
│   │   │   ├── file_list_service.py     # Listado de archivos
│   │   │   ├── file_move_service.py     # Movimiento de archivos
│   │   │   ├── file_delete_service.py   # Eliminación (papelera)
│   │   │   ├── file_rename_service.py   # Renombrado individual
│   │   │   ├── file_path_utils.py       # Utilidades de rutas
│   │   │   └── file_extensions.py       # Extensiones soportadas
│   │   │
│   │   ├── File State
│   │   │   └── file_state_storage.py    # Persistencia SQLite de estados
│   │   │
│   │   ├── Icons & Preview
│   │   │   ├── icon_service.py          # Servicio principal de iconos
│   │   │   ├── preview_service.py       # Generación de previews
│   │   │   ├── icon_processor.py        # Procesamiento de iconos
│   │   │   ├── icon_renderer.py         # Renderizado de iconos
│   │   │   ├── icon_normalizer.py       # Normalización visual
│   │   │   ├── icon_conversion_helper.py # Conversión de formatos
│   │   │   ├── icon_extraction_fallbacks.py # Fallbacks de extracción
│   │   │   ├── windows_icon_extractor.py # Extracción nativa Windows
│   │   │   ├── windows_icon_converter.py # Conversión HICON a QPixmap
│   │   │   ├── pixel_analyzer.py        # Análisis de píxeles
│   │   │   ├── pdf_renderer.py          # Renderizado de PDFs
│   │   │   ├── docx_converter.py        # Conversión DOCX a PDF
│   │   │   └── preview_scaling.py       # Escalado de previews
│   │   │
│   │   ├── Rename
│   │   │   └── rename_service.py        # Renombrado masivo
│   │   │
│   │   ├── Trash (Papelera)
│   │   │   ├── trash_storage.py          # Almacenamiento y metadatos de papelera
│   │   │   ├── trash_operations.py        # Operaciones: mover, restaurar, eliminar
│   │   │   ├── trash_limits.py           # Verificación de límites (edad/tamaño)
│   │   │   └── trash_action_handler.py   # Manejador de acciones de papelera
│   │   │
│   │   ├── Desktop (Escritorio)
│   │   │   ├── desktop_operations.py     # Operaciones con archivos del escritorio
│   │   │   └── desktop_path_helper.py    # Detección y normalización de rutas Desktop
│   │   │
│   │   ├── Tab Helpers
│   │   │   └── tab_display_helper.py     # Conversión de rutas virtuales a nombres
│   │   │
│   │   ├── System
│   │   │   ├── filesystem_watcher_service.py # Observador de cambios
│   │   │   └── workspace_service.py     # Servicio de workspace
│   │   │
│   │   └── __init__.py
│   │
│   └── ui/                           # Interfaz de usuario
│       ├── __init__.py
│       │
│       ├── widgets/                  # Componentes UI reutilizables
│       │   ├── Views
│       │   │   ├── file_view_container.py    # Contenedor principal
│       │   │   ├── file_grid_view.py         # Vista de cuadrícula
│       │   │   ├── file_list_view.py         # Vista de lista
│       │   │   ├── file_tile.py              # Tile individual
│       │   │   └── grid_content_widget.py    # Contenido de grid
│       │   │
│       │   ├── Tree Sidebar
│       │   │   ├── folder_tree_sidebar.py    # Sidebar de árbol
│       │   │   ├── folder_tree_model.py      # Modelo del árbol
│       │   │   ├── folder_tree_handlers.py   # Manejadores de eventos
│       │   │   ├── folder_tree_drag_handler.py # Drag & drop árbol
│       │   │   └── folder_tree_styles.py     # Estilos del árbol
│       │   │
│       │   ├── Drag & Drop
│       │   │   ├── drag_common.py            # Utilidades comunes
│       │   │   ├── drag_preview_helper.py    # Ayuda de preview drag
│       │   │   ├── file_drop_handler.py      # Manejador de drops
│       │   │   ├── container_drag_handler.py # Drag del contenedor
│       │   │   ├── tile_drag_handler.py      # Drag de tiles
│       │   │   └── list_drag_handler.py      # Drag de lista
│       │   │
│       │   ├── Toolbar
│       │   │   ├── view_toolbar.py           # Barra de herramientas
│       │   │   ├── toolbar_navigation_buttons.py # Botones navegación
│       │   │   ├── toolbar_state_buttons.py  # Botones de estado
│       │   │   └── toolbar_button_styles.py  # Estilos de botones
│       │   │
│       │   ├── Focus Header
│       │   │   └── focus_header_panel.py     # Panel de encabezado Focus
│       │   │
│       │   ├── List Components
│       │   │   ├── list_row_factory.py       # Factory de filas
│       │   │   ├── list_icon_delegate.py     # Delegado de iconos
│       │   │   ├── list_state_cell.py        # Celda de estado
│       │   │   ├── list_checkbox.py          # Checkbox de lista
│       │   │   └── list_styles.py            # Estilos de lista
│       │   │
│       │   ├── Grid Components
│       │   │   ├── grid_selection_manager.py # Gestión de selección
│       │   │   └── tile_style.py             # Estilos de tiles
│       │   │
│       │   ├── Icons & Display
│       │   │   ├── icon_widget.py            # Widget de icono
│       │   │   ├── icon_painter.py          # Pintor de iconos
│       │   │   ├── state_badge_widget.py     # Badge de estado
│       │   │   └── text_elision.py           # Elisión de texto
│       │   │
│       │   ├── Rail
│       │   │   └── rail_widget.py           # Widget de rail (tabs)
│       │   │
│       │   ├── State Migration
│       │   │   └── file_state_migration.py  # Migración de estados
│       │   │
│       │   └── __init__.py
│       │
│       └── windows/                  # Ventanas principales
│           ├── main_window.py               # Ventana principal
│           ├── main_window_file_handler.py  # Manejador de archivos
│           ├── quick_preview_window.py      # Ventana de preview rápido
│           ├── quick_preview_ui_setup.py    # Configuración UI preview
│           ├── quick_preview_loader.py      # Cargador de previews
│           ├── quick_preview_cache.py       # Caché de previews
│           ├── quick_preview_navigation.py  # Navegación preview
│           ├── quick_preview_thumbnails.py  # Miniaturas preview
│           ├── quick_preview_thumbnail_widget.py # Widget miniatura
│           ├── quick_preview_pdf_handler.py # Manejador PDF preview
│           ├── quick_preview_header.py      # Encabezado preview
│           ├── quick_preview_styles.py      # Estilos preview
│           ├── quick_preview_animations.py  # Animaciones preview
│           ├── bulk_rename_dialog.py       # Diálogo renombrado masivo
│           ├── desktop_window.py           # Ventana de escritorio (Focus)
│           ├── trash_delete_dialog.py      # Diálogo de confirmación eliminación permanente
│           └── __init__.py
│
├── assets/                          # Recursos
│   ├── icons/                       # Iconos SVG genéricos
│   └── poppler/                     # Binarios Poppler (PDF)
│
├── data/                            # Datos de aplicación
│   └── rename_templates.json        # Plantillas de renombrado
│
├── storage/                         # Almacenamiento persistente
│   ├── claritydesk.db               # Base de datos SQLite (estados)
│   ├── tabs.json                    # Estado de tabs
│   └── trash/                       # Papelera interna
│       ├── files/                   # Archivos eliminados
│       └── metadata.json            # Metadatos (rutas originales, fechas)
│
└── INFORMES/                        # Documentación
    └── Reglas Principales/
        └── reglasprincipales.mdc
```

---

## 🌳 ÁRBOL DE ARCHIVOS Y FUNCIONES

### 📄 **main.py**
- **Función:** Punto de entrada principal de la aplicación
- **Responsabilidades:**
  - Crea QApplication
  - Inicializa TabManager y FocusManager
  - Crea y muestra MainWindow
  - Ejecuta el loop de eventos Qt

---

### 🎯 **MANAGERS** (Gestores de Alto Nivel)

#### **tab_manager.py**
- **Función:** Gestor central de tabs (Focus) y listados de archivos
- **Responsabilidades:**
  - Gestiona lista de tabs (carpetas abiertas)
  - Maneja tab activo
  - Persistencia de estado de tabs
  - Listado filtrado de archivos del tab activo
  - Emite señales: `tabsChanged`, `activeTabChanged`, `files_changed`
- **Dependencias:** TabStateManager, TabHistoryManager, TabNavigationHandler, FileListService, FileSystemWatcherService

#### **focus_manager.py**
- **Función:** Orquestador de creación y navegación de Focus
- **Responsabilidades:**
  - Abre o crea Focus para una ruta
  - Elimina Focus
  - Delega operaciones a TabManager
  - Emite señales: `focus_opened`, `focus_removed`

#### **file_state_manager.py**
- **Función:** Gestor de estados de archivos con persistencia SQLite
- **Responsabilidades:**
  - Cache de estados en memoria
  - Sincronización con SQLite
  - Operaciones batch de estados
  - Emite señales: `state_changed`, `states_changed`

---

### 📦 **MODELS** (Modelos de Datos)

#### **file_operation_result.py**
- **Función:** Modelo de resultado de operaciones de archivos
- **Responsabilidades:**
  - Encapsula éxito/error de operaciones
  - Mensajes de error
  - Métodos estáticos: `success()`, `error()`

---

### 🔧 **SERVICES** (Servicios de Lógica de Negocio)

#### **TAB MANAGEMENT**

##### **tab_manager_init.py**
- **Función:** Inicialización de componentes de TabManager
- **Responsabilidades:**
  - Obtiene ruta de almacenamiento
  - Configura FileSystemWatcherService
  - Configura QTimer para debounce

##### **tab_state_manager.py**
- **Función:** Gestión de estado interno de tabs
- **Responsabilidades:**
  - Carga estado desde almacenamiento
  - Guarda estado de tabs
  - Valida tabs al cargar

##### **tab_storage_service.py**
- **Función:** Persistencia de tabs en JSON
- **Responsabilidades:**
  - Carga estado desde JSON
  - Guarda estado a JSON
  - Validación y ajuste de índices

##### **tab_finder.py**
- **Función:** Búsqueda y creación de tabs
- **Responsabilidades:**
  - `find_tab_index()`: Busca índice de tab existente
  - `find_or_add_tab()`: Busca o crea tab si no existe

##### **tab_validator.py**
- **Función:** Validación de carpetas
- **Responsabilidades:**
  - `validate_folder()`: Verifica que carpeta existe y es válida

##### **tab_path_normalizer.py**
- **Función:** Normalización de rutas
- **Responsabilidades:**
  - `normalize_path()`: Normaliza rutas para comparación consistente

##### **tab_index_helper.py**
- **Función:** Utilidades de índices de tabs
- **Responsabilidades:**
  - `adjust_active_index_after_remove()`: Ajusta índice activo tras eliminar tab

##### **tab_history_manager.py**
- **Función:** Historial de navegación back/forward
- **Responsabilidades:**
  - Mantiene historial de carpetas visitadas
  - Navegación hacia atrás/adelante
  - Flag de navegación para evitar loops

##### **tab_navigation_handler.py**
- **Función:** Lógica de navegación back/forward
- **Responsabilidades:**
  - `go_back()`: Navega hacia atrás
  - `go_forward()`: Navega hacia adelante
  - `can_go_back()` / `can_go_forward()`: Verifica disponibilidad
  - Activa carpeta sin crear nueva entrada en historial

#### **FILE OPERATIONS**

##### **file_list_service.py**
- **Función:** Listado de archivos de carpetas
- **Responsabilidades:**
  - `get_files()`: Lista archivos filtrados por extensión
  - Incluye carpetas y archivos ejecutables sin extensión
  - Detecta archivos PE (MZ header)

##### **file_move_service.py**
- **Función:** Movimiento de archivos entre carpetas
- **Responsabilidades:**
  - `move_file()`: Mueve archivo/carpeta a destino
  - Resolución de conflictos
  - Validación de rutas

##### **file_delete_service.py**
- **Función:** Eliminación segura de archivos con soporte para Desktop y Trash Focus
- **Responsabilidades:**
  - `delete_file()`: Elimina archivo según contexto
  - Desktop Focus: Usa TrashService (papelera interna)
  - Trash Focus: Eliminación permanente (requiere confirmación)
  - Carpetas normales: Papelera de reciclaje Windows (SHFileOperationW)

##### **file_rename_service.py**
- **Función:** Renombrado individual de archivos
- **Responsabilidades:**
  - Renombrado con validación
  - Manejo de errores

##### **file_path_utils.py**
- **Función:** Utilidades de validación y manipulación de rutas
- **Responsabilidades:**
  - `validate_file()`, `validate_folder()`, `validate_path()`
  - `resolve_conflict()`: Resuelve conflictos de nombres

##### **file_extensions.py**
- **Función:** Definición de extensiones soportadas
- **Responsabilidades:**
  - `SUPPORTED_EXTENSIONS`: Set de extensiones permitidas

#### **FILE STATE**

##### **file_state_storage.py**
- **Función:** Persistencia SQLite de estados de archivos
- **Responsabilidades:**
  - Inicialización de esquema SQLite
  - `set_state()` / `set_states_batch()`: Guarda estados
  - `remove_state()` / `remove_states_batch()`: Elimina estados
  - `get_state_by_path()`: Obtiene estado por ruta
  - `get_file_id_from_path()`: Obtiene ID de archivo
  - `update_path_for_rename()`: Actualiza ruta tras renombrar
  - `remove_missing_files()`: Limpia archivos inexistentes
  - `load_all_states()`: Carga todos los estados

#### **ICONS & PREVIEW**

##### **icon_service.py**
- **Función:** Servicio principal de iconos nativos Windows
- **Responsabilidades:**
  - `get_file_icon()`: Obtiene icono nativo Windows
  - Cache de iconos por extensión
  - Soporte para previews PDF reales con Poppler

##### **preview_service.py**
- **Función:** Generación de previews de archivos
- **Responsabilidades:**
  - `get_file_preview()`: Genera preview de archivo
  - Renderizado de PDFs y DOCX
  - Fallback a iconos SVG
  - Escalado y normalización visual

##### **icon_processor.py**
- **Función:** Procesamiento de iconos
- **Responsabilidades:**
  - `has_excessive_whitespace()`: Detecta espacios excesivos

##### **icon_renderer.py**
- **Función:** Renderizado de iconos y previews
- **Responsabilidades:**
  - `render_image_preview()`: Renderiza imágenes
  - `render_svg_icon()`: Renderiza iconos SVG
  - `get_svg_for_extension()`: Obtiene SVG por extensión

##### **icon_normalizer.py**
- **Función:** Normalización visual de iconos
- **Responsabilidades:**
  - `normalize_for_list()`: Normaliza para lista
  - `apply_visual_normalization()`: Aplica normalización visual

##### **icon_conversion_helper.py**
- **Función:** Conversión entre formatos de iconos
- **Responsabilidades:**
  - Conversión entre formatos Windows/Qt

##### **icon_extraction_fallbacks.py**
- **Función:** Fallbacks para extracción de iconos
- **Responsabilidades:**
  - `get_icon_via_extracticon()`: Extracción vía ExtractIcon
  - `get_icon_via_qicon()`: Extracción vía QFileIconProvider

##### **windows_icon_extractor.py**
- **Función:** Extracción nativa de iconos Windows
- **Responsabilidades:**
  - `get_icon_via_imagelist()`: Extracción vía ImageList

##### **windows_icon_converter.py**
- **Función:** Conversión de HICON a QPixmap
- **Responsabilidades:**
  - `hicon_to_qpixmap_at_size()`: Convierte HICON a QPixmap

##### **pixel_analyzer.py**
- **Función:** Análisis de píxeles de iconos
- **Responsabilidades:**
  - Análisis de contenido de iconos

##### **pdf_renderer.py**
- **Función:** Renderizado de PDFs usando Poppler
- **Responsabilidades:**
  - Renderizado de páginas PDF a QPixmap
  - Clase `PdfRenderer`

##### **docx_converter.py**
- **Función:** Conversión de DOCX a PDF
- **Responsabilidades:**
  - Conversión de DOCX a PDF para preview
  - Clase `DocxConverter`

##### **preview_scaling.py**
- **Función:** Escalado de previews
- **Responsabilidades:**
  - `scale_pixmap_to_size()`: Escala QPixmap a tamaño
  - `scale_if_needed()`: Escala si es necesario

#### **RENAME**

##### **rename_service.py**
- **Función:** Servicio de renombrado masivo
- **Responsabilidades:**
  - `generate_preview()`: Genera preview de renombrados
  - `apply_renames()`: Aplica renombrados
  - Soporte para plantillas con `{n}`, `{name}`, `{date}`
  - Carga/guarda plantillas desde JSON

#### **SYSTEM**

##### **filesystem_watcher_service.py**
- **Función:** Observador de cambios en sistema de archivos
- **Responsabilidades:**
  - Observa cambios en carpeta activa
  - Emite señales cuando cambian archivos
  - Usa QFileSystemWatcher

##### **workspace_service.py**
- **Función:** Servicio de workspace
- **Responsabilidades:**
  - `get_workspace_root()`: Obtiene raíz del workspace

#### **TRASH (PAPELERA)**

##### **trash_storage.py**
- **Función:** Almacenamiento y gestión de metadatos de papelera
- **Responsabilidades:**
  - `get_trash_path()`: Obtiene ruta de carpeta de papelera
  - `load_trash_metadata()` / `save_trash_metadata()`: Persistencia JSON
  - `list_trash_files()`: Lista archivos en papelera
  - `get_trash_metadata_for_file()`: Obtiene metadatos de archivo
  - Constantes: `TRASH_FOCUS_PATH`, `MAX_TRASH_AGE_DAYS`, `MAX_TRASH_SIZE_MB`

##### **trash_operations.py**
- **Función:** Operaciones de papelera (único servicio autorizado para eliminar permanentemente)
- **Responsabilidades:**
  - `move_to_trash()`: Mueve archivo a papelera interna con metadatos
  - `restore_from_trash()`: Restaura archivo a ubicación original (o Desktop)
  - `delete_permanently()`: Eliminación permanente irreversible

##### **trash_limits.py**
- **Función:** Verificación de límites de papelera (solo verifica, nunca elimina automáticamente)
- **Responsabilidades:**
  - `check_trash_limits()`: Verifica si excede límites de edad o tamaño
  - `cleanup_if_needed()`: Alias para verificación de límites

##### **trash_action_handler.py**
- **Función:** Manejador de acciones de papelera
- **Responsabilidades:**
  - `restore_file_from_trash()`: Restaura archivo desde papelera
  - `delete_file_permanently()`: Eliminación permanente (requiere confirmación)

#### **DESKTOP (ESCRITORIO)**

##### **desktop_operations.py**
- **Función:** Operaciones con archivos del escritorio Windows
- **Responsabilidades:**
  - `load_desktop_files()`: Lista archivos del escritorio
  - `move_into_desktop()`: Mueve archivo al escritorio
  - `move_out_of_desktop()`: Mueve archivo fuera del escritorio
  - `rename_desktop_file()`: Renombra archivo en escritorio
  - Nunca elimina archivos (usa TrashService)

##### **desktop_path_helper.py**
- **Función:** Detección y normalización de rutas del escritorio
- **Responsabilidades:**
  - `get_desktop_path()`: Obtiene ruta del escritorio Windows (vía registro)
  - `normalize_path()`: Normaliza rutas para comparación
  - `is_desktop_focus()`: Detecta si ruta es Desktop Focus (real o virtual)
  - Constante: `DESKTOP_FOCUS_PATH`

#### **TAB HELPERS**

##### **tab_display_helper.py**
- **Función:** Conversión de rutas virtuales a nombres de visualización
- **Responsabilidades:**
  - `get_tab_display_name()`: Convierte rutas a nombres amigables
  - Desktop Focus → "Escritorio"
  - Trash Focus → "Papelera"
  - Rutas normales → basename

---

### 🎨 **UI** (Interfaz de Usuario)

#### **WIDGETS** (Componentes UI)

##### **Views**

###### **file_view_container.py**
- **Función:** Contenedor principal de vistas de archivos
- **Responsabilidades:**
  - Gestiona cambio entre vista grid y lista
  - Se suscribe a TabManager para actualizar archivos
  - Maneja drag & drop de archivos
  - Integra FocusHeaderPanel y ViewToolbar
  - Emite señal `open_file` para preview rápido

###### **file_grid_view.py**
- **Función:** Vista de cuadrícula de archivos
- **Responsabilidades:**
  - Muestra archivos en grid con tiles
  - Gestión de selección múltiple
  - Scroll y navegación

###### **file_list_view.py**
- **Función:** Vista de lista de archivos (QTableWidget)
- **Responsabilidades:**
  - Muestra archivos en tabla
  - Columnas: checkbox, icono, nombre, estado
  - Selección múltiple

###### **file_tile.py**
- **Función:** Tile individual de archivo en grid
- **Responsabilidades:**
  - Muestra icono, nombre y badge de estado
  - Maneja clicks y doble-click
  - Estilos y elisión de texto

###### **grid_content_widget.py**
- **Función:** Widget de contenido del grid
- **Responsabilidades:**
  - Contenedor del grid con scroll

##### **Tree Sidebar**

###### **folder_tree_sidebar.py**
- **Función:** Sidebar con árbol de carpetas
- **Responsabilidades:**
  - Muestra árbol de carpetas Focus
  - Navegación por árbol
  - Botón para agregar Focus
  - Menú contextual

###### **folder_tree_model.py**
- **Función:** Modelo de datos del árbol
- **Responsabilidades:**
  - `add_focus_path_to_model()`: Añade ruta Focus al modelo
  - `remove_focus_path_from_model()`: Elimina ruta del modelo
  - `find_parent_item()`: Encuentra item padre

###### **folder_tree_handlers.py**
- **Función:** Manejadores de eventos del árbol
- **Responsabilidades:**
  - `handle_tree_click()`: Maneja clicks en árbol
  - `handle_add_button_click()`: Maneja botón agregar
  - `handle_context_menu()`: Maneja menú contextual

###### **folder_tree_drag_handler.py**
- **Función:** Manejador de drag & drop del árbol
- **Responsabilidades:**
  - `handle_drag_enter()`: Maneja entrada de drag
  - `handle_drag_move()`: Maneja movimiento de drag
  - `handle_drop()`: Maneja drop de archivos
  - `get_drop_target_path()`: Obtiene ruta destino
  - `_process_dropped_files()`: Procesa archivos soltados

###### **folder_tree_styles.py**
- **Función:** Estilos del árbol de carpetas
- **Responsabilidades:**
  - `get_complete_stylesheet()`: Obtiene stylesheet completo
  - Estilos base, árbol, items, branches

##### **Drag & Drop**

###### **drag_common.py**
- **Función:** Utilidades comunes de drag & drop
- **Responsabilidades:**
  - Funciones compartidas para drag & drop

###### **drag_preview_helper.py**
- **Función:** Ayuda para preview de drag
- **Responsabilidades:**
  - Crea preview visual durante drag

###### **file_drop_handler.py**
- **Función:** Manejador de drops de archivos
- **Responsabilidades:**
  - `handle_drag_enter()`: Maneja entrada de drag
  - `handle_drag_move()`: Maneja movimiento
  - `handle_drop()`: Maneja drop
  - `handle_file_drop()`: Procesa archivos soltados

###### **container_drag_handler.py**
- **Función:** Manejador de drag del contenedor
- **Responsabilidades:**
  - Drag & drop a nivel de contenedor

###### **tile_drag_handler.py**
- **Función:** Manejador de drag de tiles
- **Responsabilidades:**
  - `handle_tile_drag()`: Inicia drag desde tile
  - `_create_drag_object()`: Crea objeto QDrag
  - `_get_drag_file_paths()`: Obtiene rutas para drag
  - `_get_drag_preview()`: Crea preview de drag

###### **list_drag_handler.py**
- **Función:** Manejador de drag de lista
- **Responsabilidades:**
  - `handle_start_drag()`: Inicia drag desde lista
  - `is_same_folder_drop()`: Verifica si es misma carpeta
  - `handle_drag_enter()` / `handle_drag_move()` / `handle_drop()`
  - `_extract_file_paths_from_items()`: Extrae rutas de items

##### **Toolbar**

###### **view_toolbar.py**
- **Función:** Barra de herramientas de vista
- **Responsabilidades:**
  - Botones de cambio de vista (grid/lista)
  - Botones de navegación (back/forward)
  - Botones de estado
  - Botón limpiar estados

###### **toolbar_navigation_buttons.py**
- **Función:** Botones de navegación
- **Responsabilidades:**
  - `create_navigation_buttons()`: Crea botones back/forward

###### **toolbar_state_buttons.py**
- **Función:** Botones de estado
- **Responsabilidades:**
  - `create_state_buttons()`: Crea botones de estados

###### **toolbar_button_styles.py**
- **Función:** Estilos de botones de toolbar
- **Responsabilidades:**
  - `get_view_button_style()`: Estilo botón vista
  - `get_nav_button_style()`: Estilo botón navegación
  - `get_state_button_style()`: Estilo botón estado
  - `get_clear_button_style()`: Estilo botón limpiar

##### **Focus Header**

###### **focus_header_panel.py**
- **Función:** Panel de encabezado de Focus
- **Responsabilidades:**
  - Muestra información del Focus activo
  - Título y acciones

##### **List Components**

###### **list_row_factory.py**
- **Función:** Factory para crear filas de lista
- **Responsabilidades:**
  - Crea filas con checkbox, icono, nombre, estado

###### **list_icon_delegate.py**
- **Función:** Delegado para renderizar iconos en lista
- **Responsabilidades:**
  - Renderiza iconos en columna de lista

###### **list_state_cell.py**
- **Función:** Celda de estado en lista
- **Responsabilidades:**
  - Renderiza badge de estado

###### **list_checkbox.py**
- **Función:** Checkbox de lista
- **Responsabilidades:**
  - Checkbox para selección

###### **list_styles.py**
- **Función:** Estilos de lista
- **Responsabilidades:**
  - Stylesheets para vista de lista

##### **Grid Components**

###### **grid_selection_manager.py**
- **Función:** Gestión de selección en grid
- **Responsabilidades:**
  - Maneja selección múltiple de tiles

###### **tile_style.py**
- **Función:** Estilos de tiles
- **Responsabilidades:**
  - Stylesheets para tiles

##### **Icons & Display**

###### **icon_widget.py**
- **Función:** Widget para mostrar iconos
- **Responsabilidades:**
  - Widget reutilizable para iconos

###### **icon_painter.py**
- **Función:** Pintor de iconos
- **Responsabilidades:**
  - Lógica de pintado de iconos

###### **state_badge_widget.py**
- **Función:** Widget de badge de estado
- **Responsabilidades:**
  - Muestra badge con estado de archivo

###### **text_elision.py**
- **Función:** Elisión de texto
- **Responsabilidades:**
  - Trunca texto con "..." cuando es largo

##### **Rail**

###### **rail_widget.py**
- **Función:** Widget de rail (tabs)
- **Responsabilidades:**
  - Muestra tabs como rail horizontal
  - Navegación entre tabs

##### **State Migration**

###### **file_state_migration.py**
- **Función:** Migración de estados tras renombrar
- **Responsabilidades:**
  - `migrate_states_on_rename()`: Migra estados cuando se renombra archivo

#### **WINDOWS** (Ventanas)

##### **main_window.py**
- **Función:** Ventana principal de la aplicación
- **Responsabilidades:**
  - Layout principal con sidebar y área de contenido
  - Integra FolderTreeSidebar y FileViewContainer
  - Maneja preview rápido (QuickPreviewWindow)
  - Atajos de teclado
  - Conexión de señales

##### **main_window_file_handler.py**
- **Función:** Manejador de archivos de ventana principal
- **Responsabilidades:**
  - `open_file_with_system()`: Abre archivo con aplicación del sistema
  - `filter_previewable_files()`: Filtra archivos previewables

##### **quick_preview_window.py**
- **Función:** Ventana de preview rápido estilo QuickLook
- **Responsabilidades:**
  - Preview inmersivo a pantalla completa
  - Navegación entre archivos
  - Soporte para PDFs multi-página
  - Animaciones

##### **quick_preview_ui_setup.py**
- **Función:** Configuración de UI de preview
- **Responsabilidades:**
  - Setup de layout y componentes UI

##### **quick_preview_loader.py**
- **Función:** Cargador de previews
- **Responsabilidades:**
  - Carga previews de forma asíncrona
  - Gestión de carga

##### **quick_preview_cache.py**
- **Función:** Caché de previews
- **Responsabilidades:**
  - Cachea previews para rendimiento

##### **quick_preview_navigation.py**
- **Función:** Navegación en preview
- **Responsabilidades:**
  - Navegación entre archivos
  - Teclado y mouse

##### **quick_preview_thumbnails.py**
- **Función:** Miniaturas en preview
- **Responsabilidades:**
  - Muestra miniaturas de archivos

##### **quick_preview_thumbnail_widget.py**
- **Función:** Widget de miniatura
- **Responsabilidades:**
  - Widget individual de miniatura

##### **quick_preview_pdf_handler.py**
- **Función:** Manejador de PDFs en preview
- **Responsabilidades:**
  - Manejo específico de PDFs multi-página

##### **quick_preview_header.py**
- **Función:** Encabezado de preview
- **Responsabilidades:**
  - Muestra información del archivo

##### **quick_preview_styles.py**
- **Función:** Estilos de preview
- **Responsabilidades:**
  - Stylesheets para ventana de preview

##### **quick_preview_animations.py**
- **Función:** Animaciones de preview
- **Responsabilidades:**
  - Animaciones de transición

##### **bulk_rename_dialog.py**
- **Función:** Diálogo de renombrado masivo
- **Responsabilidades:**
  - UI para renombrado masivo
  - Preview de renombrados
  - Integración con RenameService

##### **desktop_window.py**
- **Función:** Ventana de escritorio (Desktop Focus)
- **Responsabilidades:**
  - Muestra archivos del escritorio Windows
  - Integración con DesktopOperations
  - Soporte para Focus virtual de escritorio

##### **trash_delete_dialog.py**
- **Función:** Diálogo de confirmación para eliminación permanente
- **Responsabilidades:**
  - Confirma eliminación permanente desde papelera
  - Advertencia de operación irreversible
  - Integración con TrashOperations

---

## 🔄 FLUJO PRINCIPAL

### 1. **Inicialización**
```
main.py
  └─> Crea QApplication
  └─> TabManager()
      └─> TabStateManager (carga tabs.json)
      └─> TabHistoryManager (historial vacío)
      └─> FileSystemWatcherService (observador)
  └─> FocusManager(TabManager)
  └─> MainWindow(TabManager, FocusManager)
      └─> IconService()
      └─> PreviewService(IconService)
      └─> FileViewContainer(TabManager, IconService)
      └─> FolderTreeSidebar()
```

### 2. **Abrir Focus (Tab)**
```
Usuario hace click en árbol o agrega Focus
  └─> FocusManager.open_or_create_focus_for_path()
      └─> TabManager.add_tab()
          └─> TabFinder.find_or_add_tab()
          └─> TabStateManager.save_state()
          └─> FileSystemWatcherService.watch_folder()
          └─> Emite activeTabChanged
      └─> Emite focus_opened
  └─> FileViewContainer recibe señal
      └─> Actualiza archivos con FileListService.get_files()
      └─> Actualiza vista (grid o lista)
```

### 3. **Mostrar Archivos**
```
TabManager emite activeTabChanged
  └─> FileViewContainer._on_active_tab_changed()
      └─> FileListService.get_files(folder_path, extensions)
          └─> Lista archivos y carpetas filtrados
      └─> FileGridView o FileListView actualiza
          └─> FileTile para cada archivo
              └─> IconService.get_file_icon()
              └─> FileStateManager.get_state()
```

### 4. **Preview Rápido**
```
Usuario hace doble-click en archivo
  └─> FileTile emite señal open_file
  └─> FileViewContainer emite open_file
  └─> MainWindow._on_open_file()
      └─> QuickPreviewWindow(preview_service, file_path, file_paths)
          └─> QuickPreviewLoader carga preview
              └─> PreviewService.get_file_preview()
                  └─> PdfRenderer (si es PDF)
                  └─> DocxConverter (si es DOCX)
                  └─> IconService (fallback)
```

### 5. **Drag & Drop**
```
Usuario arrastra archivo
  └─> TileDragHandler o ListDragHandler
      └─> Crea QDrag con rutas
  └─> Usuario suelta en carpeta
      └─> FileDropHandler.handle_drop()
          └─> FileMoveService.move_file()
              └─> shutil.move()
          └─> FileStateManager actualiza estados si necesario
```

### 6. **Renombrado Masivo**
```
Usuario selecciona archivos y abre diálogo
  └─> BulkRenameDialog
      └─> RenameService.generate_preview()
          └─> Genera preview de nuevos nombres
      └─> Usuario confirma
          └─> RenameService.apply_renames()
              └─> os.rename() para cada archivo
              └─> FileStateManager.update_path_for_rename()
```

### 7. **Eliminación a Papelera**
```
Usuario elimina archivo
  └─> FileDeleteService.delete_file()
      └─> Desktop Focus: TrashOperations.move_to_trash()
          └─> Mueve a storage/trash/files/
          └─> Guarda metadatos (ruta original, fecha)
      └─> Trash Focus: TrashOperations.delete_permanently()
          └─> TrashDeleteDialog (confirmación)
          └─> Eliminación permanente
      └─> Carpeta normal: Papelera Windows (SHFileOperationW)
```

### 8. **Restauración desde Papelera**
```
Usuario restaura archivo desde papelera
  └─> TrashActionHandler.restore_file_from_trash()
      └─> TrashOperations.restore_from_trash()
          └─> Lee metadatos (ruta original)
          └─> Restaura a ubicación original (o Desktop si no existe)
          └─> Elimina de metadatos
```

### 9. **Desktop Focus**
```
Usuario abre Desktop Focus
  └─> FocusManager.open_or_create_focus_for_path(DESKTOP_FOCUS_PATH)
      └─> TabManager.add_tab(DESKTOP_FOCUS_PATH)
      └─> FileListService.get_files() detecta Desktop Focus
          └─> DesktopOperations.load_desktop_files()
              └─> Lista archivos del escritorio Windows
      └─> TabDisplayHelper.get_tab_display_name()
          └─> Convierte a "Escritorio"
```

### 10. **Trash Focus**
```
Usuario abre Trash Focus
  └─> FocusManager.open_or_create_focus_for_path(TRASH_FOCUS_PATH)
      └─> TabManager.add_tab(TRASH_FOCUS_PATH)
      └─> FileListService.get_files() detecta Trash Focus
          └─> TrashStorage.list_trash_files()
              └─> Lista archivos en storage/trash/files/
      └─> TabDisplayHelper.get_tab_display_name()
          └─> Convierte a "Papelera"
```

---

## 🔗 DEPENDENCIAS PRINCIPALES

### **Flujo de Dependencias:**

```
main.py
  ├─> TabManager
  │     ├─> TabStateManager
  │     ├─> TabHistoryManager
  │     ├─> TabNavigationHandler
  │     ├─> TabFinder
  │     ├─> TabValidator
  │     ├─> TabPathNormalizer
  │     ├─> FileListService
  │     └─> FileSystemWatcherService
  │
  ├─> FocusManager
  │     └─> TabManager
  │
  └─> MainWindow
        ├─> TabManager
        ├─> FocusManager
        ├─> IconService
        │     ├─> IconNormalizer
        │     ├─> PreviewService
        │     └─> WindowsIconConverter
        │
        ├─> PreviewService
        │     ├─> IconProcessor
        │     ├─> IconRenderer
        │     ├─> WindowsIconExtractor
        │     ├─> PdfRenderer
        │     ├─> DocxConverter
        │     └─> PreviewScaling
        │
        ├─> FileViewContainer
        │     ├─> TabManager
        │     ├─> IconService
        │     ├─> FileStateManager
        │     ├─> RenameService
        │     ├─> FileDeleteService
        │     │     ├─> TrashOperations (Desktop/Trash Focus)
        │     │     └─> Windows Recycle Bin (carpetas normales)
        │     ├─> DesktopOperations (si Desktop Focus)
        │     ├─> TrashStorage (si Trash Focus)
        │     ├─> TabDisplayHelper
        │     ├─> FileGridView
        │     ├─> FileListView
        │     ├─> FileDropHandler
        │     └─> FocusHeaderPanel
        │
        └─> FolderTreeSidebar
              ├─> FocusManager
              └─> FolderTreeModel
```

### **Jerarquía de Servicios:**

```
IconService (nivel alto)
  └─> PreviewService
        ├─> IconProcessor
        ├─> IconRenderer
        ├─> IconNormalizer
        ├─> WindowsIconExtractor
        ├─> WindowsIconConverter
        ├─> PdfRenderer
        ├─> DocxConverter
        └─> PreviewScaling
```

---

## 🚪 PUNTOS DE ENTRADA

### **1. main.py**
- **Función:** `main()`
- **Descripción:** Punto de entrada principal de la aplicación

### **2. Señales Qt Principales:**
- `TabManager.tabsChanged` → Actualiza UI de tabs
- `TabManager.activeTabChanged` → Actualiza vista de archivos
- `TabManager.files_changed` → Refresca lista de archivos
- `FocusManager.focus_opened` → Actualiza árbol de carpetas
- `FileStateManager.state_changed` → Actualiza badges de estado

### **3. Eventos de Usuario:**
- Click en árbol → `FolderTreeHandlers.handle_tree_click()`
- Doble-click en archivo → `FileTile` emite `open_file`
- Drag & Drop → `FileDropHandler.handle_drop()`
- Renombrado masivo → `BulkRenameDialog`

---

## 📊 ESTADÍSTICAS

- **Total de archivos Python:** ~100 archivos
- **Managers:** 3 archivos
- **Services:** ~40 archivos
  - Tab Management: 9 servicios
  - File Operations: 6 servicios
  - Trash: 4 servicios
  - Desktop: 2 servicios
  - Icons & Preview: 12 servicios
  - Otros: 7 servicios
- **UI Widgets:** ~35 archivos
- **UI Windows:** ~16 archivos
- **Models:** 1 archivo

---

## 🎯 NOTAS IMPORTANTES

1. **Separación de Responsabilidades:**
   - Managers: Orquestación de alto nivel
   - Services: Lógica de negocio pura
   - UI: Presentación y eventos

2. **Persistencia:**
   - Tabs: `storage/tabs.json` (JSON)
   - Estados de archivos: `storage/claritydesk.db` (SQLite)
   - Papelera: `storage/trash/files/` (archivos) + `storage/trash/metadata.json` (metadatos)

3. **Señales Qt:**
   - Comunicación desacoplada entre componentes
   - Patrón Observer para actualizaciones de UI

4. **Iconos:**
   - Nativos Windows con fallback a SVG
   - Cache por extensión
   - Preview real para PDFs y DOCX

5. **Preview Rápido:**
   - Ventana inmersiva estilo QuickLook
   - Soporte multi-página para PDFs
   - Navegación con teclado y mouse

6. **Papelera Interna:**
   - Sistema de papelera propio (`storage/trash/`)
   - Metadatos con rutas originales y fechas de eliminación
   - Límites configurables (edad: 30 días, tamaño: 2048MB)
   - Restauración a ubicación original o Desktop
   - Eliminación permanente con confirmación

7. **Desktop Focus:**
   - Focus virtual para escritorio Windows
   - Integración con escritorio real del sistema
   - Operaciones específicas (mover dentro/fuera, renombrar)
   - Eliminación usa papelera interna (no reciclaje Windows)

---

**Fin del Informe**

