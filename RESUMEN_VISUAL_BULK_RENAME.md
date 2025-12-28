# Contrato Visual Oficial - Diálogos de ClarityDesk Pro

> **Este documento define el contrato visual oficial para todos los diálogos de ClarityDesk Pro.**
> 
> **Cualquier ventana emergente (QDialog, QMessageBox custom, input dialogs) debe adherirse a estas reglas visuales para garantizar coherencia con la MainWindow y los File Box Panels.**

## Principios Fundamentales

1. **Transparencia Total**: El QDialog base debe ser completamente transparente
2. **Frameless**: Sin barra de título ni controles del sistema operativo
3. **Panel Elevado**: Contenedor único con fondo y bordes redondeados
4. **Coherencia Visual**: Mismos colores, radios y espaciados que File Box Panels
5. **Header Personalizado**: Header arrastrable con botón cerrar propio

---

# Reglas Generales para Todos los Diálogos

## Estructura Obligatoria

Todos los diálogos deben seguir esta estructura base:

```
QDialog (Frameless, Transparent)
└── Contenedor Principal (con fondo y bordes redondeados)
    ├── Header (arrastrable, con título y botón cerrar)
    └── Panel de Contenido (con el contenido específico)
```

## Configuración de Ventana (Obligatorio)

```python
# Window Flags
self.setWindowFlags(
    Qt.WindowType.Dialog |
    Qt.WindowType.FramelessWindowHint
)

# Atributos de transparencia
self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

# Estilo del QDialog - completamente transparente
self.setStyleSheet("""
    QDialog {
        background-color: transparent;
    }
""")
```

## Contenedor Principal (Obligatorio)

```python
main_container = QWidget()
main_container.setStyleSheet(f"""
    QWidget {{
        background-color: {APP_HEADER_BG};  /* #1A1D22 */
        border: 1px solid {APP_HEADER_BORDER};  /* #2A2E36 */
        border-radius: 12px;
    }}
""")
```

## Header (Obligatorio)

```python
header_widget = QWidget()
header_widget.setFixedHeight(48)
header_widget.setStyleSheet(f"""
    QWidget {{
        background-color: transparent;
        border-bottom: 1px solid {APP_HEADER_BORDER};
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
    }}
""")

# Título
title_label = QLabel("Título del Diálogo")
title_label.setStyleSheet(f"""
    QLabel {{
        font-size: 15px;
        font-weight: 600;
        color: {FILE_BOX_TEXT};
        background-color: transparent;
        border: none;
        padding: 0;
        margin: 0;
    }}
""")

# Botón cerrar
close_button = QPushButton("✕")
close_button.setFixedSize(32, 28)
close_button.setStyleSheet(f"""
    QPushButton {{
        background-color: transparent;
        border: none;
        border-radius: 6px;
        color: {FILE_BOX_TEXT};
        font-size: 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: rgba(255, 255, 255, 0.1);
    }}
    QPushButton:pressed {{
        background-color: rgba(255, 255, 255, 0.15);
    }}
""")
```

## Panel de Contenido (Obligatorio)

```python
content_panel = QWidget()
content_panel.setStyleSheet(f"""
    QWidget {{
        background-color: {CENTRAL_AREA_BG};  /* #202326 */
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
    }}
""")

content_layout = QVBoxLayout(content_panel)
content_layout.setContentsMargins(20, 20, 20, 20)
content_layout.setSpacing(16)
```

## Centrado en Pantalla (Obligatorio)

```python
def showEvent(self, event: QEvent) -> None:
    """Center dialog on screen when shown."""
    super().showEvent(event)
    screen = self.screen()
    if not screen:
        screen = QApplication.primaryScreen()
    
    if screen:
        screen_geometry = screen.availableGeometry()
        dialog_geometry = self.frameGeometry()
        self.move(
            screen_geometry.left() + (screen_geometry.width() - dialog_geometry.width()) // 2,
            screen_geometry.top() + (screen_geometry.height() - dialog_geometry.height()) // 2
        )
```

