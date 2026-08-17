/-
  CTM.Graph — Cognitive Transition Machine Formal Kernel (Iteration 38)
  
  The CTM is a Graph G = (S, E, F).
  "Action" is completely eliminated. The unit is a typed transition s → s'.
  
  Luna generates candidate transitions.
  CTM filters legal transitions.
  External tools inject new transitions.
-/

namespace CTM.Graph

axiom State : Type

/-- The intrinsic transitions the model (Luna) can propose -/
axiom E_M : State → State → Prop

/-- The strict legal transitions defined by the CTM -/
axiom Legal : State → State → Prop

/-- Accepted terminal states (Kernel Check) -/
axiom Accept : State → Prop

/-- 
  CTM³³: CTM merely filters candidates.
  Filter_M(S) = CandidateTransitions(M, S) ∩ LegalTransitions(S)
-/
def E_CTM (s s' : State) : Prop := E_M s s' ∧ Legal s s'

/-- Reachability (Transitive Closure) -/
inductive Reach (E : State → State → Prop) (x : State) : State → Prop
  | refl : Reach E x x
  | step {y z : State} : Reach E x y → E y z → Reach E x z

/-- 
  Nuclear Theorem (CTM³⁴): Theorem of Non-Creation.
  CTM cannot increase the reachable state space; it only reorganizes traversal.
-/
theorem ctm_reach_bounded (x y : State) (h : Reach E_CTM x y) : Reach E_M x y :=
by
  induction h with
  | refl => exact Reach.refl
  | step _ h_edge ih =>
    -- Extract E_M from the CTM intersection
    have h_EM : E_M _ y := h_edge.left
    exact Reach.step ih h_EM

/--
  CTM³⁶: The true frontier of Capacity Expansion.
  External Tools expand the Generate phase, not just the Filter phase.
-/
axiom E_Tool : State → State → Prop

/-- The combined generation capacity: Model + External Tools -/
def E_M_Tool (s s' : State) : Prop := E_M s s' ∨ E_Tool s s'

/-- The CTM filtering applied to the expanded capacity -/
def E_CTM_Tool (s s' : State) : Prop := E_M_Tool s s' ∧ Legal s s'

end CTM.Graph
