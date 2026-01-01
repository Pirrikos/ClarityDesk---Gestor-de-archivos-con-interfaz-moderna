# REGLAS DE CONSOLIDACIÓN — ClarityDesk Pro

**Versión:** 1.0
**Fecha:** 2026-01-01
**Propósito:** Directrices arquitectónicas para consolidación asistida por IA

---

## 0. Objetivo de la consolidación

La consolidación **NO añade funcionalidades**.
La consolidación **NO cambia comportamiento visible**.

### Su objetivo es:

- **Reducir ambigüedad** - Claridad arquitectónica
- **Eliminar confusión estructural** - Organización coherente
- **Congelar contratos internos** - APIs estables
- **Hacer el proyecto mantenible y legible a largo plazo** - Código sostenible

**Regla fundamental:** Si algo funciona, no se toca salvo que viole una regla.

---

## 1. Regla de Oro (inmutable)

> **Si no puedes explicar por qué existe un archivo en una frase, está mal consolidado.**

---

## 2. Regla de Congelación Funcional

### Ningún cambio debe alterar:

- ❌ UX (experiencia de usuario)
- ❌ Flujos de usuario
- ❌ Resultados de operaciones

### Contratos inmutables:

- ✅ No se cambian firmas públicas salvo duplicación clara
- ✅ Los tests existentes deben seguir pasando sin modificación
- ❌ Si un cambio requiere "ajustar tests", **NO es consolidación**

---

## 3. Regla de Capas (estricta)

### Las capas no se negocian:

```
core → models → services → managers → ui
```

### Prohibido:

- ❌ UI importando services "profundos" directamente si existe manager
- ❌ Services dependiendo de UI
- ❌ Models con lógica de orquestación

**Si algo rompe esto, se corrige aunque funcione.**

---

## 4. Regla de Fuente de Verdad Única

Para cada dominio debe existir **una sola fuente de verdad**.

### Ejemplos actuales:

| Dominio | Fuente de Verdad |
|---------|------------------|
| Borrado de archivos | `file_delete_service.py` |
| Preview de documentos | `PreviewPdfService` |
| Estado de archivos | `file_state_storage` |
| Gestión de tabs | `TabManager` |

### Duplicación permitida solo si:

1. Está **explícitamente documentada**
2. Tiene **nombres claramente distintos**
3. Las **responsabilidades NO se solapan**

---

## 5. Regla de Nombres (crítica)

### Dos archivos NO pueden llamarse igual si hacen cosas distintas.

#### Caso prohibido (ejemplo real):
```
❌ tab_manager_init.py en app/services/
❌ tab_manager_init.py en app/managers/
```
*Mismo nombre, diferentes responsabilidades.*

#### Solución obligatoria:

1. **Renombrar** para reflejar intención
2. **No fusionar** por comodidad
3. **No mover** lógica innecesariamente
4. **El nombre es parte de la arquitectura**

---

## 6. Regla de Fragmentación Controlada

### Dividir archivos es correcto solo si:

- ✅ Cada archivo tiene una **responsabilidad clara**
- ✅ La navegación **mejora**, no empeora
- ✅ No existen más de **2–3 `*_utils.py`** por dominio

### Se considera fragmentación excesiva:

- ❌ Archivos de 30–50 líneas sin identidad clara
- ❌ Utilidades que solo agrupan funciones sueltas
- ⚠️ Esto no es urgente, pero se marca para **Fase C**

#### Ejemplo actual:
```
⚠️ FolderTreeSidebar (11 archivos):
   - folder_tree_icon_utils.py
   - folder_tree_index_utils.py
   - folder_tree_menu_utils.py
   - folder_tree_widget_utils.py
   → Candidato a consolidación en Fase C
```

---

## 7. Regla de Wrappers

### Un wrapper solo es válido si:

- ✅ Añade **semántica clara**
- ✅ Añade **validación**
- ✅ Añade **señales/eventos**
- ✅ Protege a la UI de **cambios futuros**

### Si solo delega llamadas:

1. Se marca como **"wrapper ligero"**
2. **No se elimina** sin decisión consciente
3. **Nunca** se refactoriza "por limpieza"

#### Ejemplo actual:
```python
# focus_manager.py - Wrapper ligero
# Delega a TabManager pero añade señales específicas
# → Mantener hasta evaluación explícita
```