## Paleta de Colores (Obligatorio)

### Fondos
- **QDialog**: `transparent`
- **Contenedor Principal**: `#1A1D22` (APP_HEADER_BG)
- **Panel de Contenido**: `#202326` (CENTRAL_AREA_BG)
- **Inputs/Combos**: `#1A1E25` (FILE_BOX_LIST_BG)
- **Hover**: `#252A31` (FILE_BOX_HOVER_BG)

### Bordes
- **Principal**: `#2A2E36` (APP_HEADER_BORDER, FILE_BOX_BORDER)
- **Focus**: `#007AFF` (FILE_BOX_BUTTON_PRIMARY)

### Texto
- **Principal**: `#e6edf3` (FILE_BOX_TEXT)
- **Secundario**: `#9AA0A6`

### Botones
- **Primario**: `#007AFF` (FILE_BOX_BUTTON_PRIMARY)
- **Secundario**: Estilo dark button

## Radios y Espaciados (Obligatorio)

- **Bordes redondeados del contenedor**: `12px`
- **Bordes redondeados de inputs**: `6px`
- **Bordes redondeados de tablas**: `8px`
- **Padding del panel de contenido**: `20px`
- **Spacing vertical**: `16px`
- **Altura del header**: `48px`

## Componentes Estándar

### Inputs (QLineEdit, QTextEdit)
```python
stylesheet = f"""
    QLineEdit {{
        background-color: {FILE_BOX_LIST_BG};
        color: {FILE_BOX_TEXT};
        border: 1px solid {FILE_BOX_BORDER};
        border-radius: 6px;
        padding: 8px;
    }}
    QLineEdit:focus {{
        border-color: {FILE_BOX_BUTTON_PRIMARY};
    }}
    QLineEdit::placeholder {{
        color: #9AA0A6;
    }}
"""
```

### Combos (QComboBox)
```python
stylesheet = f"""
    QComboBox {{
        background-color: {FILE_BOX_LIST_BG};
        color: {FILE_BOX_TEXT};
        border: 1px solid {FILE_BOX_BORDER};
        border-radius: 6px;
        padding: 8px;
    }}
    QComboBox:hover {{
        border-color: {FILE_BOX_BUTTON_PRIMARY};
    }}
    QComboBox:focus {{
        border-color: {FILE_BOX_BUTTON_PRIMARY};
    }}
"""
```

### Botones Primarios
```python
stylesheet = f"""
    QPushButton {{
        background-color: {FILE_BOX_BUTTON_PRIMARY};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {FILE_BOX_BUTTON_PRIMARY_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {FILE_BOX_BUTTON_PRIMARY_PRESSED};
    }}
"""
```

### Botones Secundarios
```python
stylesheet = f"""
    QPushButton {{
        background-color: {BUTTON_BG_DARK};
        border: 1px solid {BUTTON_BORDER_DARK};
        border-radius: 6px;
        color: rgba(255, 255, 255, 0.88);
        padding: 8px 16px;
    }}
    QPushButton:hover {{
        background-color: {BUTTON_BG_DARK_HOVER};
        border-color: {BUTTON_BORDER_DARK_HOVER};
    }}
"""
```

## Checklist de Implementación

Al crear un nuevo diálogo, verificar:

- [ ] QDialog es frameless y transparente
- [ ] Contenedor principal tiene fondo #1A1D22 y borde #2A2E36
- [ ] Radio de 12px en todas las esquinas del contenedor
- [ ] Header de 48px con título y botón cerrar
- [ ] Panel de contenido con fondo #202326
- [ ] Padding de 20px en el panel de contenido
- [ ] Spacing de 16px entre elementos
- [ ] Inputs con estilo oscuro consistente
- [ ] Botones con estilos primario/secundario correctos
- [ ] Centrado automático en pantalla
- [ ] Header arrastrable funcional
- [ ] Sin artefactos negros ni fondos visibles fuera del contenedor

