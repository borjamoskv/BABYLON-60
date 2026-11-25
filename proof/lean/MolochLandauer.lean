/-
AUDITORÍA DE ALCANCE · 2026-10-25
Contabilidad abstracta en Nat con resta truncada y penalización definida. Se prueban desigualdades de esa función, no física de Landauer, medición de externalidades, equilibrio de juego, compatibilidad de incentivos o dominancia de Pareto.
Nombres públicos preservados; este cambio solo corrige comentarios.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

set_option warningAsError true

namespace Babylon.MolochLandauer

/-! Sección del modelo discreto. El alcance de cada declaración depende de su tipo y sus hipótesis, no del nombre de la sección. -/

inductive ActionClass where
  | Constructive   -- Aporta exergía neta al pool común
  | Neutral        -- Conservativo, sin externalidades
  | Extract        -- Tragedia de los comunes / carrera armamentística / Moloch
  | Apoptosis      -- Auto-aniquilación controlada (FAIL-STOP 0xDEAD_6060)
deriving Repr, BEq, DecidableEq

/-- Registro de magnitudes Nat declaradas por el modelo. No mide energía, entropía, colateral o efectos observados. -/
structure AgentAction where
  agent_id : Nat
  action_class : ActionClass
  claimed_benefit : Nat
  internal_dissipation : Nat
  externalized_entropy : Nat
deriving Repr, BEq, DecidableEq

/-! Sección del modelo discreto. El alcance de cada declaración depende de su tipo y sus hipótesis, no del nombre de la sección. -/

/-- Detector definido mediante una etiqueta y campos declarados por la acción. -/
def is_moloch_extraction (a : AgentAction) : Bool :=
  match a.action_class with
  | .Extract =>
    (a.claimed_benefit > 0) && (a.externalized_entropy > a.internal_dissipation)
  | _ => false

/-! Sección del modelo discreto. El alcance de cada declaración depende de su tipo y sus hipótesis, no del nombre de la sección. -/

/-- Penalización definida a partir de campos Nat; el nombre no establece unidades ni la ley física de Landauer. -/
def landauer_penalty (a : AgentAction) : Nat :=
  if is_moloch_extraction a then
    a.externalized_entropy + a.claimed_benefit
  else
    a.externalized_entropy

/-- Beneficio menos costes mediante resta truncada en Nat; no representa pérdidas negativas o bienestar de todos los participantes. -/
def net_exergy_payoff (a : AgentAction) : Nat :=
  a.claimed_benefit - (a.internal_dissipation + landauer_penalty a)

/-- Compara un argumento de colateral con una penalización; no acredita fondos reales ni que se cobre la penalización. -/
def is_admissible (a : AgentAction) (agent_collateral : Nat) : Bool :=
  agent_collateral ≥ landauer_penalty a

/-! Sección del modelo discreto. El alcance de cada declaración depende de su tipo y sus hipótesis, no del nombre de la sección. -/

/-- Bajo el detector, la penalización definida fuerza payoff Nat cero. No se prueban incentivos de agentes externos. -/
theorem moloch_payoff_is_zero (a : AgentAction) (h_moloch : is_moloch_extraction a = true) :
    net_exergy_payoff a = 0 := by
  unfold net_exergy_payoff
  unfold landauer_penalty
  rw [h_moloch]
  simp
  omega

/-- Positividad condicional de la fórmula bajo clase, externalidad y beneficio supuestos. -/
theorem constructive_action_positive_payoff (a : AgentAction)
    (h_class : a.action_class = .Constructive)
    (h_ext : a.externalized_entropy = 0)
    (h_ben : a.claimed_benefit > a.internal_dissipation) :
    net_exergy_payoff a > 0 := by
  unfold net_exergy_payoff
  unfold landauer_penalty
  unfold is_moloch_extraction
  rw [h_class]
  rw [h_ext]
  simp
  omega

/-- Compara dos valores de una función de payoff bajo hipótesis. No demuestra dominancia de Pareto o equilibrio de un juego. -/
theorem cooperation_dominates_moloch (a_coop a_ext : AgentAction)
    (h_coop_class : a_coop.action_class = .Constructive)
    (h_coop_ext : a_coop.externalized_entropy = 0)
    (h_coop_ben : a_coop.claimed_benefit > a_coop.internal_dissipation)
    (h_moloch : is_moloch_extraction a_ext = true) :
    net_exergy_payoff a_coop > net_exergy_payoff a_ext := by
  have h_zero : net_exergy_payoff a_ext = 0 := moloch_payoff_is_zero a_ext h_moloch
  have h_pos : net_exergy_payoff a_coop > 0 :=
    constructive_action_positive_payoff a_coop h_coop_class h_coop_ext h_coop_ben
  rw [h_zero]
  exact h_pos

/-- La penalización definida es mayor o igual al campo de externalidad; no prueba transferencia, cobro o balance físico. -/
theorem landauer_compensates_entropy (a : AgentAction) :
    landauer_penalty a ≥ a.externalized_entropy := by
  unfold landauer_penalty
  split
  · omega
  · exact Nat.le_refl _

/-! Sección del modelo discreto. El alcance de cada declaración depende de su tipo y sus hipótesis, no del nombre de la sección. -/

/-- Suma de un campo Nat a lo largo de una lista finita. -/
def total_externalized_entropy : List AgentAction → Nat
  | [] => 0
  | a :: rest => a.externalized_entropy + total_externalized_entropy rest

/-- Suma de penalizaciones calculadas; no registra pagos o transferencias reales. -/
def total_landauer_penalties : List AgentAction → Nat
  | [] => 0
  | a :: rest => landauer_penalty a + total_landauer_penalties rest

/-- Desigualdad entre sumas de campos de una lista arbitraria. No mide solvencia de un pool real. -/
theorem trace_entropy_solvency_universal (trace : List AgentAction) :
    total_landauer_penalties trace ≥ total_externalized_entropy trace := by
  induction trace with
  | nil =>
    exact Nat.le_refl _
  | cons a rest ih =>
    unfold total_landauer_penalties
    unfold total_externalized_entropy
    have h_a := landauer_compensates_entropy a
    omega

end Babylon.MolochLandauer
