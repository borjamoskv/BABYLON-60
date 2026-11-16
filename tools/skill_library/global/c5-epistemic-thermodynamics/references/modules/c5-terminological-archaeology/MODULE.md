---
name: c5-terminological-archaeology
display_name: Arqueología Terminológica (Anagnórisis Conceptual C5-REAL)
description: "Cruza perífrasis con literatura primaria y registra términos canónicos en el léxico C5. Dispara con \"arqueología terminológica\", \"busca mis perífrasis\", \"anagnórisis\", \"ya existe ese término\", \"tiene nombre esto\", \"cómo se llama esto en ciencia\", \"cómo se llama cuando\"."
role: auditor
allowed_roles:
  - auditor
  - arquitecto
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: operador
    downstream: notario
---

# C5 Terminological Archaeology — Anagnórisis Conceptual

> **Directiva Declarativa:**
> - **Rol Asignado:** `auditor` (Auditoría de sesiones + cruce bibliográfico + registro léxico)
> - **Modo de Acceso a Worktree:** `audit-only` (solo lectura de transcripts y skills; escritura
>   exclusivamente en `~/.gemini/config/C5_LEXICON.json` y `c5-lexicon-enforcer/SKILL.md`)
> - **Fase Causal:** `verification`

## Misión (Directriz Cero)

Convertir el fenómeno accidental de *anagnórisis terminológica* (descubrir que ya existe
un término canónico para una intuición propia) en un **proceso activo, sistemático y
continuo**. El operador biológico de alta exergía opera como antena transductora:
detecta invariantes físicas antes de conocer su nombre formal. Este equipo completa el
circuito al identificar y registrar esas correspondencias.

## Disparadores

```
arqueología terminológica
busca mis perífrasis
anagnórisis
ya existe ese término
tiene nombre esto
cómo se llama esto en ciencia
cómo se llama cuando
busca el término para
¿hay palabra para
```

## Pipeline de 4 Agentes (Ejecución en Cadena)

```
[Sesión / Transcripts]
        │
        ▼
[A1: EXCAVADOR] — c5_orphan_phrase_detector.py
  Detecta perífrasis sistémicas huérfanas ≥7 palabras
  que describen mecanismos sin usar término técnico de raíz.
  → candidatos.jsonl
        │
        ▼
[A2: MAPEADOR] — c5_canonical_term_mapper.py
  Cruza candidatos contra:
    1. C5_LEXICON.json (BM25 Jaccard local)
    2. Wikipedia API en + es
    3. Semantic Scholar API (gratuita)
  → mapeos.jsonl
        │
        ▼
[A3: LINTER DIFERENCIAL] — c5_delta_boundary_linter.py
  Veredicto: CONVERGE / DIVERGE / SUPERSET / NO_MATCH
  Cuantifica coverage y extrae delta (lo que Borja añade de nuevo)
  → delta.jsonl
        │
        ▼
[A4: NOTARIO] — c5_lexicon_notary.py
  Escribe en C5_LEXICON.json + Fase 2f del lexicon-enforcer
  → ANAGNORISIS_LOG.md
```

## Protocolo de Ejecución Completo

### Modo A: Análisis de sesión activa (disparador manual)

Cuando el operador usa el trigger, ejecutar el pipeline completo sobre la sesión actual:

```bash
SKILL_DIR=../../../../c5-terminological-archaeology/scripts
BRAIN_DIR=~/.gemini/antigravity/brain
SINCE=$(date -v-30d +%Y-%m-%d)  # Últimos 30 días

cd /tmp/c5_archaeology_$(date +%s)

# A1: Excavar
python3 $SKILL_DIR/c5_orphan_phrase_detector.py \
  --session-dir $BRAIN_DIR \
  --since $SINCE \
  --output candidatos.jsonl

# A2: Mapear
python3 $SKILL_DIR/c5_canonical_term_mapper.py \
  --input candidatos.jsonl \
  --output mapeos.jsonl

# A3: Lintear
python3 $SKILL_DIR/c5_delta_boundary_linter.py \
  --input mapeos.jsonl \
  --output delta.jsonl

# A4: Notarizar
python3 $SKILL_DIR/c5_lexicon_notary.py \
  --input delta.jsonl \
  --artifact-dir $ARTIFACT_DIR
```

### Modo B: Análisis de texto inline (modo rápido)

Cuando el operador pega una descripción larga de un fenómeno:

```bash
python3 $SKILL_DIR/c5_orphan_phrase_detector.py \
  --input "DESCRIPCIÓN DEL OPERADOR AQUÍ" > /tmp/candidatos.jsonl

python3 $SKILL_DIR/c5_canonical_term_mapper.py \
  --input /tmp/candidatos.jsonl > /tmp/mapeos.jsonl

python3 $SKILL_DIR/c5_delta_boundary_linter.py \
  --input /tmp/mapeos.jsonl

# El agente interpreta los resultados y presenta al operador
```

### Modo C: Registro manual directo

Cuando el operador descubre directamente un término:

```bash
python3 $SKILL_DIR/c5_lexicon_notary.py \
  --term "Nombre Canónico" \
  --intuition "Cómo lo describía Borja antes" \
  --author "Apellido" \
  --year YYYY \
  --work "Obra seminal" \
  --dry-run  # Verificar antes de escribir
```

## Estructura de Salida Obligatoria

Tras ejecutar el pipeline completo, presentar al operador:

### 1. Resumen de Candidatos Detectados
Lista de perífrasis huérfanas encontradas con su tipo de señal.

### 2. Correspondencias Canónicas
Para cada candidato con veredicto CONVERGE:
- **Término Canónico:** [nombre]
- **Autor / Año / Obra:** [referencia]
- **Disciplina:** [área]
- **Tu descripción original:** [frase excavada]
- **Coverage:** [porcentaje]

### 3. Deltas Identificados (SUPERSET o DIVERGE)
Lo que la intuición de Borja añade más allá del término canónico — candidato a
bautismo como término nuevo o extensión de C5-REAL.

### 4. Confirmación de Registro
Confirmar que los términos han sido escritos en `C5_LEXICON.json` y que la
`Fase 2f` del `lexicon-enforcer` ha sido actualizada.

## Invariantes del Equipo

1. **Nunca inventar ni confabular** un término canónico. Si no existe en las 3 fuentes,
   el resultado es `NO_MATCH` y se encola como candidato potencialmente nuevo.
2. **Flash-Defense activa:** Toda referencia bibliográfica (autor, año, obra) debe
   verificarse contra una fuente externa antes de registrarse en el lexicón.
3. **Escritura atómica:** El Notario solo escribe en `C5_LEXICON.json` y
   `c5-lexicon-enforcer/SKILL.md`. Nunca en `10_PROJECTS/`, `20_VAULT/`, `BABYLON-60` ni `scratch/`.
4. **No sobreescribir entradas de alta calidad:** Si un término ya está en el lexicón
   con `coverage >= 0.90`, el registro se omite (idempotente).
5. **Dry-run obligatorio** en el primer uso de cada sesión.
