# REGLAS DE REFACTOR — ClarityDesk Pro

**Versión:** 1.0
**Tipo:** Evolución futura
**Fecha:** 2026-01-01
**Propósito:** Directrices para mejoras y evolución del código

---

## 🎯 Propósito de este Documento

Este documento contiene reglas para la **evolución futura** del proyecto:
- Refactorización de código existente
- Mejoras de rendimiento
- Optimizaciones arquitectónicas
- Evolución de patrones

**IMPORTANTE:** Estas reglas aplican DESPUÉS de que las [Reglas de Consolidación](REGLAS_DE_CONSOLIDACION.md) se hayan completado.

---

## ⚠️ Principio Fundamental

```
Refactorizar ≠ Consolidar
Refactorizar = Mejorar código que ya funciona
Consolidar = Organizar código sin cambiar comportamiento
```

---

## 📋 Cuándo Refactorizar

### ✅ CUÁNDO SÍ:
1. **Después de Fase de Consolidación**
   - El proyecto está organizado
   - Los contratos están claros
   - La arquitectura está congelada

2. **Cuando hay Evidencia Clara**
   - Métricas de rendimiento muestran cuellos de botella
   - Usuarios reportan problemas específicos
   - Tests revelan fragilidad en el código

3. **Cuando hay Beneficio Medible**
   - Mejora de rendimiento >20%
   - Reducción de bugs recurrentes
   - Simplificación que elimina >100 líneas

### ❌ CUÁNDO NO:
1. **Porque "se puede hacer mejor"**
   - Código funciona
   - No hay problemas reportados
   - No hay métricas que lo justifiquen

2. **Porque "no me gusta el estilo"**
   - Preferencias personales
   - "Esto podría ser más elegante"
   - "Yo lo haría diferente"

3. **Porque "la IA lo sugiere"**
   - La IA ofrece refactorización no solicitada
   - No hay regla que lo respalde
   - No hay problema que resolver

---

## 🛠️ Tipos de Refactorización

### 1. Refactorización de Rendimiento

**Criterio:** Solo si hay evidencia de problema de rendimiento

**Proceso:**
1. Medir (profiling, benchmarks)
2. Identificar cuello de botella
3. Proponer solución
4. Medir mejora
5. Si mejora >20% → Aplicar

**Ejemplo válido:**
```python
# ANTES (medido: 2 segundos para 1000 archivos)
def get_all_icons():
    for file in files:
        icon = generate_icon(file)  # Llamada síncrona
        icons.append(icon)

# DESPUÉS (medido: 0.3 segundos)
def get_all_icons():
    with ThreadPoolExecutor() as executor:
        icons = list(executor.map(generate_icon, files))
```

### 2. Refactorización de Claridad

**Criterio:** Solo si el código es objetivamente confuso

**Indicadores de confusión real:**
- Múltiples desarrolladores no entienden la lógica
- Bugs recurrentes en la misma zona
- Necesita >10 minutos para entender una función

**Ejemplo válido:**
```python
# ANTES (confuso)
def p(f, t=0):
    return f if t < 1 else f[:t] if t > 0 else f[t:]

# DESPUÉS (claro)
def truncate_filename(filename: str, max_length: int = 0) -> str:
    """Trunca nombre de archivo a longitud máxima."""
    if max_length == 0:
        return filename
    return filename[:max_length]
```

### 3. Refactorización de Tests

**Criterio:** Solo para mejorar cobertura o detectabilidad de bugs

**Válido:**
- Añadir tests faltantes para casos edge
- Mejorar aserciones débiles
- Añadir tests de integración

**Inválido:**
- Reescribir tests que pasan
- Cambiar estilo de tests
- Añadir tests "por completitud"

---

## 🚫 Anti-Patrones de Refactorización

### 1. "Refactor Because IA Suggested"
```
❌ IA: "Puedo optimizar esta función"
❌ Dev: "Ok, hazlo"

✅ Dev: "¿Qué problema resuelve?"
✅ IA: "Ninguno, solo es más elegante"
✅ Dev: "Entonces no lo hagas"
```

### 2. "Premature Optimization"
```
❌ "Este loop podría ser más rápido con list comprehension"
   → Si no es cuello de botella, no tocar

✅ "Este loop toma 5 segundos en profiling"
   → Medir, optimizar, validar
```

### 3. "Refactor Creep"
```
❌ "Ya que estoy refactorizando X, también haré Y y Z"
   → Scope creep

✅ "Refactorizo solo X, como se planeó"
   → Foco claro
```

---

## 📊 Métricas de Refactorización

### Antes de Refactorizar:
1. **Medir estado actual**
   - Rendimiento (tiempo, memoria)
   - Complejidad ciclomática
   - Cobertura de tests

