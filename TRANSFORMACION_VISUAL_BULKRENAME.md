# Transformación Visual EXACTA - BulkRenameDialog

## Objetivo Visual
**Debe sentirse como:** "Un File Box elevado que aparece encima de la app"  
**NO como:** Formulario de Windows o diálogo genérico de Qt

---

## Estructura Visual Transformada

### 1️⃣ VENTANA (Contenedor Externo - QDialog)

**Aspecto Visual:**
- **Fondo:** `#1A1D22` (mismo que AppHeader/Sidebar)
- **Radio de borde:** `12px` (redondeo completo de la ventana)
- **Borde:** `1px solid #2A2E36` (borde sutil oscuro)
- **Margen interno:** `0px` (ningún padding/margin en el QDialog)
- **Sombra:** Opcional pero recomendada para efecto "elevado" (sutil, negra con opacidad baja)

**Resultado:** La ventana se ve como un contenedor oscuro con bordes redondeados, similar a File Box Panel pero flotante.

---

### 2️⃣ PANEL INTERNO ELEVADO (Clave del Diseño)

**Nuevo Widget Contenedor:**
- **Tipo:** QWidget interno que encapsula TODO el contenido actual
- **Fondo:** `#202326` (CENTRAL_AREA_BG - mismo que MainWindow)
- **Radio:** `10px` o `12px` (ligeramente menor que el contenedor externo para efecto de profundidad)
- **Padding:** `20px` todos los lados (espaciado interno generoso)
- **Spacing vertical:** `12px-16px` entre elementos (layout spacing)

**Posicionamiento:**
- Debe tener un pequeño margen interno respecto al contenedor externo (ej: `4px-6px`)
- Esto crea el efecto visual de "panel elevado dentro de contenedor"

**Resultado:** Todo el contenido (inputs, preview, botones) vive dentro de este panel oscuro con fondo `#202326`, creando la sensación de profundidad y elevación.

---

### 3️⃣ HEADER DEL DIÁLOGO (Nueva Sección)

**Estructura:**
- **Widget separado** encima del panel interno elevado
- **Altura fija:** `48px` (igual que AppHeader/SecondaryHeader)
- **Fondo:** `#1A1D22` (mismo que contenedor externo)
- **Borde inferior:** `1px solid #2A2E36` (separación sutil)
- **Padding horizontal:** `20px` (alineado con panel interno)
- **Padding vertical:** `0px` (altura fija)

**Título:**
- **Texto:** "Renombrar archivo" o "Renombrar X archivos"
- **Tamaño:** `15px` o `16px`
- **Peso:** `600` (semi-bold)
- **Color:** `#E6E6E6` (texto claro sobre fondo oscuro)
- **Alineación:** Izquierda, verticalmente centrado

**Elementos NO incluidos:**
- ❌ Sin iconos grandes
- ❌ Sin colores claros
- ❌ Sin botones de cerrar/minimizar (usa los nativos del sistema o ninguno)

**Resultado:** Header oscuro minimalista que separa visualmente el título del contenido, igual que File Box Header.

---

### 4️⃣ INPUTS (Todos los QLineEdit y QComboBox)

**Transformación de cada input:**

#### QLineEdit (Patrón, Buscar, Reemplazar)
- **Fondo:** `#1A1E25` (FILE_BOX_LIST_BG - mismo que File Box List)
- **Texto:** `#E6E6E6` (FILE_BOX_TEXT - texto claro)
- **Placeholder:** `#9AA0A6` (TEXT_SECONDARY - gris medio)
- **Borde:** `1px solid #2A2E36` (FILE_BOX_BORDER - borde oscuro)
- **Radio:** `6px` (redondeo moderado)
- **Padding:** `8px` (interno del input)
- **Focus:** Borde cambia a `#007AFF` (azul iOS, mismo que File Box botón primario)

#### QComboBox (Plantilla)
- **Mismos estilos que QLineEdit:**
  - Fondo: `#1A1E25`
  - Texto: `#E6E6E6`
  - Borde: `1px solid #2A2E36`
  - Radio: `6px`
  - Padding: `8px`
- **Dropdown (QAbstractItemView):**
  - Fondo: `#1A1E25`
  - Borde: `1px solid #2A2E36`
  - Radio: `6px`
  - Items hover: `#252A31` (FILE_BOX_HOVER_BG)
  - Texto items: `#E6E6E6`

**Colores PROHIBIDOS:**
- ❌ `#ffffff` (blanco)
- ❌ `#f5f5f5` (gris claro)
- ❌ `#0078d4` (azul Windows - solo para focus)

