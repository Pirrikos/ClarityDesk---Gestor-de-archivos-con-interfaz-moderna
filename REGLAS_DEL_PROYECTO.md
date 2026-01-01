# CLARITYDESK PRO - REGLAS DEL PROYECTO

**Versión:** 2.1
**Tipo:** Permanentes (Arquitectura, Capas, Estilo)
**Fecha:** 2026-01-01

---

## 📋 CONTENIDO

Este documento contiene las reglas **permanentes** del proyecto ClarityDesk Pro:
- Arquitectura de capas
- Patrones de código
- Convenciones de estilo
- Directrices de Qt/PySide6
- Protocolos de testing

Para reglas de **consolidación temporal** → Ver [REGLAS_DE_CONSOLIDACION.md](REGLAS_DE_CONSOLIDACION.md)
Para evolución futura → Ver [REGLAS_DE_REFACTOR.md](REGLAS_DE_REFACTOR.md)

---

## ⚡ QUICK REFERENCE (Más Crítico - Siempre Activo)

### ARCHITECTURE CORE:
- ✅ Separación de capas: `models → services → managers → ui` (Regla 1)
- ✅ Una clase = una descripción de una frase (Regla 2)
- ✅ Cohesión: 1 archivo (400 líneas) > 5 archivos (80 líneas cada uno) (Regla 3)
- ✅ No duplicación de código - centralizar en utils (Regla 4)
- ✅ Siempre inyectar dependencias, nunca hardcodear (Regla 5)

### FORBIDDEN PATTERNS:
- ❌ `*_wrapper.py` sin lógica (Regla 6)
- ❌ Archivos de una sola función (Regla 6)
- ❌ Clases de un solo método (Regla 6)
- ❌ God objects (>15 métodos públicos) (Regla 6)

### Qt CRITICAL:
- ⚡ Signals: a nivel de clase, emit DESPUÉS de actualizar estado (Regla 16)
- ⚡ Managers NUNCA importan QWidget (Regla 17)
- ⚡ Siempre pasar parent a QWidget/QObject (Regla 18)
- ⚡ Operaciones pesadas (>100ms): usar QThread (Regla 20)
- ⚡ Eventos de archivos: debounce 500ms (Regla 21)

### FILE LIMITS:
- 📏 Máx 800 líneas/archivo (límite de coherencia de IA)
- 📏 Dividir solo si: responsabilidad diferente O reutilizado en 3+ lugares
- 📏 Nombres deben ser auto-documentados

### TESTING:
- 🧪 Managers/Services DEBEN tener tests
- 🧪 Mín 3 tests: éxito, error, caso edge
- 🧪 Red flag: necesita >3 mocks → refactorizar clase

---

## 0. PROTOCOLO DE COLABORACIÓN CON IA

### Estrategia de Optimización de Tokens:
- Reglas completas: ~8,000 tokens
- Presupuesto de contexto por tarea: ~20,000 tokens

### Estrategia de carga:
1. Cargar reglas completas UNA VEZ al inicio de sesión
2. Por tarea: citar solo números de regla relevantes
3. Ejemplo: "Modificar sidebar siguiendo reglas 3, 16, 18"

La IA recuerda reglas del contexto de sesión.
No recargar a menos que sea nueva sesión de Cursor.

### Gestión de Ventana de Contexto:
- Máx 800 líneas por archivo (la IA pierde coherencia arriba de esto)
- Proporcionar máx 3-4 archivos por solicitud
- Enunciar objetivo en UNA frase
- Especificar qué NO debe cambiar

### La IA DEBE Siempre (Antes de Codificar):
1. Replantear solicitud: "¿Quieres [X]?"
2. Listar archivos afectados: `file1.py` (modificar), `file2.py` (nuevo)
3. Validar reglas: ✅ Sigue separación de capas, ⚠️ Necesita tests
4. Pedir confirmación: "¿Proceder? (sí/no/modificar)"

### La IA NUNCA DEBE:
- ❌ Cambiar >3 archivos sin preguntar
- ❌ Hacer suposiciones sobre requisitos
- ❌ Ignorar errores y continuar
- ❌ Omitir explicación del POR QUÉ

