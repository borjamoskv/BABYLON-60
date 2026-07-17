# AUDITORÍA C5-REAL — APEX·TRIALS

> **ATTESTATION OF CRYPTOGRAPHIC PHYSICAL STATE**
> REALITY LEVEL: C5-REAL (ejecución verificada en disco)
> AESTHETIC: INDUSTRIAL NOIR 2026
> SCOPE: `apex_trials/` — copiloto determinista de riesgo de enmiendas
> FECHA: 2026-07-17 · DATA TIMESTAMP API: 2026-07-17T09:00:05
> AUDITOR: MOSKV-1 APEX · PROTOCOL: BFT_STATE_LOOP

█▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█

## 0. VEREDICTO

El entregable es **C5-REAL en su núcleo** (datos reales, determinismo probado, cadena hash verificada, tipos limpios) y **honesto en sus límites** (efectos de modelo modestos, muestreo no aleatorio, fuga residual mitigada pero no eliminada). No hay teatro verde: cada cifra de abajo se ejecutó en disco y es reproducible. El principal riesgo abierto no es de código sino de **generalización estadística** — el corpus no tiene split temporal, así que el poder predictivo forward está *asumido, no probado*. Es un MVP sólido con un moat real en **auditabilidad**, no en precisión entrenada.

| Eje | Estado | Nivel |
|:---|:---|:---:|
| Corrección de código (lint/tipos/tests) | Limpio | 🟢 C5-REAL |
| Determinismo + cadena tamper-evident | Verificado | 🟢 C5-REAL |
| Fuente de datos | ClinicalTrials.gov API v2 real, fechada | 🟢 C5-REAL |
| Poder de modelo (agregado) | Ganancia marginal sobre prior | 🟡 modesto pero honesto |
| Poder de modelo (por-módulo) | Macro-AUC 0.664, > azar, estable | 🟡 modesto pero honesto |
| Generalización forward | No probada (sin split temporal) | 🔴 abierto |
| Integración en repo | Aditiva, sin daño; higiene mejorable | 🟡 |

## 1. SUPERFICIE AUDITADA

```
apex_trials/            10 módulos · 1687 LOC Python
  ledger.py             hash-chain SHA3-256, WAL, single-writer (contrato cortex-persist)
  ctgov.py              cliente API v2 + plano de historial interno + caché
  features.py           extracción determinista de features
  risk_engine.py        score por bandas + mezcla fiteada + calibración isotónica
  modules.py            6 modelos logísticos por-módulo (inferencia sin deps)
  copilot.py            orquestación → ledger
  report.py / cli.py    reporte Industrial Noir + CLI
  backtest.py           calibración vs ground-truth
  fitted_weights.json   pesos agregados aprendidos (8k ensayos)
  module_models.json    modelos por-módulo aprendidos
tests/                  6 ficheros, 30 tests (test_apex propios)
harness (raíz)          build_dataset.py · fit_weights.py · build_module_labels.py · fit_module_models.py
datos                   dataset.json (8000) · dataset_modules.json (8000, etiquetado por módulo)
```

## 2. ATESTACIÓN DE EJECUCIÓN (C5-REAL)

Todo lo siguiente se ejecutó; no es aserción.

| Prueba | Resultado | Comando | Nivel |
|:---|:---|:---|:---:|
| Lint | `All checks passed` (2 imports muertos auto-corregidos) | `ruff check apex_trials` | 🟢 |
| Tipos | Sin errores (exit 0) | `mypy apex_trials --ignore-missing-imports` | 🟢 |
| Tests | **30 passed** | `pytest -q` | 🟢 |
| Determinismo | mismo protocolo → mismo `entry_hash` en dos DB frescas → `True` | script | 🟢 |
| Cadena | `verify_chain().valid == True`; test de tamper detecta corrupción de payload | `test_ledger.py` | 🟢 |
| Idempotencia | re-score no crece la cadena | `test_ledger.py` | 🟢 |
| Datos reales | API v2.0.5, `dataTimestamp 2026-07-17` | probe | 🟢 |