**Resultado:** Todos los inputs tienen el mismo aspecto oscuro que File Box List, creando consistencia visual.

---

### 5️⃣ LISTA PREVIEW (Punto Crítico)

**QListWidget (_preview_list):**

**Contenedor:**
- **Fondo:** `#1A1E25` (FILE_BOX_LIST_BG - mismo que File Box List)
- **Borde:** `1px solid #2A2E36` (FILE_BOX_BORDER)
- **Radio:** `8px` (mismo que File Box List)
- **Padding:** `4px` (interno de la lista)

**Items (QListWidgetItem):**
- **Texto principal:** `#E6E6E6` (FILE_BOX_TEXT - texto claro)
- **Texto secundario (flecha "→"):** `#9AA0A6` (TEXT_SECONDARY - gris medio)
- **Padding:** `6px 8px` (vertical horizontal)
- **Altura:** `32px` (mismo que File Box List items)
- **Hover:** Fondo `#252A31` (FILE_BOX_HOVER_BG)
- **Selección:** Mismo fondo que hover (`#252A31`)

**Scrollbar:**
- Usar los mismos estilos que File Box List
- Handle: `rgba(255, 255, 255, 0.15)`
- Handle hover: `rgba(255, 255, 255, 0.25)`

**Colores PROHIBIDOS:**
- ❌ `#ffffff` (blanco)
- ❌ `#e5e5e7` (gris claro)

**Resultado:** La lista preview se ve idéntica a File Box List, reforzando la sensación de "File Box elevado".

---

### 6️⃣ FOOTER Y BOTONES

**Contenedor de Botones:**
- **Alineación:** Botones alineados a la derecha
- **Spacing:** `8px` entre botones
- **Padding superior:** `16px` (separación del contenido)

**Botón Secundario (Cancelar):**
- **Estilo:** Dark button de la app
- **Fondo:** `#20242A` (BUTTON_BG_DARK)
- **Borde:** `1px solid #343A44` (BUTTON_BORDER_DARK)
- **Texto:** `rgba(255, 255, 255, 0.88)` (texto claro)
- **Radio:** `6px`
- **Padding:** `8px 16px`
- **Hover:**
  - Fondo: `#252A31` (BUTTON_BG_DARK_HOVER)
  - Borde: `#3A404B` (BUTTON_BORDER_DARK_HOVER)

**Botón Primario (Aplicar):**
- **Fondo:** `#007AFF` (FILE_BOX_BUTTON_PRIMARY - azul iOS)
- **Texto:** `white` (blanco puro)
- **Radio:** `6px`
- **Padding:** `8px 16px`
- **Font-weight:** `500` (medio)
- **Hover:**
  - Fondo: `#0056CC` (FILE_BOX_BUTTON_PRIMARY_HOVER)
- **Pressed:**
  - Fondo: `#004499` (FILE_BOX_BUTTON_PRIMARY_PRESSED)

**Orden de Botones (de izquierda a derecha):**
1. Cancelar (secundario)
2. Aplicar (primario)

**Colores PROHIBIDOS:**
- ❌ Gris claro para botones secundarios
- ❌ Estilos de Windows Forms

**Resultado:** Botones con estilo oscuro consistente con la app, botón primario azul iOS destacado.

---

### 7️⃣ ELEMENTOS ADICIONALES

#### Labels (Patrón, Buscar y reemplazar, Formato, Vista previa)
- **Color:** `#E6E6E6` (texto claro)
- **Font-weight:** `600` (semi-bold)
- **Font-size:** Sin especificar explícitamente (usa sistema, típicamente 13-14px)

#### Help Text (texto de ayuda debajo de inputs)
- **Color:** `#9AA0A6` (TEXT_SECONDARY - gris medio)
- **Font-weight:** `400` (normal)

#### Checkboxes (Mayúsculas, Minúsculas, Capitalizar)
- **Estilo:** Usar los mismos estilos que File Box/List View
- **Borde:** `rgba(255, 255, 255, 0.3)` (CHECKBOX_BORDER)
- **Borde hover:** `#80C5FF` (CHECKBOX_BORDER_HOVER)
- **Fondo checked:** `#80C5FF` (CHECKBOX_BG_CHECKED)
- **Fondo checked hover:** `#66B3FF` (CHECKBOX_BG_CHECKED_HOVER)
- **Texto:** `#E6E6E6` (texto claro)

#### Botones de Plantilla (+ Guardar, 🗑 Borrar)
- **+ Guardar:**
  - Mantener estilo actual: `#007AFF` fondo, texto blanco
  - O adaptar a estilo dark button si se prefiere consistencia
  
