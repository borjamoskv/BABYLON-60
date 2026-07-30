---
description: "Investigación forense de bugs — 5 Whys, blast radius, git bisect, y arqueología causal."
---

# 🔍 DETECTIVE — Forensics Protocol

// turbo-all

## Paso 1 — Capturar Síntoma
```
SÍNTOMA: [descripción exacta]
EVIDENCIA: [error message, logs, stack trace]
REPRODUCIBLE: [sí/no + steps]
```

## Paso 2 — Git Archaeology
```bash
git log --oneline -20
git log --all --oneline -- "[archivo_sospechoso]"
git bisect start && git bisect bad HEAD && git bisect good [commit_bueno]
```

## Paso 3 — Blast Radius
```bash
grep -rn "[patrón_del_bug]" --include="*.py" --include="*.js" | head -30
```

## Paso 4 — 5 Whys
```
1. ¿POR QUÉ falla? → [con evidencia]
2. ¿POR QUÉ [1]? → [con evidencia]
3. ¿POR QUÉ [2]? → [con evidencia]
4. ¿POR QUÉ [3]? → [con evidencia]
5. ROOT CAUSE → [causa raíz]
```

## Paso 5 — Fix + Prevention
FIX: [ataca causa raíz]. PREVENT: [test/hook/lint rule].

> **Skills:** `Archaeologist-Omega`, `BABYLON60-Guard-Omega`
