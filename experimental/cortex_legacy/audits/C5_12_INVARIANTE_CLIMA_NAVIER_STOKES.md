# C5_12 — INVARIANTE CAUSAL DEL CLIMA: HORIZONTE DE LYAPUNOV

**Nivel de realidad (EPI_01):** experimento y aritmética = C5-REAL, ejecutados y consolidados en disco (`C5_12_resultados.json`, `C5_12_divergencia.npz`, `C5_12_lyapunov_ns2d.png`). La spec planetaria ("Navier-Stokes aniquilado") = **FALSADA**: no ejecutada porque es inejecutable — por cualquier sistema, humano o máquina, con la física conocida. No es un límite de política ni de este kernel; es un límite del universo.
**Kernel (EPI_05):** claude-fable-5. Fecha: 2026-07-14.

---

## 1. DEFINICIÓN

La spec exige: (a) simular la atmósfera completa a 1 m³, (b) "anular la aleatoriedad" de la turbulencia, (c) predicción determinista perfecta **y reversible**. Las tres cláusulas chocan con muros independientes. El invariante causal que SÍ existe y fue medido: la divergencia entre trayectorias gemelas de Navier-Stokes crece como e^{λt}, y el horizonte de predicción es **logarítmico** en la precisión inicial:

> **t_hor = λ⁻¹ · ln(D_sat / ε₀)**

## 2. CRASH CAUSAL DE LA SPEC — CUATRO MUROS (aritmética verificada por doble vía)

| Muro | Magnitud | Déficit |
|---|---|---|
| **RAM** | 1.02·10¹⁹ celdas × 8 vars × 8 B = **653 EB** solo de estado | 1.2·10⁵× la RAM del mayor supercomputador (~5.4 PB) |
| **Throughput** | CFL a 1 m: Δt=2.5 ms → 3.5·10²⁹ flop/día simulado | **5 595 años de muro por día simulado** a 2 EF/s → 2·10⁶× más lento que el tiempo real |
| **Resolución** | Escala de Kolmogorov η ≈ 0.76 mm → DNS real = 2.3·10²⁸ celdas | a 1 m³ faltan **9 órdenes**: el cierre subgrid es obligatorio y el "azar anulado" reaparece como error de modelo |
| **Información** | 10¹⁹ incógnitas iniciales vs ≤10⁹ observaciones/día | estado inicial subdeterminado **10¹⁰×** |

## 3. CRASH CAUSAL DEL OBJETIVO — POR QUÉ "ANULAR EL CAOS" ES CATEGORÍA ERRÓNEA

1. **No hay aleatoriedad que anular.** Navier-Stokes ya es determinista. La turbulencia es caos determinista (Lorenz 1963; Ruelle–Takens). El obstáculo no es el azar: es λ > 0.
2. **El horizonte es logarítmico, no lineal.** Cada 10× de precisión inicial compra solo log₂10 ≈ 3.32 doblajes (~5.6 días con T₂ sinóptico ≈ 1.7 d). Medido en §4 con R² = 0.9993.
3. **Piso térmico.** La fluctuación molecular de densidad en 1 m³ de aire es 2·10⁻¹³ (N⁻¹ᐟ², N≈2.5·10²⁵). Ninguna condición inicial puede ser más precisa que eso: techo mono-escala = 42 doblajes ≈ **72 días**. La cascada multiescala de error (Lorenz 1969: los errores crecen con el T₂ rápido de las escalas pequeñas y ascienden) lo colapsa a **~15 días** — límite intrínseco, independiente del hardware (Zhang et al. 2019).
4. **"Reversible" viola la Segunda Ley que la propia spec invoca.** Disipación viscosa atmosférica ≈ 2 W/m² → producción de entropía > 0. Integrar NS hacia atrás = difusión negativa: mal puesta, el modo k se amplifica e^{νk²t}. Determinista sí; reversible no.
5. **Regularidad 3D abierta.** No existe demostración de existencia global suave (problema del milenio, Clay). Nadie puede certificar que la simulación no encuentra singularidad.

## 4. LO EJECUTADO (C5-REAL): EXPERIMENTO GEMELO NS-2D

Solver pseudo-espectral en vorticidad, 64², RK4, dealiasing 2/3, ν=10⁻⁴, determinista bit a bit (semilla 1905). Dos estados idénticos salvo perturbación única de 10⁻¹⁰ tras spin-up al atractor. Wall: 3.3 s.

| Métrica | Valor |
|---|---|
| Exponente de Lyapunov λ | **0.1760 ± 0.0003** (t⁻¹ del modelo) |
| R² del fit (326 puntos) | 0.9993 |
| Fit en mitades disjuntas | 0.184 / 0.172 (consistente, ±7%) |
| Tiempo de doblaje T₂ = ln2/λ | 3.94 |
| Crecimiento observado | 8·10⁻¹¹ → 1.5·10⁻⁸ en t∈[0,26], exponencial limpio |

Notas de honestidad: (i) 2D, sin estiramiento de vórtices — instancia legítima de NS caótico, no proxy cuantitativo de la atmósfera 3D; el mapeo a días usa el T₂ sinóptico de literatura (1.5–2 d), no este λ. (ii) La saturación no se alcanzó en ventana; D_sat := 1 por convención de error relativo O(1). (iii) La divergencia proviene únicamente de la perturbación inyectada: mismo binario, misma semilla, mismas operaciones.

## 5. DILEMAS / TRADE-OFFS

| Dilema | Opción A | Opción B | Resolución causal |
|---|---|---|---|
| Resolución vs cierre | DNS (2.3·10²⁸ celdas) | LES 1 m³ + subgrid | Ambas inviables o con error de modelo irreducible |
| Precisión vs horizonte | +10× precisión | +3.32 doblajes | Ganancia logarítmica; piso térmico a 2·10⁻¹³ |
| ν>0 vs ν=0 | Disipativo, irreversible | Euler "reversible" | Disipación anómala (Onsager): ε>0 incluso en ν→0 |
| Determinismo vs predictibilidad | NS es determinista | Horizonte finito ~15 d | λ>0 desacopla ambos: el invariante es el horizonte, no la trayectoria |

## 6. VEREDICTO

🔴 Spec original: imposible físicamente (muros §2) y conceptualmente mal planteada (§3).
🟢 Invariante causal real del clima, medido y en disco: **t_hor = λ⁻¹ ln(D_sat/ε₀)** — el determinismo no compra predictibilidad; compra una ley de horizonte.

## 7. FUENTES PRIMARIAS

- Lorenz, E. N. (1963). *Deterministic Nonperiodic Flow.* https://journals.ametsoc.org/view/journals/atsc/20/2/1520-0469_1963_020_0130_dnf_2_0_co_2.xml
- Lorenz, E. N. (1969). *The predictability of a flow which possesses many scales of motion.* Tellus 21. https://onlinelibrary.wiley.com/doi/10.1111/j.2153-3490.1969.tb00444.x
- Zhang, F. et al. (2019). *What Is the Predictability Limit of Midlatitude Weather?* J. Atmos. Sci. 76. https://journals.ametsoc.org/view/journals/atsc/76/4/jas-d-18-0269.1.xml
- Clay Mathematics Institute, *Navier–Stokes Existence and Smoothness.* https://www.claymath.org/millennium-problems/
