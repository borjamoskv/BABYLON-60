# 🧮 PROOF — Axiomatic Specification in Lean 4

> **DOMINIO DE VERIFICACIÓN FORMAL**  
> El directorio `proof/` contiene la **especificación axiomática** en Lean 4 de las propiedades de seguridad de BABYLON-60.

---

## ⚠️ Estado Formal Honesto (audit 2026-09-10)

> [!IMPORTANT]
> **Esto es un esbozo axiomático, no verificación formal completa.**
> - Las propiedades fundamentales se declaran como `axiom` (asunciones), no como `theorem` demostrados desde premisas básicas.
> - Los teoremas existentes son corolarios directos de los axiomas (`exact axiom`).
> - El archivo compila con `lake build` sin `sorry` — pero esto se logra axiomatizando las propiedades, no demostrándolas.
> - La verificación formal completa (convertir axiomas en teoremas sobre tipos concretos como `Rat`/`Nat`) es un objetivo de roadmap.

---

## 📐 Contenido Actual (`proof/lean/`)

### Fichero compilable: [`Babylon.lean`](./lean/Babylon.lean)

| Métrica | Valor |
|:---|:---|
| **Líneas de código** | ~170 |
| **Axiomas (`axiom`)** | 7 (ax_bd_1..4, ax_tz_1..3) |
| **Teoremas (`theorem`)** | 3 (corolarios directos de axiomas) |
| **`sorry` activos** | 0 ✅ |
| **Build system** | Lake (Lean 4) |

### Módulos Formalizados

| Dominio | Axiomas | Descripción |
|:---|:---|:---|
| **Desintegración Bayesiana** | ax_bd_1..4 | Simetría conjunta, no-alucinación, circuit breaker, resiliencia BFT |
| **Monitor Tonnetz** | ax_tz_1..3 | Homeostasis tríadica, degradación termodinámica, alerta de anergía |

### Ficheros adicionales en `docs/proof/lean/`

Se mantienen ~11 ficheros Lean adicionales de exploración en `docs/proof/lean/` (BabylonTrace, C5Real/, OncologyOntology). Estos son sketches experimentales, no parte del build principal.

---

## 🛤️ Roadmap de Verificación Formal

1. **Fase actual (Nivel 1 — Axiomatic Sketch):** Propiedades declaradas como axiomas, type-checked, zero `sorry`. ✅
2. **Fase 2 (Nivel 2 — Partial Verification):** Reescribir axiomas sobre `Rat`/`Nat` (no `Float`) y demostrar los que sean demostrables. Mantener como axiomas explícitos los que requieran asunciones de dominio.
3. **Fase 3 (Nivel 3 — Full Verification):** Anclaje a Mathlib, demostración de todas las propiedades de seguridad del ledger (append-only, hash-chain integrity, Lamport ordering).

---

## ⚙️ Compilación

```bash
cd proof/lean
lake build
```

Si `lake build` termina sin errores, el esbozo axiomático es sintácticamente válido y libre de `sorry`.
