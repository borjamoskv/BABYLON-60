---
title: "Dilemas de coordinación extractiva (Moloch) y micro-economía de balance de Landauer"
status: Formalizado-en-Lean4-Core
version: 1.0.0
---

# Dilemas de coordinación extractiva (Moloch) y micro-economía de balance de Landauer

Revisión: 2026-10-24. Formalización neurosimbólica en Lean 4 Core de la detección computable de dinámicas extractivas multi-agente (anti-Moloch) y su neutralización mediante internalización de costes de disipación de Landauer.

## 1. Desmitificación Epistémica: Del Ensayo a la Termodinámica Causal

En la literatura de racionalismo contemporáneo (LessWrong, *Meditations on Moloch*, Alexander, 2014), el concepto de «Moloch» se utiliza como metáfora literaria de la Tragedia de los Comunes, las carreras armamentísticas y los equilibrios de Nash Pareto-ineficientes. En esos ensayos, la coordinación falla porque los agentes carecen de un mecanismo para hacer cumplir compromisos creíbles en presencia de incentivos de defección miopes.

En BABYLON-60, esta dinámica se despoja de retórica mitológica y se formaliza como una **asimetría termodinámica de externalidades en un sustrato compartido**:
- Una acción es puramente extractiva ($\text{Moloch}$) si el beneficio privado reclamado $U_{\text{claim}} > 0$ se obtiene inyectando una degradación entrópica en el sustrato compartido estrictamente mayor que el coste disipativo que el agente asume internamente:
  $$\Delta S_{\text{externalized}} > \Delta S_{\text{internal}}$$
- En arquitecturas de cómputo en memoria compartida (SPSC, Seqlocks, buffers de mensajería), la entropía externalizada se manifiesta físicamente como contención de caché (RFO), sobreescritura destructiva de memoria, latencia inducida y consumo de colateral de red.

## 2. Micro-Economía de Balance de Landauer

El principio físico de Landauer establece que el borrado irreversible o la corrupción de un bit de información en un sistema térmico disipa un mínimo de energía:
$$Q_{\text{min}} = k_B T \ln 2$$

Para neutralizar el incentivo de extracción sin recurrir a autoridades centrales benevolentes ni a supuestas coordinaciones "acausales" (TDT/UDT):
1. **Gravamen de Landauer:** El protocolo de admisión de BABYLON-60 exige a cada agente un colateral exérgico $E_{\text{tax}}$. Si la acción es clasificada como extractiva ($\text{is\_moloch\_extraction}$), el gravamen retiene la totalidad de la entropía externalizada más el beneficio bruto reclamado:
   $$E_{\text{tax}} = \Delta S_{\text{externalized}} + U_{\text{claim}}$$
2. **Extinción del Incentivo:** El payoff neto del agente tras la mediación del balance colapsa idénticamente a cero:
   $$\text{Payoff}_{\text{net}} = U_{\text{claim}} - (\Delta S_{\text{internal}} + E_{\text{tax}}) = 0 \quad (\text{en } \mathbb{N})$$
3. **Dominancia de Pareto:** La cooperación constructiva (con externalidad nula o negativa y beneficio superior al coste interno) preserva un payoff estrictamente positivo, convirtiendo a la cooperación en la estrategia estrictamente dominante.

## 3. Especificación Formal en Lean 4 Core

La especificación e implementación canónica reside en [`proof/lean/MolochLandauer.lean`](../../proof/lean/MolochLandauer.lean).

### 3.1. Primitivas y Detector Computable
```lean
inductive ActionClass where
  | Constructive
  | Neutral
  | Extract
  | Apoptosis
deriving Repr, BEq, DecidableEq

structure AgentAction where
  agent_id : Nat
  action_class : ActionClass
  claimed_benefit : Nat
  internal_dissipation : Nat
  externalized_entropy : Nat
deriving Repr, BEq, DecidableEq

def is_moloch_extraction (a : AgentAction) : Bool :=
  match a.action_class with
  | .Extract =>
    (a.claimed_benefit > 0) && (a.externalized_entropy > a.internal_dissipation)
  | _ => false
```

### 3.2. Teoremas Constructivos Demostrados
Bajo `set_option warningAsError true` y sin dependencias no constructivas (`Classical.choice` ausente):

1. **`moloch_payoff_is_zero`:**
   $$\forall a, \text{is\_moloch\_extraction}(a) = \text{true} \implies \text{net\_exergy\_payoff}(a) = 0$$
2. **`constructive_action_positive_payoff`:**
   $$\forall a, \text{Constructive}(a) \land \Delta S_{\text{ext}} = 0 \land U > \Delta S_{\text{int}} \implies \text{net\_exergy\_payoff}(a) > 0$$
3. **`cooperation_dominates_moloch`:**
   $$\forall a_{\text{coop}}, a_{\text{ext}}, \text{net\_exergy\_payoff}(a_{\text{coop}}) > \text{net\_exergy\_payoff}(a_{\text{ext}})$$
4. **`landauer_compensates_entropy`:**
   $$\forall a, \text{landauer\_penalty}(a) \ge a.\text{externalized\_entropy}$$
5. **`trace_entropy_solvency_universal` (Solvencia Inductiva Multi-Agente):**
   $$\forall \text{trace} \in \text{List AgentAction}, \sum_{a \in \text{trace}} \text{landauer\_penalty}(a) \ge \sum_{a \in \text{trace}} a.\text{externalized\_entropy}$$

## 4. Estatus Computacional y Límites Físicos

- **Ámbito Formal:** Los teoremas demostrados garantizan la consistencia algebraica interna del mecanismo en la aritmética de Peano ($\mathbb{N}$).
- **Límites de Correspondencia:** Un teorema en Lean 4 no garantiza por sí mismo que un hardware concreto disipe exactamente $k_B T \ln 2$; la medición de disipación de calor exige calorímetros físicos y telemetría de silicio. En el software de BABYLON-60, la entropía se contabiliza en créditos de exergía discretos acoplados al colateral transaccional del ledger BFT (LARSA-120).
- **Atestación de Solidez:** Verificada en suite de pruebas automatizadas mediante `tests/test_lean_kernel_soundness.py::test_moloch_landauer_kernel_theorems_present`.
