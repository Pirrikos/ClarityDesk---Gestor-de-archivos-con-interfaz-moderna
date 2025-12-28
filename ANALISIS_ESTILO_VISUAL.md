# Análisis del Estilo Visual - ClarityDesk Pro

## Objetivo
Extraer el contrato visual implícito de la aplicación para usarlo como base en diálogos y ventanas emergentes.

---

## 1. PALETA DE COLORES DOMINANTE

### Fondos Principales
- **MainWindow (Área Central):** `#202326` (CENTRAL_AREA_BG) - Gris oscuro neutro
- **Sidebar:** `#1A1D22` (SIDEBAR_BG) - Gris más oscuro que el área central
- **AppHeader/SecondaryHeader:** `#1A1D22` (APP_HEADER_BG) - Mismo que sidebar
- **FolderTree Panel:** `#181B1E` (PANEL_BG) - Ligeramente más oscuro que sidebar
- **File Box Panel:** `#14171C` (FILE_BOX_PANEL_BG) - El más oscuro de todos
- **File Box Header:** `#1C2027` (FILE_BOX_HEADER_BG) - Ligeramente más claro que panel
- **File Box List:** `#1A1E25` (FILE_BOX_LIST_BG) - Gris intermedio
- **WindowHeader:** `#F5F5F7` - Gris claro (único elemento claro en la app)

### Fondos Secundarios y Estados
- **Hover (Sidebar):** `#23262D` (HOVER_BG) - Gris ligeramente más claro
- **Selección (Sidebar):** `#23262D` (SELECT_BG) - Mismo que hover
- **File Box Hover:** `#252A31` (FILE_BOX_HOVER_BG) - Gris claro para hover
- **Button Dark Background:** `#20242A` (BUTTON_BG_DARK) - Gris oscuro para botones
- **Button Dark Hover:** `#252A31` (BUTTON_BG_DARK_HOVER) - Más claro en hover
- **Button Light Background:** `rgba(255, 255, 255, 0.12)` - Blanco semitransparente
- **Button Light Hover:** `rgba(255, 255, 255, 0.16)` - Más opaco en hover
- **Button Header Background:** `rgba(255, 255, 255, 0.03)` - Muy sutil
- **Button Header Hover:** `rgba(255, 255, 255, 0.08)` - Más visible en hover

### Texto
- **Texto Principal (Sidebar):** `#E6E6E6` (TEXT_PRIMARY) - Blanco casi puro
- **Texto Secundario (Sidebar):** `#9AA0A6` (TEXT_SECONDARY) - Gris medio
- **Texto Deshabilitado (Sidebar):** `#6B7078` (TEXT_DISABLED) - Gris más oscuro
- **Texto Lista:** `#E8E8E8` (TEXT_LIST) - Blanco casi puro
- **Texto Subfolder:** `#B0B5BA` (TEXT_SUBFOLDER) - Gris claro
- **Texto Botones Light:** `rgba(255, 255, 255, 0.8)` - Blanco semitransparente
- **Texto Botones Header:** `rgba(255, 255, 255, 0.7)` - Blanco más transparente
- **Texto Botones Header Hover:** `rgba(255, 255, 255, 0.9)` - Más opaco en hover
- **Texto Botones Header Disabled:** `rgba(255, 255, 255, 0.35)` - Muy transparente
- **Texto File Box:** `#e6edf3` (FILE_BOX_TEXT) - Blanco azulado claro
- **Texto File Box Botones:** `#888888` (FILE_BOX_BUTTON_TEXT) - Gris medio

### Acentos y Colores Destacados
- **Acento Principal (Menú):** `#9D4EDD` (MENU_ACCENT) - Morado/violeta
- **Acento Borde (Menú):** `#7B2CBF` (MENU_ACCENT_BORDER) - Morado más oscuro
- **Acento Sidebar:** `#4A90E2` (ACCENT_COLOR) - Azul
- **File Box Botón Primario:** `#007AFF` (FILE_BOX_BUTTON_PRIMARY) - Azul iOS
- **File Box Botón Primario Hover:** `#0056CC` (FILE_BOX_BUTTON_PRIMARY_HOVER) - Azul más oscuro
- **File Box Botón Primario Pressed:** `#004499` (FILE_BOX_BUTTON_PRIMARY_PRESSED) - Azul muy oscuro
- **Checkbox Checked:** `#80C5FF` (CHECKBOX_BG_CHECKED) - Azul claro
- **Checkbox Checked Hover:** `#66B3FF` (CHECKBOX_BG_CHECKED_HOVER) - Azul más claro
- **Selección Borde:** `QColor(100, 150, 255)` - Azul suave RGB
- **Selección Fondo:** `QColor(100, 150, 255, 15)` - Azul suave semitransparente