2. **Definir objetivo**
   - "Reducir tiempo de carga en 50%"
   - "Reducir complejidad de X a Y"
   - "Aumentar cobertura a 80%"

3. **Establecer criterio de éxito**
   - Métrica específica
   - Umbral de mejora
   - Sin regresiones

### Después de Refactorizar:
1. **Validar mejora**
   - ¿Se cumplió el objetivo?
   - ¿Tests siguen pasando?
   - ¿No hay regresiones?

2. **Documentar cambio**
   - Por qué se refactorizó
   - Qué se mejoró
   - Métricas antes/después

---

## 🎯 Proceso de Refactorización

### Paso 1: Justificación
```markdown
**Problema:** Carga de 1000 archivos toma 5 segundos
**Causa:** Generación de iconos síncrona
**Propuesta:** Paralelizar con ThreadPool
**Mejora esperada:** <1 segundo
```

### Paso 2: Planificación
```markdown
**Archivos afectados:**
- icon_service.py (modificar)
- icon_batch_worker.py (nuevo)

**Tests afectados:**
- test_icon_service.py (actualizar)

**Riesgos:**
- Posible race condition en caché
- Necesita validar thread-safety
```

### Paso 3: Implementación
- Crear branch de refactor
- Implementar cambios
- Validar tests
- Medir mejora

### Paso 4: Validación
- Tests pasan
- Mejora medida cumple objetivo
- Sin regresiones de funcionalidad
- Sin nuevos bugs

### Paso 5: Documentación
- Actualizar CHANGELOG
- Comentar decisiones no obvias
- Actualizar métricas del proyecto

---

## 📝 Checklist de Refactorización

Antes de aprobar un refactor, verificar:

- [ ] ¿Hay problema real medible?
- [ ] ¿Objetivo está definido con métricas?
- [ ] ¿Solución es la más simple que funciona?
- [ ] ¿Tests siguen pasando?
- [ ] ¿No hay regresiones?
- [ ] ¿Mejora cumple objetivo (>20%)?
- [ ] ¿Cambio está documentado?
- [ ] ¿No introduce complejidad innecesaria?

**Si CUALQUIER respuesta es NO → No refactorizar.**

---

## 🔮 Refactorizaciones Futuras (Ejemplos)

### Candidatos Potenciales (No Urgentes):

1. **FolderTreeSidebar (11 archivos)**
   - **Problema:** Fragmentación excesiva
   - **Solución:** Consolidar utils relacionados
   - **Cuándo:** Fase C (no antes)

2. **Icon Rendering Pipeline**
   - **Problema:** Posible optimización de caché
   - **Solución:** Implementar LRU cache más agresivo
   - **Cuándo:** Si métricas muestran cache miss alto

3. **File State Storage**
   - **Problema:** Queries podrían ser más eficientes
   - **Solución:** Índices adicionales en SQLite
   - **Cuándo:** Si carga de >10,000 archivos es lenta

---

## ⚖️ Decisión: ¿Refactorizar o No?

### Usar este árbol de decisión:

```
¿Hay problema medible?
├─ NO → No refactorizar
└─ SÍ → Continuar

¿Hay solución clara?
├─ NO → Investigar más
└─ SÍ → Continuar

¿Mejora esperada >20%?
├─ NO → No vale la pena
└─ SÍ → Continuar

¿Tests cubren funcionalidad?
├─ NO → Escribir tests primero
└─ SÍ → Continuar

¿Riesgo de regresión es bajo?
├─ NO → Replantear approach
└─ SÍ → REFACTORIZAR
```

---

## 🎓 Lecciones Aprendidas

### DO:
- ✅ Medir antes y después
- ✅ Definir objetivo claro
- ✅ Documentar decisión
- ✅ Mantener tests pasando
- ✅ Un refactor a la vez

### DON'T:
- ❌ Refactorizar sin métricas
- ❌ "Mejorar" código que funciona
- ❌ Cambiar estilo por preferencia
- ❌ Optimizar sin profiling
- ❌ Refactor creep (scope)

---

## 📚 Referencias

- [REGLAS_DEL_PROYECTO.md](REGLAS_DEL_PROYECTO.md) - Reglas permanentes
- [REGLAS_DE_CONSOLIDACION.md](REGLAS_DE_CONSOLIDACION.md) - Consolidación actual
- [MAPA_PROYECTO.md](MAPA_PROYECTO.md) - Estado arquitectónico

---

**IMPORTANTE:** Este documento es para **futuro**. En fase actual (Consolidación), seguir [REGLAS_DE_CONSOLIDACION.md](REGLAS_DE_CONSOLIDACION.md).