### En Error - Protocolo de Recuperación:
1. PARAR inmediatamente (no continuar haciendo cambios)
2. Mostrar qué cambió (lista de archivos)
3. Explicar causa raíz + número de línea
4. Proponer: A) Revertir, B) Arreglar hacia adelante, C) Preguntar al humano
5. Obtener confirmación antes de proceder

---

## 1. SEPARACIÓN DE CAPAS (CUMPLIMIENTO ESTRICTO)

### Estructura de Directorios:
```
app/
├── models/      → Datos puros (sin lógica, sin Qt, sin I/O)
├── services/    → Operaciones de negocio (puede usar Qt para I/O)
├── managers/    → Coordinación de alto nivel (orquestar servicios)
└── ui/          → Componentes visuales (windows, widgets)
```

### Reglas de Importación (NUNCA VIOLAR):
- `models/` imports: NADA (solo standard library + typing)
- `services/` imports: solo models
- `managers/` imports: models + services
- `ui/` imports: todo

### Validación:
- Si `services` importa `ui` → INCORRECTO
- Si `models` importa `services` → INCORRECTO
- Si `managers` importa `ui` → INCORRECTO

---

## 2. PRINCIPIO DE RESPONSABILIDAD ÚNICA (SIGNIFICADO REAL)

Cada clase = una descripción de una frase.

### ✅ BUENO:
- "TabManager gestiona la lista de tabs abiertas"
- "FileListService lista archivos de una carpeta"
- "TabStorage persiste estado de tabs en disco"

### ❌ MALO:
- "TabManager gestiona tabs, guarda estado, valida rutas, envía notificaciones, maneja errores"

**Test:** Si no puedes explicar una clase en UNA frase clara → clase hace demasiado → REFACTORIZAR

---

## 3. COHESIÓN SOBRE FRAGMENTACIÓN (EFICIENCIA DE TOKENS)

### Pautas de Tamaño de Archivo:

**Archivos pequeños (50-150 líneas):**
- Modelos de datos puros (dataclasses)
- Utilidades simples (1-3 funciones relacionadas)

**Archivos medianos (150-400 líneas):**
- Services (una operación de negocio)
- Managers (coordinar services relacionados)
- Widgets UI (componentes complejos)

**Archivos grandes PERMITIDOS (400-800 líneas):**
- Managers complejos con transiciones de estado
- Ventanas principales con setup de UI extensivo
- Módulos completos con helpers internos

**LÍMITE DURO: 800 líneas por archivo**

Razón: Optimización de ventana de contexto de IA
Por encima de 800 líneas → la IA pierde coherencia
Dividir en límites lógicos (responsabilidades)

### REGLA CRÍTICA:
✅ UN archivo con 400 líneas cohesivas
❌ CINCO archivos con 80 líneas fragmentadas

**Por qué:**
- Leer 1 archivo = ~500 tokens
- Leer 5 archivos = ~5000 tokens + overhead
- IA rastrea menos contextos = mejores resultados

### Solo Dividir Archivos Si:
- ✅ Responsabilidad diferente (TabManager vs TabStorage)
- ✅ Reutilizado en 3+ lugares (path_utils.py)
- ✅ Puede ser probado independientemente
- ❌ NUNCA dividir solo para reducir conteo de líneas

---

## 4. NO DUPLICACIÓN DE CÓDIGO (DRY CON DETECCIÓN)

### Antes de Escribir Código Similar:

**Paso 1:** ¿Esta función ya existe?
- SÍ → Usarla
- NO → Continuar al Paso 2

**Paso 2:** ¿Esta lógica se usará 2+ veces?
- SÍ → Crear función reutilizable en archivo utils apropiado
- NO → Mantener inline en archivo actual

### Patrones Comunes de Centralización:
- Operaciones de rutas → `path_utils.py`
- Validación de carpetas → `validators.py`
- Manejo de errores I/O → `error_handler.py`
- Extensiones de archivos → `file_extensions.py`

### Duplicación Prohibida:
- ❌ Normalizar rutas en 5 archivos diferentes
- ❌ Validar carpetas en 8 lugares diferentes
- ❌ Mismo manejo de errores en 10 ubicaciones

