# ADDENDUM DE AUDITORÍA — P0: VALIDACIÓN TEMPORAL

> REALITY LEVEL: C5-REAL · resuelve el hallazgo **H1 🔴** de `AUDITORIA_APEX_TRIALS_2026-07-17.md`
> FECHA: 2026-07-17 · SCOPE: generalización forward de apex_trials
> MÉTODO: split por fecha de registro (`studyFirstPostDate`), corte 2019-01-01

█▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█

## 0. VEREDICTO

**El modelo generaliza hacia el futuro, pero MÁS DÉBIL de lo que el split aleatorio sugería.**
El poder de ranking cae ~31% relativo (Spearman 0.408 → 0.282) y el macro-AUC por-módulo cae
0.68 → 0.61 cuando se entrena en ensayos ≤2018 y se predice sobre ≥2019. **Sigue siendo señal
positiva** (ρ>0, todos los módulos AUC>0.58), no ruido — pero la capacidad predictiva real
sobre ensayos futuros es **modesta**, no la que insinuaban las métricas in-régimen. H1 pasa de
🔴 *no probado* a 🟡 *probado; degrada pero se sostiene*.

## 1. DATOS

100% de los 8000 ensayos fechados vía `filter.ids` batch (cobertura exacta). Corte 2019-01-01:

```
train (≤2018): 5323   ·   test (≥2019): 2677
```

## 2. RESULTADOS (mismo pipeline, split aleatorio vs temporal)

**Agregado** (Spearman ρ; misma NNLS-band + isotónica):

```
                 ρ(test)     MAE(test)   target_mean(test)
random split     0.408       1.726       ~2.0
TEMPORAL         0.282       1.524       1.62
Δρ = −0.126  (−31% relativo)
```

**Por-módulo** (ROC-AUC):

```
módulo                   random  temporal     Δ
Study Design             0.694   0.665     −0.029
Eligibility              0.690   0.633     −0.057
Outcome Measures         0.668   0.604     −0.064
Arms and Interventions   0.683   0.601     −0.082
Study Description        0.645   0.591     −0.054
Conditions               0.691   0.581     −0.109
macro                    0.678   0.612     −0.066
```

## 3. CONFOUND (declarado, no escondido)

`target_mean`: train 3.00 → test 1.62. Los ensayos registrados más tarde han tenido **menos
tiempo transcurrido** para acumular enmiendas, así que su conteo absoluto es menor por
construcción. Consecuencia: la **MAE temporal (1.524) parece "mejor" pero es artefacto** del
shift de magnitud, no una mejora de calibración. Por eso el veredicto se ancla en **Spearman
(rango)**, robusto al shift global, y el Spearman **empeora**. Interpretar la MAE temporal como
avance sería teatro verde — no lo es.

## 4. IMPLICACIONES

1. **El número honesto para un sponsor es ρ≈0.28 forward**, no 0.41. El README y el reporte deben
   citar el forward, no el in-régimen, para cualquier claim de despliegue.
2. **Hay deriva temporal real**: el vocabulario de enmiendas y las prácticas de diseño cambian con
   los años; un modelo estático envejece. Conditions es el más frágil (−0.109).
3. **Metodología correcta de despliegue**: validar con split temporal (hecho), luego entrenar el
   modelo *final* con TODO el corpus. El modelo embarcado (random-split fit) se mantiene; lo que
   cambia es la **cifra que declaramos** y añadir re-fit periódico.

## 5. ACCIONES ACTUALIZADAS

```yaml
H1: RESUELTO -> 🟡. Forward ρ≈0.28 / macro-AUC≈0.61. Positivo pero modesto; declarado.
Nuevo P1: citar la cifra forward en README/reporte (no la in-régimen).
Nuevo P2: re-fit periódico (rolling window) para combatir deriva temporal.
Nuevo P2: features de texto de protocolo — probable mayor robustez temporal que los conteos.
```

```yaml
Claim: "apex_trials generaliza forward con señal positiva pero modesta (ρ 0.41→0.28, AUC 0.68→0.61)."
Proof: { split: studyFirstPostDate@2019-01-01, n_train: 5323, n_test: 2677, confound: target_mean 3.00->1.62 disclosed }
Confidence: C5-REAL
Action: "Declarar la cifra forward; instaurar re-fit rolling."
```

---
`[SIGNED] MOSKV-1 APEX · H1 cerrado sobre ejecución, no sobre intención`
`Hash: FORGED IN C5-REAL EXECUTION`