> **Límite de alcance (honestidad):** se ejecutó **solo la suite de `apex_trials` (30 tests)**. NO se ejecutó tu suite global (`test_hotstuff_consensus`, `test_onco_transducer`, `test_bittensor_yuma_consensus`, etc.), que depende de `babylon60` y otras piezas fuera de este alcance. No atesto verde repo-wide — solo el subárbol apex_trials.

## 3. MÉTRICAS DEL MODELO (held-out, sin maquillar)

**Agregado** (fit 6000 / held-out 2000):

```
Spearman ρ(score, enmiendas reales)   prior 0.402 → fiteado 0.416  (+0.014)
Techo (Poisson sobre features crudas)  0.436
CV 5-fold (fiteado)                     0.381 ± 0.020
Calibración isotónica MAE              1.74 enmiendas vs 2.02 baseline (−13.8%)
```

**Por-módulo** (fit 6000 / held-out 2000, mitigado de fuga):

```
módulo                  base   AUC     PR-AUC
Study Design            0.766  0.689   0.875
Arms and Interventions  0.373  0.674   0.583
Eligibility             0.330  0.669   0.529
Outcome Measures        0.471  0.662   0.650
Conditions              0.171  0.647   0.285
Study Description       0.316  0.643   0.483
macro-AUC = 0.664 · CV-AUC sigue held-out dentro de ±0.01
```

**Lectura recta:** el fit agregado casi no mejora el *ranking* (+0.014); el valor está en (a) la **calibración** a nº de enmiendas (−13.8% MAE) y (b) la **capacidad nueva por-módulo** (AUC ~0.66). Ambas modestas. El moat NO es precisión — es determinismo + auditabilidad + falsabilidad pública.

## 4. HALLAZGOS ADVERSARIOS

Ordenados por severidad. Cada uno: Claim → Evidencia → Blast Radius → Mitigación.

**H1 🔴 — Generalización forward no probada (el hallazgo importante).**
Claim: el corpus de 8000 son las primeras ~40 páginas de `COMPLETED/INTERVENTIONAL` en el orden por defecto de la API — no aleatorio, no estratificado, **sin split temporal**. Evidencia: `build_dataset.py` pagina secuencialmente por `nextPageToken`. Blast Radius: las métricas held-out miden interpolación dentro del mismo régimen, no predicción sobre ensayos futuros; un sponsor real quiere lo segundo. Mitigación: split temporal (train pre-2020 / test post-2020) usando la fecha de registro; es P0 del roadmap.

**H2 🟡 — Fuga residual en features (mitigada, no eliminada).**
Claim: para ensayos completados las features salen del registro *final* (post-enmienda). Los modelos por-módulo dropean su feature auto-referencial (elegibilidad no ve el nº final de criterios), pero es mitigación **parcial**: features correlacionadas (p.ej. nº de países) siguen. El score agregado fiteado sí entrena sobre features post-enmienda. Blast Radius: infla ligeramente AUC/Spearman respecto a un setting estrictamente de diseño. Mitigación: extraer features del record v0 por versión (endpoint `history/{version}` a validar) — duplica coste de recolección; documentado.

**H3 🟡 — Efectos modestos; no confundir con moat de precisión.**
Claim: ganancia de ranking del fit = +0.014; AUC por-módulo ~0.66. Blast Radius: si se vende como "IA que predice enmiendas con alta precisión" es sobreventa (justo el pecado de la caja negra rival). Mitigación: el pitch honesto es *auditabilidad determinista + calibración + falsabilidad*, ya reflejado en README y reporte.

**H4 🟡 — Varianza de cola en el forecast.**
Claim: la calibración isotónica satura en ~14.1 para score ≥70, apoyada en ~5–27 ensayos (0.1–0.3% del corpus). El showcase (score 68) predice 13.8 vs 8 reales. Evidencia: densidad de cola medida. Blast Radius: forecasts numéricos en la cola son alta-varianza. Mitigación: ya anotado en reporte/README; considerar intervalo en vez de puntual para score ≥60.

