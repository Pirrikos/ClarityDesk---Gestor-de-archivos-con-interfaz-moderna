# Catálogo de Ventanas Emergentes - ClarityDesk

Este documento lista todas las ventanas emergentes (diálogos, mensajes, menús) encontradas en el proyecto.

---

## 1. DIÁLOGOS PERSONALIZADOS (QDialog)

### 1.1. BulkRenameDialog
**Archivo:** `app/ui/windows/bulk_rename_dialog.py`  
**Líneas:** 29-318  
**Descripción:** Diálogo para renombrar múltiples archivos con patrones, búsqueda/reemplazo y vista previa.  
**Uso:** Se muestra cuando el usuario selecciona archivos y hace clic en "Renombrar".  
**Mensajes internos:** 
- Línea 254: `QMessageBox.warning` - Error al renombrar archivos

### 1.2. TrashDeleteDialog
**Archivo:** `app/ui/windows/trash_delete_dialog.py`  
**Líneas:** 18-107  
**Descripción:** Diálogo de confirmación para eliminación permanente desde la papelera.  
**Uso:** Se muestra cuando el usuario intenta eliminar permanentemente un archivo de la papelera.  
**Mensajes internos:**
- Línea 93: `QMessageBox.warning` - Confirmación requerida (si no se marca el checkbox)

### 1.3. RenameStateDialog
**Archivo:** `app/ui/widgets/rename_state_dialog.py`  
**Líneas:** 37-252  
**Descripción:** Diálogo modal para renombrar etiquetas de estado (Pendiente, Entregado, Corregido, Revisar).  
**Uso:** Se muestra desde el menú de estados cuando se selecciona "Renombrar etiqueta…".  
**Mensajes internos:**
- Línea 230: `QMessageBox.warning` - Nombre inválido (vacío)
- Línea 244: `QMessageBox.warning` - Error al renombrar etiqueta

---

## 2. MENSAJES DE DIÁLOGO (QMessageBox)

### 2.1. MainWindow (`app/ui/windows/main_window.py`)

**Línea 705:** `QMessageBox.warning`
- **Título:** "No se puede abrir"
- **Mensaje:** "No hay aplicación asociada o el archivo no es reconocible.\nIntenta abrirlo manualmente desde el sistema."
- **Contexto:** Cuando falla la apertura de un archivo con el sistema

**Línea 866:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** Mensaje de error al restaurar estado
- **Contexto:** Error al restaurar el estado de la aplicación

**Línea 976:** `QMessageBox.information`
- **Título:** "Información"
- **Mensaje:** Información sobre estado
- **Contexto:** Información al usuario

**Línea 994:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** Error al guardar estado
- **Contexto:** Error al guardar el estado de la aplicación

**Línea 1014:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** Error al cerrar tabs
- **Contexto:** Error al cerrar pestañas

**Línea 1041:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** Error al restaurar tabs
- **Contexto:** Error al restaurar pestañas

### 2.2. WorkspaceSelector (`app/ui/widgets/workspace_selector.py`)

**Línea 422:** `QMessageBox.warning`
- **Título:** "Nombre inválido"
- **Mensaje:** "El nombre del workspace no puede estar vacío."
- **Contexto:** Al intentar renombrar workspace con nombre vacío

**Línea 440:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** "No se pudo renombrar el workspace."
- **Contexto:** Error al renombrar workspace

**Línea 459:** `QMessageBox.question`
- **Título:** "Eliminar Workspace"
- **Mensaje:** "¿Estás seguro de que quieres eliminar el workspace \"{workspace_name}\"?\n\nEsta acción no se puede deshacer."
- **Contexto:** Confirmación antes de eliminar workspace

### 2.3. BulkRenameDialog (`app/ui/windows/bulk_rename_dialog.py`)

**Línea 254:** `QMessageBox.warning`
- **Título:** "Error al renombrar"
- **Mensaje:** "No se pueden renombrar los archivos:\n\n{error_msg}\n\nPor favor, verifica los nombres e intenta nuevamente."
- **Contexto:** Error de validación al aplicar renombrado

### 2.4. RenameStateDialog (`app/ui/widgets/rename_state_dialog.py`)