---

## 8. Regla de Duplicación Real vs Organizativa

### No toda duplicación es mala.

#### Duplicación real (debe corregirse):

- ❌ Código copiado
- ❌ Lógica repetida
- ❌ Bugs corregidos en un sitio pero no en otro

#### Duplicación organizativa (aceptable):

- ✅ Archivos similares en contextos distintos
- ✅ Motores compartidos con configuración distinta

### Antes de tocar:

**Demostrar que es duplicación real**, no organizativa.

---

## 9. Regla de IA (muy importante)

### La IA puede:

- ✅ Refactorizar
- ✅ Mover archivos
- ✅ Renombrar

### Pero:

- ❌ **Nunca decide arquitectura sola**
- ✅ Siempre actúa con **reglas explícitas**
- ✅ Cada paso es **pequeño y reversible**

> **Prompt sin reglas = código inflado**

---

## 10. Regla de Cierre de Fase

### Una fase de consolidación solo se considera cerrada si:

1. ✅ No hay archivos con **nombres ambiguos**
2. ✅ No hay **duplicaciones reales** sin justificar
3. ✅ El árbol se puede **explicar de memoria**
4. ✅ El proyecto **"da calma", no miedo**

---

## 11. Qué NO es consolidación

### No es consolidación:

- ❌ "Ya que estamos…" (scope creep)
- ❌ Optimizar rendimiento
- ❌ Reescribir widgets porque "son feos"
- ❌ Reducir archivos solo por número
- ❌ Perseguir la perfección

---

## 12. Principio final

```
Funciona ≠ está bien hecho
Está bien hecho ≠ hay que tocarlo ahora
```

---

## Decisiones de consolidación

### focus_manager.py
- Se mantiene como fachada semántica del concepto Focus.
- Actualmente delega en TabManager.
- Su existencia es intencional para aislar la UI y permitir evolución futura.
- No se considera wrapper innecesario.

---

## 📋 Aplicación de Reglas - Checklist

Antes de cualquier consolidación, verificar:

- [ ] ¿Esto es realmente consolidación o mejora funcional?
- [ ] ¿Los tests siguen pasando sin cambios?
- [ ] ¿La UX se mantiene idéntica?
- [ ] ¿Las capas se respetan?
- [ ] ¿Hay fuente de verdad única?
- [ ] ¿Los nombres son claros y únicos?
- [ ] ¿Es duplicación real o organizativa?
- [ ] ¿El cambio es pequeño y reversible?
- [ ] ¿Puedo explicar el archivo en una frase?

---

## 🎯 Ejemplos de Buena Consolidación

### Ejemplo 1: Eliminación de alias confuso
```python
# ANTES (ambiguo)
PreviewService = PreviewPdfService  # ¿Qué es PreviewService?

# DESPUÉS (claro)
# UI usa directamente PreviewPdfService
# preview_service.py solo tiene utilidades auxiliares
```

### Ejemplo 2: Unificación de lógica de borrado
```python
# ANTES (duplicado real)
file_deletion_service.py → move_to_windows_recycle_bin()
file_delete_service.py → delete_file()

# DESPUÉS (fuente única)
file_delete_service.py → delete_file()  # Fuente de verdad
file_deletion_service.py → is_folder_empty()  # Utilidad específica
```

---

## 🚫 Ejemplos de Mala Consolidación

### Ejemplo 1: "Ya que estamos"
```python
# ❌ MAL
# "Voy a consolidar file_tile.py y ya que estamos,
#  mejoro las animaciones y añado zoom"
# → Esto NO es consolidación, es feature creep
```

### Ejemplo 2: Fusión sin justificación
```python
# ❌ MAL
# "Estos dos archivos hacen cosas parecidas, los fusiono"
# → ¿Son duplicación real u organizativa?
# → ¿Se puede explicar el resultado en una frase?
```

---

## 📝 Historial de Versiones

### v1.0 (2026-01-01)
- Creación inicial del documento
- Codificación de las 12 reglas fundamentales
- Ejemplos de aplicación correcta e incorrecta

---

**IMPORTANTE PARA IA:** Este documento es la base arquitectónica para cualquier trabajo de consolidación. Leer completamente antes de proponer cambios. Ante la duda, preguntar al usuario.