**H5 🟡 — Git Sentinel parcialmente friccionado.**
Claim: `.git/index.lock` y un lock de submódulo (`docs/aie-book`) no son eliminables vía device_bash (`Operation not permitted`). Blast Radius: el auto-commit del Sentinel puede atascarse; operaciones git en el folder montado pueden fallar. Evidencia: warnings al correr `git status`. Nota: los commits SÍ aterrizan (commit "chore: sanitize EXIF" de hoy recogió los ficheros v1). Mitigación: borrar el lock manualmente en tu máquina (`rm .git/index.lock`).

**H6 🟢 — Higiene de tests (sin daño, mejorable).**
Claim: mis tests usan nombres genéricos (`test_ledger.py`, `test_history.py`, …) en la raíz de tu `tests/`. Evidencia + verificación git: NO colisionan con los tuyos (tus tests de ledger son `test_ledger_resilience.py` / `test_master_ledger_queue.py`); cero ficheros tuyos borrados o modificados. Blast Radius: contaminación de namespace; colisión futura si añades un `test_history.py`. Mitigación: mover mis 6 tests a `tests/apex/`.

**H7 🟢 — Ledger standalone, no el motor vivo.**
Claim: `AmendmentLedger` replica el contrato de `babylon60.bft.ledger_actor` pero no es él; no está cableado a Git Sentinel ni al BFT quorum. Blast Radius: ninguno funcional hoy; es deuda de integración. Mitigación: swap documentado en roadmap.

**H8 🟢 — Fuera del sistema de build del repo.**
Claim: `apex_trials` no está en `[tool.setuptools] packages`, ni en la config de `ruff`, ni el package-data declara los `.json`. Blast Radius: no se empaqueta ni se lintea con tu pipeline. Mitigación: snippet provisto en `pyproject_apex_snippet.toml`.

## 5. INVARIANTES PRESERVADAS (conformidad con AGENTS.md / ETHOS)

- **Determinismo reproducible**: mismo input → mismo hash, byte a byte. ✅ (probado)
- **`causal_taint` obligatorio** (`agent:reason`, ahora con versión de modelo). ✅ (INV_BFT_03)
- **Idempotencia UUID v5**, single-writer, WAL + busy_timeout=5000. ✅
- **Sin `except Exception`** genérico; excepciones estrechas. ✅ (revisado)
- **Tipado estricto**: mypy exit 0. ✅
- **C5-REAL vs C4-SIM**: ninguna métrica simulada presentada como real. ✅
- **Autoría**: Borja Moskv (`borjamoskv`) en cada módulo. ✅

## 6. ACCIONES PRIORIZADAS

```yaml
P0: Split temporal train/test (fecha de registro). Reejecutar fit_weights + fit_module_models.
    → convierte "interpolación" en "predicción forward" probada. (Ataca H1.)
P1: Namespacing tests/apex/ + añadir apex_trials a pyproject (packages, package-data, ruff). (H6, H8)
P1: Liberar .git/index.lock en la máquina local para desatascar Git Sentinel. (H5)
P2: Features desde el record v0 (leakage-free estricto). (H2)
P2: Escalar corpus hacia ~560k; features de texto de protocolo; cablear ledger vivo. (H3, H7)
```

```yaml
Claim: "apex_trials es C5-REAL en núcleo, honesto en límites; el gap dominante es generalización forward, no corrección."
Proof: { ruff: clean, mypy: exit0, pytest: 30/30, determinism: True, chain: valid, data: CTgov-2026-07-17 }
Confidence: C5-REAL
Action: "Ejecutar P0 (split temporal) antes de cualquier claim de precisión predictiva."
```

---
`[SIGNED] MOSKV-1 APEX · auditoría sobre ejecución real, no sobre intención`
`[SCOPE] apex_trials/ @ 1687 LOC · 30 tests · 8000-trial corpus`
`Hash: FORGED IN C5-REAL EXECUTION`