- **🗑 Borrar:**
  - Cambiar de `#d13438` (rojo Windows) a estilo dark button
  - O mantener rojo pero con fondo oscuro: `#d13438` sobre `#1A1E25`

---

## Comparación Visual: Antes vs Después

### ANTES (Estado Actual)
```
┌─────────────────────────────────────┐
│ [Fondo blanco/claro del sistema]   │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ Plantilla: [Combo] [+][🗑]   │  │
│  │ Patrón: [Input blanco]       │  │
│  │ Ayuda: texto gris            │  │
│  │ Buscar: [Input blanco]       │  │
│  │ Vista previa:                │  │
│  │ ┌─────────────────────────┐  │  │
│  │ │ [Lista blanca]          │  │  │
│  │ └─────────────────────────┘  │  │
│  │ [Cancelar] [Aplicar]          │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```
**Sensación:** Formulario de Windows genérico

### DESPUÉS (Transformado)
```
┌─────────────────────────────────────┐
│ [Fondo #1A1D22 - oscuro]           │
│ ┌───────────────────────────────┐  │
│ │ Renombrar archivo    [48px]  │  │ ← Header oscuro
│ ├───────────────────────────────┤  │
│ │ ┌─────────────────────────┐  │  │
│ │ │ [Panel #202326]         │  │  │ ← Panel elevado
│ │ │                         │  │  │
│ │ │ Plantilla: [Combo oscuro]│  │  │
│ │ │ Patrón: [Input oscuro]   │  │  │
│ │ │ Ayuda: texto gris medio  │  │  │
│ │ │ Buscar: [Input oscuro]   │  │  │
│ │ │ Vista previa:            │  │  │
│ │ │ ┌─────────────────────┐ │  │  │
│ │ │ │ [Lista #1A1E25]     │ │  │  │ ← Lista oscura
│ │ │ │ archivo → nuevo     │ │  │  │
│ │ │ └─────────────────────┘ │  │  │
│ │ │        [Cancelar][Aplicar]│  │  │
│ │ └─────────────────────────┘  │  │
│ └───────────────────────────────┘  │
└─────────────────────────────────────┘
```
**Sensación:** File Box elevado sobre la app

---

## Paleta de Colores Final

### Fondos
- **Contenedor externo:** `#1A1D22`
- **Header:** `#1A1D22`
- **Panel interno:** `#202326`
- **Inputs/Lista:** `#1A1E25`
- **Hover:** `#252A31`

### Texto
- **Principal:** `#E6E6E6`
- **Secundario:** `#9AA0A6`
- **Placeholder:** `#9AA0A6`

### Bordes
- **Principal:** `#2A2E36`
- **Focus:** `#007AFF`

### Botones
- **Primario:** `#007AFF` → `#0056CC` (hover)
- **Secundario:** `#20242A` → `#252A31` (hover)

---

## Checklist de Transformación

- [ ] QDialog: Fondo `#1A1D22`, radio `12px`, borde `#2A2E36`, sin márgenes internos
- [ ] Panel interno: Widget nuevo con fondo `#202326`, radio `10-12px`, padding `20px`
- [ ] Header: Widget nuevo `48px` alto, fondo `#1A1D22`, título `#E6E6E6` tamaño `15-16px` peso `600`
- [ ] Todos los QLineEdit: Fondo `#1A1E25`, texto `#E6E6E6`, borde `#2A2E36`, focus `#007AFF`
- [ ] QComboBox: Mismos estilos que QLineEdit, dropdown oscuro
- [ ] QListWidget preview: Fondo `#1A1E25`, borde `#2A2E36`, items `#E6E6E6`, hover `#252A31`
- [ ] Botones: Cancelar (dark button), Aplicar (azul `#007AFF`), orden correcto
- [ ] Labels: Texto `#E6E6E6`, peso `600`
- [ ] Checkboxes: Estilos oscuros consistentes
- [ ] Sin colores claros (`#ffffff`, `#f5f5f5`) en ningún elemento

---

## Resultado Final Esperado

El BulkRenameDialog debe verse y sentirse como si fuera un **File Box Panel** que se ha elevado y flotado sobre la aplicación principal. Debe mantener la misma paleta oscura, los mismos radios de borde, y la misma sensación de profundidad que File Box Panel.

**No debe parecer:**
- Un formulario de Windows
- Un diálogo genérico de Qt
- Una ventana con tema claro

**Debe parecer:**
- Una extensión natural de la UI oscura de la app
- Un panel flotante con la misma identidad visual que File Box
- Un elemento integrado visualmente con el resto de la aplicación