---

## 5. INYECCIÓN DE DEPENDENCIAS (SIEMPRE)

### Patrón Correcto:
```python
class TabManager:
    def __init__(self, storage: TabStorage, validator: FolderValidator):
        self._storage = storage
        self._validator = validator
```

### Patrón Incorrecto:
```python
class TabManager:
    def __init__(self):
        self._storage = TabStorage()  # ❌ Dependencia hardcodeada
        self._validator = FolderValidator()  # ❌ No se puede testear/intercambiar
```

### Por qué:
- Testing más fácil (inyectar mocks)
- Dependencias más claras (visibles en firma)
- Implementaciones flexibles (intercambiar sin cambiar clase)
- IA entiende estructura sin leer implementación

---

## 6. PATRONES PROHIBIDOS (DESPERDICIADORES DE TOKENS)

### ❌ NUNCA CREAR:

**1. Wrappers Vacíos (SIN LÓGICA):**
```python
# ❌ PROHIBIDO
def add_tab_wrapper(self, path):
    return execute_action(self, add_tab_action, path)

# ✅ CORRECTO
def add_tab(self, path: str) -> bool:
    # Implementación directa aquí
```

**Regla de Validación de IA:**
- Si wrapper tiene <3 líneas de lógica real → ELIMINARLO
- Si wrapper añade validación/logging/manejo de errores → MANTENERLO

**2. Archivos de Una Sola Función:**
```python
# ❌ PROHIBIDO: normalize_path.py
def normalize(path):
    return os.path.normpath(path)

# ✅ CORRECTO: Añadir a path_utils.py con funciones relacionadas
```

**3. Clases de Un Solo Método:**
```python
# ❌ PROHIBIDO
class PathNormalizer:
    def normalize(self, path): ...

# ✅ CORRECTO: Función simple en utils
def normalize_path(path: str) -> str: ...
```

**4. Nombres de Archivo Prohibidos:**
- `*_wrapper.py` → Code smell (a menos que añada lógica real)
- `*_helper.py` (con 1 función) → Code smell
- `*_utils.py` (con funciones no relacionadas) → Code smell

**5. God Objects:**
- Clase con >15 métodos públicos → Demasiado compleja, dividir por responsabilidad
- Archivo necesita 10+ imports → Demasiado acoplado, refactorizar

**6. Imports Circulares:**
- Si A importa B y B importa A → Fallo de diseño
- Solución: Crear C que ambos usan, o reestructurar

---

## 7. NOMBRES DESCRIPTIVOS (AUTO-DOCUMENTACIÓN)

### Clases:
- ✅ `FileListService`, `TabManager`, `FolderValidator`
- ❌ `Helper`, `Manager`, `Utils`, `Handler`

### Funciones:
- ✅ `get_files_from_folder()`, `validate_folder_path()`, `normalize_path()`
- ❌ `do_stuff()`, `process()`, `handle()`, `get_data()`

### Archivos:
- ✅ `tab_manager.py`, `file_list_service.py`, `path_utils.py`
- ❌ `manager.py`, `service.py`, `helpers.py`, `stuff.py`

**Regla:** El nombre debe explicar el propósito SIN leer código

---

## 8. TYPE HINTS (OBLIGATORIOS)

### Siempre Requeridos:
```python
# ✅ CORRECTO
def add_tab(self, path: str) -> bool: ...
def get_files(self, folder: str) -> List[str]: ...
def process_data(self, items: List[FileInfo]) -> Optional[Result]: ...

# ❌ INCORRECTO
def add_tab(self, path): ...
```

### Por qué:
- IA entiende sin leer implementación
- Detecta errores temprano
- Sirve como documentación inline
- Reduce tokens (no necesita inferir tipos)

---

## 9. ESTRATEGIA DE DOCUMENTACIÓN

### Docstrings: Solo Cuando Sea Necesario

**Nombres claros → No se necesita docstring:**
```python
def add_tab(self, path: str) -> bool:
    # Implementación (no se necesita docstring)
```

**Nombres poco claros O lógica compleja → Docstring breve:**
```python
def restore_state(self, tabs: List[str], history: List[str]) -> None:
    """Restaurar estado de aplicación sin crear entradas de historial."""
```