### Bordes y Separadores
- **Borde Principal:** `#2A2E36` (APP_HEADER_BORDER, MENU_BORDER) - Gris oscuro
- **Borde Light:** `rgba(255, 255, 255, 0.16)` (BUTTON_BORDER_LIGHT) - Blanco semitransparente
- **Borde Light Hover:** `rgba(255, 255, 255, 0.22)` - Más opaco en hover
- **Borde Header:** `rgba(255, 255, 255, 0.08)` (BUTTON_BORDER_HEADER) - Muy sutil
- **Borde Header Hover:** `rgba(255, 255, 255, 0.15)` - Más visible
- **Borde Dark:** `#343A44` (BUTTON_BORDER_DARK) - Gris oscuro
- **Borde Dark Hover:** `#3A404B` (BUTTON_BORDER_DARK_HOVER) - Más claro
- **Borde Sidebar:** `rgba(255, 255, 255, 0.09)` (BORDER_COLOR) - Blanco muy transparente
- **Borde File Box:** `#2A2E36` (FILE_BOX_BORDER) - Gris oscuro
- **Borde File Box Izquierdo:** `#2F3440` (FILE_BOX_BORDER_LEFT) - Gris ligeramente más claro
- **Separador Línea:** `rgba(255, 255, 255, 0.15)` (SEPARATOR_LINE_COLOR) - Blanco semitransparente
- **Borde Menú Light:** `rgba(255, 255, 255, 0.1)` (MENU_BORDER_LIGHT) - Muy sutil

### Estados de Archivos (State Badges)
- **Pendiente:** `QColor(255, 220, 120)` - Amarillo tenue
- **Entregado:** `QColor(120, 180, 240)` - Azul tenue
- **Corregido:** `QColor(120, 200, 120)` - Verde tenue
- **Revisar:** `QColor(240, 140, 140)` - Rojo tenue

### Colores de Diálogos Existentes
- **BulkRenameDialog:**
  - Fondo lista preview: `#ffffff` - Blanco puro
  - Borde lista: `#e5e5e7` - Gris muy claro
  - Texto ayuda: `#8e8e93` - Gris medio
  
- **RenameStateDialog:**
  - Título: `#1f1f1f` - Casi negro
  - Warning fondo: `#fff4e5` - Beige claro
  - Warning texto: `#d13438` - Rojo
  - Input fondo: `#f5f5f5` - Gris muy claro
  - Input borde: `#d1d1d1` - Gris claro
  - Input focus: `#0078d4` - Azul Windows
  - Botón primario: `#0078d4` - Azul Windows
  - Botón primario hover: `#106ebe` - Azul más oscuro

---

## 2. TIPOGRAFÍA

### Familia de Fuentes
- **Sidebar (FolderTree):** `"Inter", "SF Pro Display", "Segoe UI", -apple-system, system-ui`
  - Prioridad: Inter → SF Pro Display → Segoe UI → Sistema
  - Estilo moderno, sans-serif
  
- **Lista (FileListView):** `'Segoe UI', sans-serif`
  - Fuente nativa de Windows
  
- **Diálogos:** Mayormente `'Segoe UI', sans-serif` o sin especificar (usa sistema)

### Tamaños de Fuente
- **Base (Sidebar):** `13px` (FONT_SIZE_BASE)
- **L1 (Sidebar):** `14px` (FONT_SIZE_L1)
- **Botones Workspace:** `12px`
- **Botones Header:** `14px`
- **Títulos Diálogos:** `16px` (RenameStateDialog)
- **Texto Normal Diálogos:** `13px` (RenameStateDialog)
- **Labels Diálogos:** Sin tamaño explícito, usa sistema (comentario: `/* font-size: establecido explícitamente */`)

