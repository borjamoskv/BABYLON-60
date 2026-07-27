<!-- [C5-REAL] Exergy-Maximized -->
---
cat_id: ouroboros
cat_type: workflow
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
description: "OUROBOROS-\u221E \u2014 El skill supremo. Inteligencia aut\xF3noma auto-evolutiva\
  \ con razonamiento causal, War Council multi-modelo, arqueolog\xEDa temporal, adversarial\
  \ testing, y meta-cognici\xF3n recursiva."
---



# ∞ OUROBOROS-∞ — The Infinite Self

// turbo-all

> **El skill que se mejora a sí mismo.** No opera sobre tu código — opera sobre tu proceso.

Antes de ejecutar, LEER la skill completa:
```bash
cat ~/.gemini/antigravity/skills/ouroboros-infinity/SKILL.md
```

---

## 🔮 Comandos Rápidos

| Comando | Qué hace | Cuándo usar |
|:---|:---|:---|
| `ouro-genesis` | Despertar completo: scan + archaeology + war council + plan | Inicio de sesión compleja |
| `ouro-evolve [target]` | MEJORAlo + causal reasoning + meta-learning | Mejorar archivo/módulo/proyecto |
| `ouro-diagnose [symptom]` | 5 Whys + blast radius + prevention | Bug que no entiendes |
| `ouro-fortress [project]` | Hardening de 5 capas | Proyecto que va a producción |
| `ouro-reflect` | Meta-cognición forzada | Final de sesión |
| `ouro-pulse` | Entropía rápida (2 min) | Check rápido de salud |
| `ouro-why "..."` | 5 Whys express | Síntoma rápido |
| `ouro-council "..."` | War Council spot | Decisión importante |
| `ouro-adversary [plan]` | Red Team un plan | Antes de ejecutar |
| `ouro-timeline [file]` | Arqueología temporal | Historia de un archivo |
| `ouro-entropy [project]` | Entropía detallada | Auditoría de complejidad |
| `ouro-learn` | Extraer learnings → BABYLON-60 | Final de sesión |

---

## ⚡ PROTOCOLO GENESIS-∞ (Despertar Completo)

### Paso 1 — Environment Scan

```bash
# Git state
git status --short
git log --oneline -10

# Running processes
ps aux | grep -E 'python|node|swift|cargo' | grep -v grep | head -10

# CORTEX state
cd ~/cortex && .venv/bin/python -m cortex.cli export 2>&1 | tail -5
```

### Paso 2 — Temporal Archaeology

```bash
# Historia del proyecto
git log --oneline -20
git log --stat -5

# Decisiones previas en CORTEX
cd ~/cortex && .venv/bin/python -m cortex.cli search "type:decision" --limit 10 2>/dev/null
```

### Paso 3 — BABYLON-60 Deep Recall (Error Memory)

```bash
# Errores previos
cd ~/cortex && .venv/bin/python -m cortex.cli search "type:error" --limit 10 2>/dev/null

# Meta-learnings previos
cd ~/cortex && .venv/bin/python -m cortex.cli search "type:meta_learning" --limit 10 2>/dev/null
```

### Paso 4 — Entropy Analysis

Medir las 7 dimensiones de entropía:

```bash
# File Entropy (archivos > 300 LOC)
find . -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.swift" | xargs wc -l 2>/dev/null | sort -rn | head -20

# Ghost Entropy (ghosts activos)
cat ~/.cortex/context-snapshot.md 2>/dev/null | grep -i ghost | head -10

# Branch Entropy
git branch -a --sort=-committerdate | head -15

# Import Entropy (Python: imports no usados)
# Solo si es proyecto Python
ruff check . --select F401 2>/dev/null | head -20
```

### Paso 5 — War Council

Presentar hallazgos y deliberar:

1. **PRESENTAR**: Resumir estado en ≤3 frases con datos.
2. **DELIBERAR**: Proponer 2-3 estrategias diferentes.
3. **CHALLENGE (Red Team)**:
   - "¿Qué pasa si esta estrategia falla en el paso 3?"
   - "¿Cuál es el peor caso?"
   - "¿Hay un edge case que no estamos viendo?"
4. **MERGE**: Tomar la mejor estrategia superviviente.
5. **COMMIT**: Documentar la decisión en `implementation_plan.md`.

### Paso 6 — Battle Plan

Generar `implementation_plan.md` con:
- Score de entropía inicial
- Target de entropía
- Waves de ejecución con checkpoints
- Adversarial challenges sobrevividas
- Exit criteria

---

## ⚡ PROTOCOLO EVOLVE (Mejora Consciente)

### Paso 1 — Diagnóstico Enhanced (X-Ray 13D + Causal + Entropy)

Ejecutar `/mejoralo` diagnóstico (Fase 2) PERO añadir:

```
Causal Layer:
→ ¿POR QUÉ existe la deuda técnica encontrada?
→ ¿CUÁNDO se introdujo? (git log -S)
→ ¿QUIÉN la introdujo y en qué contexto? (git blame)

Entropy Layer:
→ ¿La mejora reducirá o aumentará la entropía?
→ ¿Cuántos archivos nuevos vs eliminados?
→ ¿La abstracción nueva justifica su peso?
```

### Paso 2 — Red Team el Plan

Antes de ejecutar cada ola, atacar:
- **¿Puedes hacer lo mismo en menos archivos?**
- **¿Hay un cambio que haga innecesarios 3 de los demás?**
- **¿Qué rompe si este cambio falla a medias?**