---

# Ejemplo de Implementación Completa: Ventana de Renombrado (BulkRenameDialog)

## Estructura General

```
┌─────────────────────────────────────────────────────────────────┐
│ QDialog (Frameless, Transparent)                                │
│ Tamaño mínimo: 900x600px                                         │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Contenedor Principal (main_container)                        │ │
│ │ Fondo: #1A1D22 (APP_HEADER_BG)                             │ │
│ │ Borde: 1px solid #2A2E36 (APP_HEADER_BORDER)                │ │
│ │ Radio: 12px (todas las esquinas)                            │ │
│ │                                                               │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ HEADER (48px altura)                                     │ │ │
│ │ │ Fondo: transparent (hereda del contenedor)              │ │ │
│ │ │ Borde inferior: 1px solid #2A2E36                        │ │ │
│ │ │ Radio superior: 12px                                     │ │ │
│ │ │                                                           │ │ │
│ │ │ [Título: "Renombrar archivo" / "Renombrar X archivos"]  │ │ │
│ │ │                    [Botón ✕]                             │ │ │
│ │ │                                                           │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                               │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ PANEL DE CONTENIDO (content_panel)                      │ │ │
│ │ │ Fondo: #202326 (CENTRAL_AREA_BG)                        │ │ │
│ │ │ Radio inferior: 12px                                    │ │ │
│ │ │ Padding: 20px                                           │ │ │
│ │ │ Spacing: 16px                                           │ │ │
│ │ │                                                           │ │ │
│ │ │ ┌─────────────────────────────────────────────────────┐ │ │ │
│ │ │ │ BARRA DE PLANTILLAS (templates_bar)                 │ │ │ │
│ │ │ │ Ocupa todo el ancho                                  │ │ │ │
│ │ │ └─────────────────────────────────────────────────────┘ │ │ │
│ │ │                                                           │ │ │
│ │ │ ┌───────────────────────┬─────────────────────────────┐ │ │ │
│ │ │ │ COLUMNA IZQUIERDA     │ COLUMNA DERECHA            │ │ │ │
│ │ │ │                       │                             │ │ │ │
│ │ │ │ • Selector de modo    │ • Posición del número       │ │ │ │
│ │ │ │   (Radio buttons)     │   (Radio buttons)           │ │ │ │
│ │ │ │   - Nuevo             │   - Al principio           │ │ │ │
│ │ │ │   - Modificar         │   - Al final               │ │ │ │
│ │ │ │   existente           │                             │ │ │ │
│ │ │ │                       │ • Buscar y reemplazar      │ │ │ │
│ │ │ │ • Label "Patrón:"     │   - Campo "Buscar:"        │ │ │ │
│ │ │ │                       │   - Campo "Reemplazar:"     │ │ │ │
│ │ │ │ • Label nombre actual │                             │ │ │ │
│ │ │ │   (si modificar)      │ • Opciones de formato      │ │ │ │
│ │ │ │                       │   - Mayúsculas             │ │ │ │
│ │ │ │ • Campo Patrón        │   - Minúsculas             │ │ │ │
│ │ │ │   (QLineEdit)         │   - Título                 │ │ │ │
│ │ │ │                       │                             │ │ │ │
│ │ │ │ • Texto de ayuda      │                             │ │ │ │
│ │ │ │                       │                             │ │ │ │
│ │ │ └───────────────────────┴─────────────────────────────┘ │ │ │
│ │ │                                                           │ │ │
│ │ │ ┌─────────────────────────────────────────────────────┐ │ │ │
│ │ │ │ VISTA PREVIA                                        │ │ │ │
│ │ │ │                                                     │ │ │ │
│ │ │ │ Label "Vista previa:"                               │ │ │ │
│ │ │ │                                                     │ │ │ │
│ │ │ │ ┌───────────────────────────────────────────────┐ │ │ │ │
│ │ │ │ │ Tabla (QTableWidget)                          │ │ │ │ │
│ │ │ │ │ Borde: 1px solid #2A2E36                      │ │ │ │ │
│ │ │ │ │ Radio: 8px                                     │ │ │ │ │
│ │ │ │ │ Fondo: #1A1E25 (FILE_BOX_LIST_BG)            │ │ │ │ │
│ │ │ │ │                                                 │ │ │ │ │
│ │ │ │ │ ┌──────────────┬─────────────────────────────┐ │ │ │ │ │
│ │ │ │ │ │ antes        │ después                     │ │ │ │ │
│ │ │ │ │ │ (header 28px)│ (header 28px)               │ │ │ │ │
│ │ │ │ │ ├──────────────┼─────────────────────────────┤ │ │ │ │ │
│ │ │ │ │ │ archivo1.txt │ archivo1_2024-01-15.txt     │ │ │ │ │
│ │ │ │ │ │ archivo2.txt │ archivo2_2024-01-15.txt     │ │ │ │ │
│ │ │ │ │ │ archivo3.txt │ archivo3_2024-01-15.txt     │ │ │ │ │
│ │ │ │ │ │ ...          │ ...                         │ │ │ │ │
│ │ │ │ │ └──────────────┴─────────────────────────────┘ │ │ │ │ │
│ │ │ │ └───────────────────────────────────────────────┘ │ │ │ │
│ │ │ └─────────────────────────────────────────────────────┘ │ │ │
│ │ │                                                           │ │ │
│ │ │ ┌─────────────────────────────────────────────────────┐ │ │ │
│ │ │ │ FOOTER - BOTONES                                    │ │ │ │
│ │ │ │                                                     │ │ │ │
│ │ │ │                    [Cancelar]  [Aplicar]            │ │ │ │
│ │ │ │                                                     │ │ │ │
│ │ │ └─────────────────────────────────────────────────────┘ │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Paleta de Colores

### Fondos
- **QDialog**: `transparent` (completamente transparente)
- **Contenedor Principal**: `#1A1D22` (APP_HEADER_BG)
- **Panel de Contenido**: `#202326` (CENTRAL_AREA_BG)
- **Inputs/Combos**: `#1A1E25` (FILE_BOX_LIST_BG)
- **Tabla Preview**: `#1A1E25` (FILE_BOX_LIST_BG)
- **Header Tabla**: `#1C2027` (FILE_BOX_HEADER_BG)
- **Hover Items**: `#252A31` (FILE_BOX_HOVER_BG)