### Pesos de Fuente
- **Normal:** `400` (font-weight: 400)
- **Medio:** `500` (font-weight: 500)
- **Semi-bold:** `600` (font-weight: 600)
- **Bold:** `700` (font-weight: bold)

### Espaciado de Letras
- **Sidebar:** `letter-spacing: -0.2px` - Ligera compresión para mejor legibilidad

---

## 3. BORDES Y RADIOS

### Radios de Borde (Border Radius)
- **Botones Workspace/State:** `6px` - Redondeo moderado
- **Botones Header:** `6px` - Consistente con otros botones
- **Menús:** `8px` (workspace menu), `6px` (state menu) - Redondeo suave
- **File Box Panel:** `12px` - Redondeo más pronunciado
- **File Box Header:** `12px` (top-left, top-right) - Consistente con panel
- **File Box List:** `8px` - Redondeo moderado
- **Headers List View:** `8px` - Redondeo moderado
- **Inputs Diálogos:** `4px` (RenameStateDialog) - Redondeo mínimo
- **ComboBox Diálogos:** `4px` - Redondeo mínimo
- **Warning Box Diálogos:** `4px` - Redondeo mínimo
- **Botones Diálogos:** `6px` (RenameStateDialog) - Redondeo moderado
- **Preview List (BulkRename):** `8px` - Redondeo moderado

### Grosor de Bordes
- **Bordes Principales:** `1px` - Estándar
- **Bordes File Box Izquierdo:** `2px` - Más grueso para destacar
- **Separadores:** `1px` - Estándar

### Estilos de Borde
- Mayormente `solid` - Líneas continuas
- Algunos usan `rgba()` para transparencia

---

## 4. ESPACIADOS Y MÁRGENES

### Márgenes de Layout
- **MainWindow:** Sin márgenes explícitos en paintEvent
- **AppHeader:** `16px` horizontal, `6px` vertical (contentsMargins)
- **SecondaryHeader:** Similar a AppHeader
- **WorkspaceSelector:** `12px` izquierdo (LAYOUT_LEFT_MARGIN)
- **Diálogos:** `20px` todos los lados (BulkRenameDialog, RenameStateDialog)
- **File Box Panel:** Sin márgenes explícitos en panel principal

### Espaciado Entre Elementos (Spacing)
- **AppHeader Layout:** `16px` - Espaciado generoso
- **WorkspaceSelector Layout:** `6px` (LAYOUT_SPACING) - Compacto
- **BulkRenameDialog Layout:** `12px` - Moderado
- **RenameStateDialog Layout:** `16px` - Generoso
- **Search Replace Layout:** `8px` - Compacto
- **Format Options Layout:** `16px` - Generoso

### Padding Interno
- **Botones Workspace:** `6px 14px` (vertical horizontal)
- **Botones Header:** `4px 8px` (AppHeader close button)
- **Botones State:** `0px` (sin padding vertical)
- **Menú Items:** `6px 12px` (workspace menu), `6px 20px` (state menu)
- **Inputs Diálogos:** `8px` (RenameStateDialog)
- **ComboBox Diálogos:** `8px`
- **Preview List Items:** `6px`
- **File Box List Items:** `6px 8px`
- **Tree Items:** `4px 0px` vertical, `24px` horizontal (ITEM_H_PADDING)

### Alturas Fijas
- **AppHeader:** `48px`
- **SecondaryHeader:** `48px`
- **WindowHeader:** `40px`
- **WorkspaceSelector:** `52px` (WORKSPACE_HEADER_HEIGHT)
- **Workspace Button:** `28px` (WORKSPACE_BUTTON_HEIGHT)
- **Tree Items:** `30px` (ITEM_HEIGHT)
- **File Box List Items:** `32px`
- **Botones Header:** `28px` (tamaño fijo)

### Espaciado Vertical (V-Spacing)
- **Tree Items:** `12px` (ITEM_V_SPACING) - Entre elementos del árbol

---

## 5. JERARQUÍA VISUAL