**Línea 230:** `QMessageBox.warning`
- **Título:** "Nombre inválido"
- **Mensaje:** "El nombre de la etiqueta no puede estar vacío."
- **Contexto:** Validación de nombre vacío

**Línea 244:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** Error del manager o mensaje por defecto
- **Contexto:** Error al renombrar etiqueta

### 2.5. FileViewContainer (`app/ui/widgets/file_view_container.py`)

**Línea 353:** `QMessageBox.critical`
- **Título:** "Error al renombrar"
- **Mensaje:** Mensaje de error amigable al usuario
- **Contexto:** Error crítico al renombrar archivo

### 2.6. TrashDeleteDialog (`app/ui/windows/trash_delete_dialog.py`)

**Línea 93:** `QMessageBox.warning`
- **Título:** "Confirmación requerida"
- **Mensaje:** "Debes marcar la casilla para confirmar la eliminación permanente."
- **Contexto:** Validación de checkbox antes de eliminar

### 2.7. FileViewContextMenu (`app/ui/widgets/file_view_context_menu.py`)

**Línea 202:** `QMessageBox.warning`
- **Título:** "Error al crear carpeta"
- **Mensaje:** Mensaje de error del servicio
- **Contexto:** Error al crear carpeta desde menú contextual

**Línea 256:** `QMessageBox.warning`
- **Título:** "Error al mover a la papelera"
- **Mensaje:** Lista de errores por archivo
- **Contexto:** Errores al mover archivos a la papelera

**Línea 367:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** Error al eliminar permanentemente
- **Contexto:** Error al eliminar archivo permanentemente

**Línea 416:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** Error al restaurar archivo desde papelera
- **Contexto:** Error al restaurar archivo

**Línea 461:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** Error al renombrar archivo
- **Contexto:** Error al renombrar desde menú contextual

**Línea 478:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** Error al copiar archivo
- **Contexto:** Error al copiar archivo

### 2.8. FileBoxUIUtils (`app/ui/utils/file_box_ui_utils.py`)

**Línea 15:** `QMessageBox.information`
- **Título:** "Carpeta no disponible"
- **Mensaje:** "La carpeta temporal ya no está disponible."
- **Contexto:** Carpeta temporal no existe al intentar abrirla

**Línea 31:** `QMessageBox.warning`
- **Título:** "Error"
- **Mensaje:** "No se pudo abrir la carpeta:\n{folder_path}"
- **Contexto:** Error al abrir carpeta en el explorador del sistema

---

## 3. DIÁLOGOS DE ENTRADA (QInputDialog)

### 3.1. WorkspaceSelector (`app/ui/widgets/workspace_selector.py`)

**Línea 384:** `QInputDialog.getText`
- **Título:** "Nuevo Workspace"
- **Prompt:** "Nombre del workspace:"
- **Contexto:** Crear nuevo workspace

**Línea 409:** `QInputDialog.getText`
- **Título:** "Renombrar Workspace"
- **Prompt:** "Nuevo nombre del workspace:"
- **Texto inicial:** Nombre actual del workspace
- **Contexto:** Renombrar workspace existente

### 3.2. FileViewContextMenu (`app/ui/widgets/file_view_context_menu.py`)

**Línea 182:** `QInputDialog.getText`
- **Título:** "Nueva carpeta"
- **Prompt:** "Nombre de la carpeta:"
- **Texto inicial:** "Nueva carpeta"
- **Contexto:** Crear nueva carpeta desde menú contextual de fondo

**Línea 320:** `QInputDialog.getText` (aproximada)
- **Título:** Varía según tipo ("Nuevo documento Word", "Nuevo documento de texto", "Nuevo documento Markdown")
- **Prompt:** Varía según tipo
- **Contexto:** Crear nuevo archivo (docx, txt, md) desde menú contextual

---

## 4. DIÁLOGOS DE ARCHIVOS (QFileDialog)

### 4.1. WorkspaceSelector (`app/ui/widgets/workspace_selector.py`)