### Bordes
- **Contenedor Principal**: `#2A2E36` (APP_HEADER_BORDER)
- **Inputs/Combos**: `#2A2E36` (FILE_BOX_BORDER)
- **Focus Inputs**: `#007AFF` (FILE_BOX_BUTTON_PRIMARY)
- **Separador Columnas**: `#2A2E36` (FILE_BOX_BORDER)

### Texto
- **Principal**: `#e6edf3` (FILE_BOX_TEXT)
- **Secundario/Ayuda**: `#9AA0A6`
- **Placeholder**: `#9AA0A6`

### Botones
- **Cancelar**: 
  - Fondo: `BUTTON_BG_DARK`
  - Borde: `BUTTON_BORDER_DARK`
  - Hover: `BUTTON_BG_DARK_HOVER`
- **Aplicar**:
  - Fondo: `#007AFF` (FILE_BOX_BUTTON_PRIMARY)
  - Hover: `#0056CC` (FILE_BOX_BUTTON_PRIMARY_HOVER)
  - Pressed: `#004499` (FILE_BOX_BUTTON_PRIMARY_PRESSED)

## Componentes Detallados

### 1. Header (48px altura)
```
┌─────────────────────────────────────────────────────────┐
│ Renombrar archivo                    [✕]                │
└─────────────────────────────────────────────────────────┘
```
- **Título**: Font 15px, weight 600, color FILE_BOX_TEXT
- **Botón Cerrar**: 32x28px, transparent con hover
- **Borde inferior**: 1px solid APP_HEADER_BORDER
- **Radio superior**: 12px