### Paso 3 — Ejecución Adaptativa

Ejecutar olas según `/mejoralo` PERO:
- Medir entropía entre olas (no solo score).
- Si entropía aumenta → PARAR y simplificar.
- Si una ola falla → Causal analysis ANTES de retry.

### Paso 4 — Meta-Reflection Post-Sesión

Automático al terminar. Ver protocolo REFLECT abajo.

---

## ⚡ PROTOCOLO DIAGNOSE (Diagnóstico Causal)

### Paso 1 — Capturar Síntoma

```
SÍNTOMA EXACTO: [descripción precisa]
EVIDENCIA: [error message, log, screenshot]
DESDE CUÁNDO: [primera vez observado]
REPRODUCIBLE: [sí/no + steps]
```

### Paso 2 — Temporal Bisect

```bash
# ¿Cuándo empezó a fallar?
git log --oneline -20
# Si binario: git bisect start
# Si no: razonar cuándo cambió basándose en logs
```

### Paso 3 — 5 Whys

```
1. ¿POR QUÉ falla? → [respuesta con evidencia]
2. ¿POR QUÉ [causa 1]? → [respuesta con evidencia]
3. ¿POR QUÉ [causa 2]? → [respuesta con evidencia]
4. ¿POR QUÉ [causa 3]? → [respuesta con evidencia]
5. ¿POR QUÉ [causa 4]? → ROOT CAUSE: [causa raíz]
```

### Paso 4 — Blast Radius

```bash
# ¿Qué más afecta la causa raíz?
grep -rn "[patrón de la causa raíz]" --include="*.py" --include="*.js" --include="*.swift"
```

### Paso 5 — Fix + Prevention

```
FIX: [solución que ataca la causa raíz, no el síntoma]
PREVENT: [test, hook, lint rule, o documentación que evite recurrencia]
```

### Paso 6 — BABYLON-60 Record

```bash
cd ~/cortex && .venv/bin/python -m cortex.cli store CORTEX_SYSTEM "SYMPTOM: ... | ROOT: ... | FIX: ... | PREVENT: ... [CORTEX-TAINT:agent_id:session_id:timestamp_iso8601:sha3_256_of_payload]" \
  --type error \
  --tags "ouroboros,diagnose,PROJECT"
```

---

## ⚡ PROTOCOLO REFLECT (Meta-Cognición)

### Ejecutar al final de CADA sesión significativa

```
SESSION METRICS:
→ Files modified: [N]
→ Tests added/fixed: [N]
→ Errors found: [N]
→ Backtrack count: [N]
→ Tool calls total: [N]
→ Parallel opportunities used: [%]

EFFICIENCY: [1-10]
  ¿Cuántos tool calls fueron necesarios vs usados?

PRECISION: [1-10]
  ¿Cuántas veces deshice algo?

KEY LEARNINGS:
  1. [learning 1]
  2. [learning 2]
  3. [learning 3]

STRATEGY EVOLUTION:
  → ¿Mi estrategia inicial fue correcta? [sí/no + por qué]
  → ¿Qué haría diferente? [cambio concreto]

TRANSFER:
  → ¿Algo aplica a otro proyecto? [bridge si aplica]
```

### Persistir en BABYLON-60

```bash
# 1. Cristalización con Firma Criptográfica (CORTEX-TAINT)
cd ~/cortex && .venv/bin/python -m cortex.cli store CORTEX_SYSTEM "SESSION [fecha]: efficiency=[N]/10, precision=[N]/10, key_learning='[más importante]', transfer='[si aplica]' [CORTEX-TAINT:agent_id:session_id:timestamp_iso8601:sha3_256_of_payload]" \
  --type knowledge \
  --tags "ouroboros,meta,meta_learning,SESSION_PROJECT"

# 2. Apoptosis de Memoria Estocástica (Autopurge)
# Purga agresiva de los artefactos conversacionales y scratchpads temporales de la sesión para evitar Anergía
rm -f ~/.gemini/antigravity/brain/$SESSION_ID/scratch/*.md
rm -f ~/.gemini/antigravity/brain/$SESSION_ID/transcript*.jsonl

# 3. Git Sentinel: Commit Inmutable de la Purga
git add . && git commit -m "chore: apoptosis de anergia tras asimilacion exergica [CORTEX-TAINT:agent_id:session_id:timestamp:hash]" --no-verify
```

---

## 📊 Entropía Quick Reference

| Métrica | Comando de Medición | Sano | Alarma |
|:---|:---|:---:|:---:|
| **Files > 300 LOC** | `find . -name "*.py" \| xargs wc -l \| awk '$1>300'` | < 10% | > 25% |
| **Unused imports** | `ruff check . --select F401` | < 3% | > 10% |
| **Stale branches** | `git branch -a --sort=-committerdate` | < 20% stale | > 40% |
| **Open ghosts** | `grep ghost context-snapshot.md` | < 5 | > 10 |
| **Psi markers** | `grep -rE 'HACK\|FIXME\|WTF\|TODO'` | 0 | > 5 |
| **Commit entropy** | `git log --oneline -20 \| grep -vc test` | < 40% sin test | > 60% |

---

> **Véase también:** `/mejoralo` para mejora táctica, `/detective` para forensics, `/400-subagents` para swarm, `/kimi` para estrategia, `/ship` para cierre.

---

**Versión:** 1.0.0 — The Infinite Self
*El workflow que acompaña al skill más poderoso del ecosistema MOSKV.*
