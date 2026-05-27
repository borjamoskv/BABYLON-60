---
description: Preventive build rule — compile after each logical group of changes
---

# 🔨 Compilación Preventiva v2 — Regla de Oro

// turbo-all

**NUNCA acumules más de un grupo lógico de cambios sin compilar.**

---

## Detección Automática de Proyecto

| Archivo presente | Comando build | Comando quick check |
|---|---|---|
| `package.json` + `build` script | `npm run build` | `npx tsc --noEmit` (TS) |
| `package.json` + `dev` script | `npm run dev` → verificar arranque | — |
| `index.html` (sin package.json) | Abrir en browser | `node --check *.js` |
| `Package.swift` | `swift build` | `swift build 2>&1 | tail -5` |
| `Cargo.toml` | `cargo build` | `cargo check` |
| `pyproject.toml` / `setup.py` | `python -m py_compile <file>` | `python -c "import <mod>"` |
| `go.mod` | `go build ./...` | `go vet ./...` |
| `Makefile` | `make` | `make check` |

---

## Qué es un "Grupo Lógico"

| ✅ Un grupo | ❌ NO son un solo grupo |
|---|---|
| 1 componente + sus estilos | 3+ componentes nuevos |
| Renombrar función + usos | Cambiar estructura + migrar UI |
| Fix 1 bug (causa + efecto) | Feature completo 5+ archivos |
| Extraer módulo reutilizable | Refactor de toda la arquitectura |

---

## Señales de Alerta 🚨

Compilar **INMEDIATAMENTE** si:
- **> 3 archivos** editados sin compilar
- Cambiaste una **interfaz/tipo/protocolo** que otros importan
- **Renombraste** algo importado en múltiples sitios
- **> 10 minutos** de edición continua sin compilar
- Próximo cambio **depende** de los anteriores

---

## Protocolo de Reporte

```
✅ BUILD OK (npm run build) — 0 errores, 0 warnings
```

```
❌ BUILD FAILED — 2 errores:
  • src/app.js:42 — TypeError: x is not a function
  • src/utils.js:15 — ReferenceError: y is not defined
→ Corrigiendo antes de continuar...
```

---

## Integración Multi-Workflow

| Dentro de... | Cuándo compilar |
|---|---|
| `/mejoralo` | Entre cada ola (1→2→3→4) |
| `/detective` | Después de cada auto-fix |
| `/guardian` | Después de cada fix CSS/HTML |
| `/refactor` | Después de cada extracción |
| Cualquier tarea | Cada grupo lógico |

---

## Excepciones (NO compilar)

- Solo editaste `.md`, comentarios, o docs
- Solo editaste `.env`, `.gitignore`, configuración
- El usuario dice "no compiles todavía"
- Estás en medio de un refactor multi-paso planificado

---

## Para Proyectos Multi-Stack

Si el proyecto tiene web + python + swift:
```bash
# Compilar el stack que tocaste
# Web → npm run build
# Python → python -m py_compile archivo.py
# Swift → swift build

# NO compilar stacks que no tocaste
```