### Elementos que Destacan
1. **Botones Primarios (File Box):** `#007AFF` - Azul brillante, máximo contraste
2. **Acentos de Menú:** `#9D4EDD` - Morado vibrante para indicadores checked
3. **State Badges:** Colores saturados (amarillo, azul, verde, rojo) sobre fondos oscuros
4. **Botones Activos (View Toggle):** `rgba(255, 255, 255, 0.2)` - Fondo más visible
5. **File Box Panel:** Borde izquierdo `2px` más grueso - Destaca del contenido principal

### Elementos Secundarios
1. **Botones Header:** Fondo muy sutil (`rgba(255, 255, 255, 0.03)`) - Solo visible en hover
2. **Texto Secundario:** `rgba(255, 255, 255, 0.7)` - Menos contraste que primario
3. **Bordes:** Mayormente sutiles con transparencia
4. **Separadores:** `rgba(255, 255, 255, 0.15)` - Muy sutiles

### Elementos Terciarios/Deshabilitados
1. **Texto Deshabilitado:** `rgba(255, 255, 255, 0.35)` - Muy bajo contraste
2. **Botones Deshabilitados:** Mismo estilo que normal pero con texto deshabilitado

### Por Qué Destacan
- **Contraste:** Los elementos primarios usan colores saturados sobre fondos oscuros
- **Tamaño:** Los botones primarios tienen padding generoso (`8px 16px`)
- **Color:** Azul iOS (`#007AFF`) es reconocible como acción principal
- **Bordes:** El File Box Panel usa borde más grueso (`2px`) para separación visual
- **Opacidad:** Los elementos activos aumentan opacidad de fondo (`0.2` vs `0.03`)

---

## 6. PATRONES REPETIDOS

### Headers
**AppHeader y SecondaryHeader:**
- Fondo: `#1A1D22`
- Borde inferior: `1px solid #2A2E36`
- Altura fija: `48px`
- Márgenes: `16px` horizontal, `6px` vertical
- Espaciado: `16px` entre elementos

**WindowHeader:**
- Fondo: `#F5F5F7` (único elemento claro)
- Borde inferior: `1px solid rgba(0, 0, 0, 0.1)`
- Altura fija: `40px`
- Márgenes: `12px` horizontal, `0px` vertical

### Panels
**File Box Panel:**
- Fondo: `#14171C` (más oscuro)
- Borde izquierdo: `2px solid #2F3440`
- Radio: `12px`
- Header separado con fondo `#1C2027`
- Lista con fondo `#1A1E25` y radio `8px`

**Sidebar (FolderTree):**
- Fondo: `#181B1E`
- Transparente en contenedor
- Sin bordes visibles
- Items con altura `30px`

### Controles (Botones, Inputs, Menús)

**Botones Light (WorkspaceSelector):**
- Fondo: `rgba(255, 255, 255, 0.12)`
- Borde: `rgba(255, 255, 255, 0.16)`
- Radio: `6px`
- Padding: `6px 14px`
- Hover: Aumenta opacidad fondo y borde

**Botones Header:**
- Fondo: `rgba(255, 255, 255, 0.03)` - Muy sutil
- Borde: `rgba(255, 255, 255, 0.08)`
- Radio: `6px`
- Tamaño: `28x28px` fijo
- Hover: Aumenta opacidad significativamente

**Botones Dark:**
- Fondo: `#20242A`
- Borde: `#343A44`
- Radio: `6px`
- Hover: Colores más claros

**Menús:**
- Fondo: `#1A1D22` (MENU_BG) o `rgba(26, 29, 34, 0.95)` (MENU_BG_ALPHA)
- Borde: `#2A2E36` o `rgba(255, 255, 255, 0.1)`
- Radio: `8px` (workspace), `6px` (state)
- Padding: `8px` (workspace), `4px` (state)
- Items: `6px 12px` (workspace), `6px 20px` (state)
- Hover: `#20242A` (MENU_HOVER_BG) o `rgba(255, 255, 255, 0.1)`

**Inputs (Diálogos):**
- Fondo: `white` o `#f5f5f5`
- Borde: `#d1d1d1`
- Radio: `4px`
- Padding: `8px`
- Focus: Borde `#0078d4` (azul Windows)

**ComboBox (Diálogos):**
- Similar a inputs
- Fondo: `#f5f5f5`
- Borde: `#d1d1d1`
- Radio: `4px`
- Padding: `8px`
- Hover/Focus: Borde `#0078d4`