### 2. Barra de Plantillas
- Ocupa todo el ancho
- ComboBox con plantillas predefinidas
- Estilo oscuro consistente

### 3. Layout de Dos Columnas

#### Columna Izquierda:
1. **Selector de Modo** (Radio buttons)
   - "Nuevo"
   - "Modificar existente" (predeterminado, solo archivo único)

2. **Label "Patrón:"**
   - Font weight 600
   - Color FILE_BOX_TEXT

3. **Label Nombre Actual** (condicional)
   - Visible solo si "Modificar existente" y archivo único
   - Fondo FILE_BOX_LIST_BG
   - Borde FILE_BOX_BORDER
   - Radio 6px
   - Texto secundario #9AA0A6

4. **Campo Patrón** (QLineEdit)
   - Placeholder: "Ejemplo: {name}_{date}"
   - Fondo FILE_BOX_LIST_BG
   - Borde FILE_BOX_BORDER
   - Radio 6px
   - Padding 8px
   - Focus: borde azul #007AFF

5. **Texto de Ayuda**
   - Color #9AA0A6
   - Explica placeholders disponibles

#### Separador Vertical
- Línea de 1px
- Color FILE_BOX_BORDER
- Entre las dos columnas

#### Columna Derecha:
1. **Posición del Número** (solo múltiples archivos)
   - Radio buttons:
     - "Al principio"
     - "Al final" (predeterminado)

2. **Buscar y Reemplazar**
   - Label "Buscar y reemplazar:"
   - Campo "Buscar:" (QLineEdit)
   - Campo "Reemplazar:" (QLineEdit)
   - Layout horizontal

3. **Opciones de Formato**
   - Checkboxes:
     - Mayúsculas
     - Minúsculas
     - Título
   - Mutuamente excluyentes

### 4. Vista Previa (Tabla)