### Prohibido:
- ❌ Docstrings de 10 líneas para funciones simples
- ❌ Repetir lo que el nombre ya dice
- ❌ Descripciones de parámetros cuando los tipos son obvios

### Eficiencia de Tokens:
Nombre claro (5 tokens) > Nombre poco claro + docstring largo (150 tokens)

---

## 10. MANEJO DE ERRORES (EXPLÍCITO)

### Patrón Correcto:
```python
try:
    file_content = open(path).read()
except FileNotFoundError:
    logger.error(f"Archivo no encontrado: {path}")
    return None
except PermissionError:
    logger.error(f"Sin permiso: {path}")
    return None
```

### Patrón Incorrecto:
```python
try:
    file_content = open(path).read()
except:  # ❌ Demasiado amplio
    pass  # ❌ Fallo silencioso
```

### Reglas:
- Siempre capturar excepciones específicas
- Loggear errores con contexto (ruta, operación, etc.)
- Nunca usar `except: pass` desnudo
- Retornar defaults significativos o lanzar errores informativos

---

## 11. TESTING (OBLIGATORIO)

### Requisitos de Cobertura:

**Deben tener tests:**
- TODOS los Managers (`tab_manager`, `files_manager`, etc.)
- TODOS los Services con file I/O
- TODA lógica de negocio con condicionales

**Nice to have:**
- Utilidades simples
- Componentes UI puros (testing visual)

### Casos de Test Mínimos:
```python
def test_add_tab_success():
    """Probar adición exitosa de tab."""
    # Happy path

def test_add_tab_error():
    """Probar manejo de errores."""
    # Caso de error

def test_add_tab_edge_case():
    """Probar condiciones de borde."""
    # Caso edge
```

### Red Flags:
- 🚨 Test necesita >3 mocks → Clase mal diseñada → Refactorizar primero
- 🚨 Test necesita >5 líneas de setup → Clase demasiado compleja
- 🚨 Test es >30 líneas → Test hace demasiado → Dividir

---

## 12-24. REGLAS Qt/PySide6

[El contenido de las reglas 12-24 permanece igual que en el archivo original]

Ver archivo completo de reglas en: `.trae/rules/project_rules.md`

---

## REGLA DE COMENTARIOS (OBLIGATORIA)

El código debe explicar **qué hace** por sí solo.
Los comentarios solo se permiten para explicar **por qué** una lógica existe.

### Se permiten comentarios únicamente cuando:
- Hay lógica sensible (tiempos, debounce, doble clic, gestos, eventos)
- Hay decisiones no obvias que no deben modificarse
- El código puede parecer extraño pero es correcto y no debe refactorizarse

### No se permiten comentarios:
- Para explicar código evidente
- Para describir cada línea
- Como tutorial
- Para justificar mal diseño

### Formato de los comentarios:
- Máximo 1–2 líneas
- En español
- Explican la intención, no la implementación
- Sirven como protección frente a refactors automáticos de IA

### Regla para IA:
- Si un bloque de código tiene comentario, su comportamiento no debe cambiar
- No se permite "optimizar" ni refactorizar lógica comentada sin justificación explícita

---

## VALIDATION CHECKLIST (Antes de Completar Cualquier Tarea)

- [ ] ¿Puedo explicar esta clase en una frase?
- [ ] ¿Nombres claros sin leer código?
- [ ] ¿Sin código duplicado?
- [ ] ¿Dependencias inyectadas?
- [ ] ¿Tiene tests básicos?
- [ ] ¿Sigue separación de capas?
- [ ] ¿Type hints presentes?
- [ ] ¿Manejo de errores explícito?
- [ ] ¿Recursos Qt correctamente gestionados?
- [ ] ¿Operaciones pesadas en QThread?
- [ ] ¿Eventos de file system con debounce?
- [ ] ¿Previews/thumbnails en caché?
- [ ] ¿Operaciones largas cancelables?

**Si CUALQUIER respuesta es NO → Refactorizar antes de continuar.**

---

**FIN DE REGLAS DEL PROYECTO**