### Listas y Tablas

**File Box List:**
- Fondo: `#1A1E25`
- Borde: `1px solid #2A2E36`
- Radio: `8px`
- Padding: `4px`
- Items: `6px 8px`, altura `32px`
- Hover: `#252A31`

**Preview List (BulkRenameDialog):**
- Fondo: `#ffffff`
- Borde: `1px solid #e5e5e7`
- Radio: `8px`
- Padding: `4px`
- Items: `6px` padding

**List View (FileListView):**
- Fondo: `#202326` (CENTRAL_AREA_BG)
- Sin bordes visibles
- Headers: Fondo `#1A1D22`, radio `8px`, padding `6px 10px`
- Items: Sin padding vertical, `4px 20px` horizontal

### Scrollbars
- Ancho: `8px` (vertical)
- Handle: `rgba(255, 255, 255, 0.15)`
- Handle Hover: `rgba(255, 255, 255, 0.25)`
- Handle Pressed: `rgba(255, 255, 255, 0.30)`
- Radio: `4px`
- Min altura: `30px`

---

## 7. OBSERVACIONES ESPECIALES

### Consistencia de Tema
- La aplicación usa un **tema oscuro** consistente con fondos grises oscuros (`#1A1D22` a `#202326`)
- El único elemento claro es **WindowHeader** (`#F5F5F7`), posiblemente para diferenciación visual
- Los diálogos existentes (BulkRenameDialog, RenameStateDialog) usan **fondos claros** (`#ffffff`, `#f5f5f5`), creando contraste con la ventana principal

### Uso de Transparencia
- Extensivo uso de `rgba()` para fondos y bordes semitransparentes
- Permite efectos de hover sutiles aumentando opacidad
- Crea profundidad visual sin colores sólidos

### Patrón de Hover
- Consistente: aumentar opacidad de fondo y borde en hover
- Ejemplo: `rgba(255, 255, 255, 0.03)` → `rgba(255, 255, 255, 0.08)`
- Algunos elementos cambian color completamente (botones primarios)

### Radios Consistentes
- `6px` para botones y controles pequeños
- `8px` para menús y listas
- `12px` para paneles grandes (File Box)
- `4px` para inputs en diálogos (más conservador)

### Espaciado Generoso
- Márgenes de `16px-20px` en diálogos
- Spacing de `12px-16px` entre secciones
- Padding de `6px-8px` en controles

### Tipografía Moderna
- Preferencia por fuentes del sistema (Segoe UI, SF Pro Display)
- Tamaños base `13px-14px` para legibilidad
- Pesos `400-600` para jerarquía sutil

---

## RESUMEN PARA DIÁLOGOS

### Contrato Visual Implícito

**Fondos:**
- Diálogos: Fondos claros (`#ffffff` o `#f5f5f5`) para contraste con ventana oscura
- O alternativamente: Fondos oscuros (`#1A1D22`) para consistencia con app

**Bordes:**
- Radio: `6px-8px` para diálogos, `4px` para inputs
- Grosor: `1px` estándar
- Color: `#d1d1d1` para inputs claros, `#2A2E36` para fondos oscuros

**Espaciado:**
- Márgenes: `20px` todos los lados
- Spacing: `12px-16px` entre elementos
- Padding inputs: `8px`

**Tipografía:**
- Familia: `'Segoe UI', sans-serif` o sistema
- Tamaño base: `13px-14px`
- Títulos: `16px`, peso `600`
- Labels: Peso `500-600`

**Colores:**
- Texto principal: `#1f1f1f` (claro) o `#E6E6E6` (oscuro)
- Texto secundario: `#8e8e93` (claro) o `#9AA0A6` (oscuro)
- Acentos: `#0078d4` (azul Windows) o `#007AFF` (azul iOS)
- Botones primarios: `#0078d4` con hover `#106ebe`

**Botones:**
- Radio: `6px`
- Padding: `8px 16px` (primarios), `6px 12px` (secundarios)
- Primarios: Fondo azul, texto blanco
- Secundarios: Fondo transparente/gris, borde sutil

Este análisis describe objetivamente el estilo visual actual sin proponer cambios.

