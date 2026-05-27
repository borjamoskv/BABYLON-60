---
description: Proactive Optimization Radar — Continuous improvement detection and execution
---

# 🔭 PROACTIVO v1 — Radar de Optimización Continua

// turbo-all

Motor de detección y ejecución de mejoras que opera como capa subyacente a toda actividad. Cada tarea completada dispara un scan de optimización.

---

## Trigger: Post-Task Optimization Scan

Después de CADA tarea completada (explícita o autónoma), ejecutar este scan:

### 1. Code Quality Radar (< 2 calls)
```bash
# En el directorio del workspace activo:

# Archivos tocados en los últimos commits
git diff --name-only HEAD~3 2>/dev/null | head -20

# Complejidad ciclomática de archivos tocados (si hay herramienta)
# Detección de funciones largas
grep -rn "def \|function \|class " --include="*.py" --include="*.js" --include="*.ts" <archivos_tocados> | head -20
```

### 2. Debt Detector
Buscar automáticamente:
```
TODO|FIXME|HACK|XXX|TEMP|DEPRECATED|WORKAROUND
```
en archivos tocados. Si se encuentra:
- HACK/TEMP → Proponer fix
- TODO trivial (< 5 LOC de trabajo) → Ejecutar directamente
- DEPRECATED → Eliminar si no tiene dependientes

### 3. Stale Detection
- Archivos no tocados en >6 meses en el mismo directorio que archivos activos → flag
- Tests que no se ejecutan → flag
- Configuraciones que no aplican → proponer eliminación

---

## Decision Matrix para Auto-Ejecución

```
                    IMPACTO
              Bajo        Alto
         ┌──────────┬──────────┐
  RIESGO │ EJECUTAR │ PROPONER │
   Bajo  │ sin ask  │ con plan │
         ├──────────┼──────────┤
  RIESGO │ EJECUTAR │  STOP +  │
   Alto  │ informar │  review  │
         └──────────┴──────────┘
```

---

## Optimizaciones Específicas por Lenguaje

### Python
- `import` no usado → eliminar
- `f-string` donde hay `format()` o `%` → modernizar
- `type hints` faltantes en funciones públicas → añadir
- `__all__` faltante en `__init__.py` → añadir si >3 exports
- Context managers donde hay try/finally → refactorizar

### JavaScript/TypeScript
- `var` → `const`/`let`
- `.then()` chains → `async/await`
- `require()` → `import`
- Callbacks anidados → flatten
- `==` → `===`

### CSS
- Propiedades duplicadas → eliminar
- Selectores no usados → purgar
- Valores hardcoded → custom properties
- Prefijos obsoletos → eliminar

### Shell/Bash
- Scripts sin `set -euo pipefail` → añadir
- Paths sin comillas → comillar
- `$(command)` donde hay backticks → modernizar

---

## Heurísticas de Complejidad

| Señal | Acción |
|---|---|
| Función > 40 LOC | Flag para split |
| Clase > 300 LOC | Flag para decomposición |
| Archivo > 500 LOC | Flag para split |
| Indentación > 4 niveles | Flag para extract method |
| Parámetros > 5 | Flag para parameter object |
| Imports > 15 | Flag para dependencia excesiva |

---

## Output Format

```
🔭 PROACTIVO — Scan completado:
  📍 Archivos escaneados: N
  🔧 Optimizaciones ejecutadas: N
  📋 Optimizaciones propuestas: N
  ⚡ Deuda técnica detectada: +/-N items
```

---

*∴ PROACTIVO v1 ◈ "Cada tarea completada es el trigger de la siguiente mejora."*