**Línea 508:** `QFileDialog.getExistingDirectory`
- **Título:** "Seleccionar Carpeta"
- **Contexto:** Seleccionar carpeta para nuevo Focus
- **Opciones:** `ShowDirsOnly`

---

## 5. MENÚS CONTEXTUALES (QMenu)

### 5.1. WorkspaceSelector (`app/ui/widgets/workspace_selector.py`)

**Línea 348:** `QMenu` - Menú de Workspaces
- **Ubicación:** Botón de workspace
- **Contenido:**
  - Lista de workspaces (checkeable, muestra activo)
  - Separador
  - "+ Nuevo workspace"
  - Separador (si hay workspace activo)
  - "Renombrar workspace…" (si hay workspace activo)
  - "Eliminar workspace…" (si hay workspace activo)

**Línea 551:** `QMenu` - Menú de Estados
- **Ubicación:** Botón de estados (🏷️)
- **Contenido:**
  - Estados disponibles (Pendiente, Entregado, Corregido, Revisar)
  - Separador
  - "Quitar estado"
  - Separador
  - "Renombrar etiqueta…"

### 5.2. FileViewContextMenu (`app/ui/widgets/file_view_context_menu.py`)

**Menú contextual de fondo (espacio vacío):**
- Nueva carpeta
- Pegar (si hay datos en clipboard)
- Separador
- Submenú "Nuevo":
  - Documento Word
  - Documento de texto
  - Documento Markdown

**Menú contextual de archivos/carpetas:**
- Copiar
- Cortar
- Separador
- Mover a la papelera

**Ubicación:** Líneas 52-113 (menú de fondo), 116-165 (menú de items)

### 5.3. FolderTreeSidebar (`app/ui/widgets/folder_tree_sidebar.py`)

**Menú contextual del árbol de carpetas:**
- Crear carpeta
- Renombrar
- Eliminar
- Propiedades

**Ubicación:** Manejo de eventos del árbol de carpetas

### 5.4. SecondaryHeader (`app/ui/widgets/secondary_header.py`)

**Línea 238:** `QMenu` - Menú del botón de configuración
- Menú contextual del botón de settings

**Línea 252:** `QMenu` - Otro menú contextual
- Menú adicional en el header secundario

### 5.5. FolderTreeEventHandler (`app/ui/widgets/folder_tree_event_handler.py`)

**Línea 188:** `QMenu` - Menú contextual del árbol
- Manejo de eventos del árbol de carpetas con menús contextuales

---

## RESUMEN POR TIPO

### Diálogos Personalizados (QDialog): 3
1. BulkRenameDialog
2. TrashDeleteDialog
3. RenameStateDialog

### Mensajes (QMessageBox): ~25 instancias
- MainWindow: 6 mensajes
- WorkspaceSelector: 3 mensajes
- BulkRenameDialog: 1 mensaje
- RenameStateDialog: 2 mensajes
- FileViewContainer: 1 mensaje crítico
- TrashDeleteDialog: 1 mensaje
- FileViewContextMenu: 6 mensajes
- FileBoxUIUtils: 2 mensajes

### Diálogos de Entrada (QInputDialog): 4+
- WorkspaceSelector: 2 (crear y renombrar workspace)
- FileViewContextMenu: 2+ (crear carpeta, crear archivos)

### Diálogos de Archivos (QFileDialog): 1
- WorkspaceSelector: 1 (seleccionar carpeta para Focus)

### Menús Contextuales (QMenu): ~7+
- WorkspaceSelector: 2 menús (workspaces y estados)
- FileViewContextMenu: 2 menús (fondo y items) + 1 submenú "Nuevo"
- FolderTreeSidebar: 1 menú (árbol de carpetas)
- SecondaryHeader: 2 menús (configuración y otros)
- FolderTreeEventHandler: 1 menú (eventos del árbol)

---

## NOTAS

- Todos los diálogos personalizados heredan de `QDialog` y son modales
- Los `QMessageBox` se usan principalmente para errores y advertencias
- Los `QInputDialog` se usan para entrada simple de texto
- Los `QFileDialog` se usan para selección de carpetas/archivos
- Los `QMenu` se muestran contextualmente al hacer clic derecho o en botones específicos

