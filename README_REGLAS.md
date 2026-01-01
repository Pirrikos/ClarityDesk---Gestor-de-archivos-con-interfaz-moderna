# 📚 Documentación de Reglas - ClarityDesk Pro

**Fecha:** 2026-01-01
**Propósito:** Índice de documentación arquitectónica y reglas del proyecto

---

## 🗂️ Organización de Documentos

Este proyecto mantiene su documentación organizada en tres categorías:

### 1. Reglas Permanentes (Arquitectura Core)
**Archivo:** [REGLAS_DEL_PROYECTO.md](REGLAS_DEL_PROYECTO.md)

**Contenido:**
- Arquitectura de capas (models → services → managers → ui)
- Patrones de código obligatorios
- Convenciones de estilo
- Directrices Qt/PySide6
- Protocolos de testing
- Regla de comentarios

**Cuándo usar:**
- En todo momento durante el desarrollo
- Para validar código nuevo
- Para revisar pull requests
- Antes de escribir cualquier funcionalidad

**Permanencia:** ✅ Reglas fijas, no cambian con fases

---

### 2. Reglas Temporales (Consolidación Actual)
**Archivo:** [REGLAS_DE_CONSOLIDACION.md](REGLAS_DE_CONSOLIDACION.md)

**Contenido:**
- 12 reglas fundamentales de consolidación
- Qué es y qué NO es consolidación
- Principio de fuente de verdad única
- Regla de nombres crítica
- Regla de fragmentación controlada
- Reglas específicas para IA

**Cuándo usar:**
- Durante Fase B y Fase C (consolidación)
- Cuando se reorganiza código existente
- Cuando se eliminan duplicados
- Cuando se renombran archivos/clases

**Temporalidad:** ⏱️ Solo durante fase de consolidación

**Objetivo:** Reducir ambigüedad, eliminar confusión estructural, congelar contratos

---

### 3. Reglas de Evolución (Futuro)
**Archivo:** [REGLAS_DE_REFACTOR.md](REGLAS_DE_REFACTOR.md)

**Contenido:**
- Cuándo y cómo refactorizar
- Tipos de refactorización válidos
- Anti-patrones de refactorización
- Métricas y validación
- Proceso de refactorización
- Checklist de aprobación

**Cuándo usar:**
- DESPUÉS de fase de consolidación
- Cuando hay evidencia de problemas de rendimiento
- Cuando hay bugs recurrentes en misma zona
- Para mejoras con beneficio medible (>20%)

**Futuro:** 🔮 Para evolución post-consolidación

---

## 🗺️ Mapa Arquitectónico

**Archivo:** [MAPA_PROYECTO.md](MAPA_PROYECTO.md)

**Contenido:**
- Árbol completo de estructura del proyecto
- Análisis por capas
- Problemas arquitectónicos detectados
- Evaluación de diseño
- Estadísticas finales
- Historial de cambios

**Cuándo usar:**
- Para entender la estructura completa
- Para onboarding de nuevos desarrolladores
- Para planificar cambios arquitectónicos
- Para auditorías de código

**Actualización:** Se actualiza después de cambios estructurales significativos

---

## 🎯 Flujo de Trabajo Recomendado

### Para Desarrollo Normal:
1. Leer [REGLAS_DEL_PROYECTO.md](REGLAS_DEL_PROYECTO.md)
2. Consultar [MAPA_PROYECTO.md](MAPA_PROYECTO.md) para ubicación de archivos
3. Seguir arquitectura de capas estrictamente

### Durante Consolidación:
1. Seguir [REGLAS_DE_CONSOLIDACION.md](REGLAS_DE_CONSOLIDACION.md) **obligatoriamente**
2. Validar con checklist antes de cada cambio
3. NO añadir funcionalidades, solo reorganizar

### Para Refactorización Futura:
1. Verificar que consolidación está completa
2. Seguir [REGLAS_DE_REFACTOR.md](REGLAS_DE_REFACTOR.md)
3. Medir antes y después
4. Documentar decisión

---

## 🤖 Instrucciones para IA

### Al inicio de sesión:
1. Cargar [REGLAS_DEL_PROYECTO.md](REGLAS_DEL_PROYECTO.md) completo (una vez)
2. Identificar fase actual del proyecto
3. Cargar reglas de fase correspondiente

### Durante tareas:
- Citar solo números de regla relevantes (ej: "Siguiendo reglas 3, 16, 18")
- Validar contra checklist antes de cambios
- Preguntar si hay ambigüedad

### Fase actual:
**Fase B - Consolidación**
→ Usar [REGLAS_DE_CONSOLIDACION.md](REGLAS_DE_CONSOLIDACION.md) como guía principal

---

## 📊 Métricas del Proyecto

**Total archivos Python (app/):** 243 archivos
- **Models:** 5 archivos
- **Services:** 77 archivos
- **Managers:** 15 archivos
- **UI Widgets:** 98 archivos
- **UI Windows:** 35+ archivos
- **Core:** 3 archivos

**Estado:** Arquitectura sólida, consolidación en progreso

---

## 🔗 Enlaces Rápidos

| Documento | Propósito | Cuándo Usar |
|-----------|-----------|-------------|
| [REGLAS_DEL_PROYECTO.md](REGLAS_DEL_PROYECTO.md) | Arquitectura permanente | Siempre |
| [REGLAS_DE_CONSOLIDACION.md](REGLAS_DE_CONSOLIDACION.md) | Consolidación temporal | Fase B/C |
| [REGLAS_DE_REFACTOR.md](REGLAS_DE_REFACTOR.md) | Evolución futura | Post-consolidación |
| [MAPA_PROYECTO.md](MAPA_PROYECTO.md) | Estructura completa | Navegación y onboarding |

---

## ⚡ Quick Reference

### Regla de Oro:
> **Si no puedes explicar por qué existe un archivo en una frase, está mal consolidado.**

### Principio Final:
```
Funciona ≠ está bien hecho
Está bien hecho ≠ hay que tocarlo ahora
```

### Capas (inmutable):
```
core → models → services → managers → ui
```

### Límites:
- Max 800 líneas/archivo
- Max 15 métodos públicos/clase
- Min 3 tests/componente

---

**Última actualización:** 2026-01-01
**Versión de reglas:** 2.1
**Estado del proyecto:** Fase B - Consolidación