#### Encabezados:
```
┌──────────────┬─────────────────────────────┐
│ antes        │ después                     │
└──────────────┴─────────────────────────────┘
```
- **Altura**: 28px
- **Fondo**: FILE_BOX_HEADER_BG (#1C2027)
- **Texto**: Font 11px, weight 500, minúsculas
- **Padding**: 4px 8px
- **Borde inferior**: 1px solid FILE_BOX_BORDER
- **Radio superior**: 8px

#### Filas:
- **Padding**: 6px 8px
- **Fondo**: transparent
- **Hover**: FILE_BOX_HOVER_BG (#252A31)
- **Texto**: FILE_BOX_TEXT (#e6edf3)
- **Sin selección ni edición**

### 5. Footer - Botones

```
                    [Cancelar]  [Aplicar]
```

- **Cancelar**:
  - Estilo dark button
  - Fondo BUTTON_BG_DARK
  - Borde BUTTON_BORDER_DARK
  - Radio 6px
  - Padding 8px 16px

- **Aplicar**:
  - Estilo primary button
  - Fondo azul #007AFF
  - Sin borde
  - Radio 6px
  - Padding 8px 16px
  - Font weight 500

## Características Especiales

### Ventana Frameless
- Sin barra de título de Windows
- Sin controles de ventana del sistema
- Header arrastrable personalizado
- Botón cerrar funcional propio
- Centrado automático en pantalla

### Transparencia
- QDialog completamente transparente
- Solo el contenedor principal tiene fondo visible
- Sin artefactos negros en esquinas
- Bordes redondeados limpios

### Responsive
- Tamaño mínimo: 900x600px
- Layout horizontal para opciones (2 columnas)
- Preview ocupa espacio vertical con stretch factor 2
- Columnas de tabla con stretch igual

### Interactividad
- Preview en tiempo real al cambiar patrones
- Validación de nombres antes de aplicar
- Manejo de errores con mensajes claros
- Templates predefinidos guardados

## Flujo Visual

1. **Usuario abre diálogo** → Ventana centrada, frameless
2. **Selecciona modo** → Aparece/desaparece label nombre actual
3. **Escribe patrón** → Preview se actualiza en tiempo real
4. **Ajusta opciones** → Preview refleja cambios inmediatamente
5. **Revisa preview** → Tabla muestra antes/después claramente
6. **Aplica o cancela** → Botones con estilos diferenciados

## Estilos Consistentes

Todos los componentes siguen el estilo "File Box elevated":
- Fondos oscuros (#1A1D22, #202326, #1A1E25)
- Bordes sutiles (#2A2E36)
- Texto claro (#e6edf3)
- Acentos azules (#007AFF)
- Radios consistentes (6px, 8px, 12px)
- Espaciado uniforme (16px, 20px)

---

# Reglas Generales para Todos los Diálogos

## Estructura Obligatoria

Todos los diálogos deben seguir esta estructura base:

```
QDialog (Frameless, Transparent)
└── Contenedor Principal (con fondo y bordes redondeados)
    ├── Header (arrastrable, con título y botón cerrar)
    └── Panel de Contenido (con el contenido específico)
```

## Configuración de Ventana (Obligatorio)

```python
# Window Flags
self.setWindowFlags(
    Qt.WindowType.Dialog |
    Qt.WindowType.FramelessWindowHint
)

# Atributos de transparencia
self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

# Estilo del QDialog - completamente transparente
self.setStyleSheet("""
    QDialog {
        background-color: transparent;
    }
""")
```

## Contenedor Principal (Obligatorio)

```python
main_container = QWidget()
main_container.setStyleSheet(f"""
    QWidget {{
        background-color: {APP_HEADER_BG};  /* #1A1D22 */
        border: 1px solid {APP_HEADER_BORDER};  /* #2A2E36 */
        border-radius: 12px;
    }}
""")
```

## Header (Obligatorio)

```python
header_widget = QWidget()
header_widget.setFixedHeight(48)
header_widget.setStyleSheet(f"""
    QWidget {{
        background-color: transparent;
        border-bottom: 1px solid {APP_HEADER_BORDER};
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
    }}
""")

# Título
title_label = QLabel("Título del Diálogo")
title_label.setStyleSheet(f"""
    QLabel {{
        font-size: 15px;
        font-weight: 600;
        color: {FILE_BOX_TEXT};
        background-color: transparent;
        border: none;
        padding: 0;
        margin: 0;
    }}
""")

# Botón cerrar
close_button = QPushButton("✕")
close_button.setFixedSize(32, 28)
close_button.setStyleSheet(f"""
    QPushButton {{
        background-color: transparent;
        border: none;
        border-radius: 6px;
        color: {FILE_BOX_TEXT};
        font-size: 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: rgba(255, 255, 255, 0.1);
    }}
    QPushButton:pressed {{
        background-color: rgba(255, 255, 255, 0.15);
    }}
""")
```

## Panel de Contenido (Obligatorio)

```python
content_panel = QWidget()
content_panel.setStyleSheet(f"""
    QWidget {{
        background-color: {CENTRAL_AREA_BG};  /* #202326 */
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
    }}
""")

content_layout = QVBoxLayout(content_panel)
content_layout.setContentsMargins(20, 20, 20, 20)
content_layout.setSpacing(16)
```

## Centrado en Pantalla (Obligatorio)

```python
def showEvent(self, event: QEvent) -> None:
    """Center dialog on screen when shown."""
    super().showEvent(event)
    screen = self.screen()
    if not screen:
        screen = QApplication.primaryScreen()
    
    if screen:
        screen_geometry = screen.availableGeometry()
        dialog_geometry = self.frameGeometry()
        self.move(
            screen_geometry.left() + (screen_geometry.width() - dialog_geometry.width()) // 2,
            screen_geometry.top() + (screen_geometry.height() - dialog_geometry.height()) // 2
        )
```

## Paleta de Colores (Obligatorio)

### Fondos
- **QDialog**: `transparent`
- **Contenedor Principal**: `#1A1D22` (APP_HEADER_BG)
- **Panel de Contenido**: `#202326` (CENTRAL_AREA_BG)
- **Inputs/Combos**: `#1A1E25` (FILE_BOX_LIST_BG)
- **Hover**: `#252A31` (FILE_BOX_HOVER_BG)

### Bordes
- **Principal**: `#2A2E36` (APP_HEADER_BORDER, FILE_BOX_BORDER)
- **Focus**: `#007AFF` (FILE_BOX_BUTTON_PRIMARY)

### Texto
- **Principal**: `#e6edf3` (FILE_BOX_TEXT)
- **Secundario**: `#9AA0A6`

### Botones
- **Primario**: `#007AFF` (FILE_BOX_BUTTON_PRIMARY)
- **Secundario**: Estilo dark button

## Radios y Espaciados (Obligatorio)

- **Bordes redondeados del contenedor**: `12px`
- **Bordes redondeados de inputs**: `6px`
- **Bordes redondeados de tablas**: `8px`
- **Padding del panel de contenido**: `20px`
- **Spacing vertical**: `16px`
- **Altura del header**: `48px`

## Componentes Estándar

### Inputs (QLineEdit, QTextEdit)
```python
stylesheet = f"""
    QLineEdit {{
        background-color: {FILE_BOX_LIST_BG};
        color: {FILE_BOX_TEXT};
        border: 1px solid {FILE_BOX_BORDER};
        border-radius: 6px;
        padding: 8px;
    }}
    QLineEdit:focus {{
        border-color: {FILE_BOX_BUTTON_PRIMARY};
    }}
    QLineEdit::placeholder {{
        color: #9AA0A6;
    }}
"""
```

### Combos (QComboBox)
```python
stylesheet = f"""
    QComboBox {{
        background-color: {FILE_BOX_LIST_BG};
        color: {FILE_BOX_TEXT};
        border: 1px solid {FILE_BOX_BORDER};
        border-radius: 6px;
        padding: 8px;
    }}
    QComboBox:hover {{
        border-color: {FILE_BOX_BUTTON_PRIMARY};
    }}
    QComboBox:focus {{
        border-color: {FILE_BOX_BUTTON_PRIMARY};
    }}
"""
```

### Botones Primarios
```python
stylesheet = f"""
    QPushButton {{
        background-color: {FILE_BOX_BUTTON_PRIMARY};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {FILE_BOX_BUTTON_PRIMARY_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {FILE_BOX_BUTTON_PRIMARY_PRESSED};
    }}
"""
```

### Botones Secundarios
```python
stylesheet = f"""
    QPushButton {{
        background-color: {BUTTON_BG_DARK};
        border: 1px solid {BUTTON_BORDER_DARK};
        border-radius: 6px;
        color: rgba(255, 255, 255, 0.88);
        padding: 8px 16px;
    }}
    QPushButton:hover {{
        background-color: {BUTTON_BG_DARK_HOVER};
        border-color: {BUTTON_BORDER_DARK_HOVER};
    }}
"""
```

## Checklist de Implementación

Al crear un nuevo diálogo, verificar:

- [ ] QDialog es frameless y transparente
- [ ] Contenedor principal tiene fondo #1A1D22 y borde #2A2E36
- [ ] Radio de 12px en todas las esquinas del contenedor
- [ ] Header de 48px con título y botón cerrar
- [ ] Panel de contenido con fondo #202326
- [ ] Padding de 20px en el panel de contenido
- [ ] Spacing de 16px entre elementos
- [ ] Inputs con estilo oscuro consistente
- [ ] Botones con estilos primario/secundario correctos
- [ ] Centrado automático en pantalla
- [ ] Header arrastrable funcional
- [ ] Sin artefactos negros ni fondos visibles fuera del contenedor

---

# Ejemplo de Implementación Completa

A continuación se muestra el ejemplo completo del BulkRenameDialog como referencia de implementación correcta:

