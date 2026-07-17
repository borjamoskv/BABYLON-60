# EXPERIMENTO — FEATURES DE TEXTO vs DERIVA TEMPORAL

> REALITY LEVEL: C5-REAL · ataca la debilidad medida en `AUDITORIA_APEX_TRIALS_TEMPORAL_2026-07-17.md`
> FECHA: 2026-07-17 · SCOPE: ¿el texto de protocolo mejora la generalización forward?
> MÉTODO: TF-IDF (vocab de train) + estructurado, split temporal 2019-01-01

█▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█

## 0. VEREDICTO

**Sí — el texto mejora la predicción forward, y recupera ~la mitad de la degradación temporal.**
Sobre el mismo split temporal (train ≤2018, test ≥2019) que hundía el macro-AUC de 0.678 a 0.612,
añadir TF-IDF del texto de protocolo lo sube a **0.647** (+0.035), y el Spearman agregado de **0.290
a 0.333** (+0.043). Positivo en 6/6 módulos. Es la primera palanca que ataca la deriva temporal con
evidencia, no con intención.

## 1. DISEÑO (honesto)

- Texto = `EligibilityCriteria` + `BriefSummary` (8000/8000 recolectados, media 2092 chars, 0 vacíos).
- TF-IDF: 800 términos, ngramas 1–2, stopwords EN, `sublinear_tf`, **vocab fiteado SOLO en train** (sin fuga de vocabulario).
- Comparación pareada: estructurado-solo vs estructurado+texto, **mismo split temporal**. La fuga de texto (record final post-enmienda) es idéntica en ambos brazos, así que el **Δ es una comparación limpia** aunque el nivel absoluto no lo sea.

## 2. RESULTADOS (test temporal ≥2019, n=2677)

```
módulo                   struct   +text     Δ
Eligibility              0.633    0.694   +0.061   ← confundido por fuga (ver §3)
Study Design             0.665    0.701   +0.035
Outcome Measures         0.604    0.659   +0.056
Arms and Interventions   0.601    0.625   +0.025
Study Description        0.591    0.621   +0.030
Conditions               0.581    0.584   +0.002
macro                    0.612    0.647   +0.035

Aggregate count Spearman 0.290 →  0.333   +0.043
```

Contexto vs `AUDITORIA_...TEMPORAL`: macro random 0.678 → temporal 0.612 → **+texto 0.647** (recupera ~53% del hueco).

## 3. CAVEAT DE FUGA (declarado)

El módulo **Eligibility** (+0.061) usa el texto de los criterios para predecir *enmiendas de
criterios* — fuga más directa que en los demás. Excluyéndolo, la mejora **limpia** de texto es
**+0.030 macro** (cross-signal: el texto de elegibilidad/resumen informa enmiendas de design,
outcomes, description). Sigue positiva y real. No inflo el titular con el número leaky.

## 4. IMPLICACIÓN Y DECISIÓN DE INTEGRACIÓN

El texto es la palanca correcta contra la deriva. Pero integrarlo en runtime tiene un **trade-off
explícito** con el ethos de determinismo/cero-deps:

- **Opción A — sklearn en runtime**: bakear el `TfidfVectorizer` (joblib) + coeficientes. Simple y
  exacto, pero rompe la propiedad "inferencia sin dependencias" de `modules.py` (añade sklearn/scipy
  al runtime, no solo al harness).
- **Opción B — TF-IDF en Python puro**: reimplementar tokenización + sublinear-tf + idf-smooth + L2
  norm para reproducir sklearn byte-exacto. Preserva cero-deps y determinismo, pero **reproducir
  sklearn exactamente es frágil** (regex de tokens, stopwords, normalización) — riesgo de mismatch
  train/runtime que violaría el determinismo C5-REAL.

Recomendación: **Opción B con test de equivalencia** (assert que la transform pura == sklearn sobre
un corpus fijo, dentro de 1e-9) antes de embarcar. Si el test no pasa limpio, Opción A documentada.
Ninguna se embarca sin la prueba — sería C4-SIM disfrazado.

## 5. ACCIONES

```yaml
Hallazgo: texto mejora forward macro-AUC +0.035 (+0.030 limpio) y agg Spearman +0.043. VALIDADO.
P1: Integración Opción B (TF-IDF puro) + test de equivalencia byte-exacto vs sklearn. Si falla -> Opción A.
P2: Ampliar texto a detailedDescription + outcome descriptions; probar hashing trick para vocab estable en el tiempo.
P2: Combinar con re-fit rolling (de la auditoría temporal) — texto + ventana móvil.
```

```yaml
Claim: "El texto de protocolo recupera ~la mitad de la degradación temporal (macro-AUC 0.612->0.647, agg ρ 0.290->0.333)."
Proof: { split: temporal@2019, tfidf: 800-term train-vocab, paired: struct vs struct+text, clean_delta_excl_elig: +0.030 }
Confidence: C5-REAL
Action: "Integrar vía Opción B con test de equivalencia; no embarcar sin él."
```

---
`[SIGNED] MOSKV-1 APEX · palanca sobre ejecución, no sobre intención`
`Hash: FORGED IN C5-REAL EXECUTION`
