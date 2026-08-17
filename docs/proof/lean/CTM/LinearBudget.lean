/-
  CTM.LinearBudget — Formalizing Budget as a Linear Resource (Iteration 38)
-/

import CTM.Graph

namespace CTM.LinearBudget

open CTM.Graph

/--
  A bounded run where each transition consumes exactly 1 unit of budget.
-/
inductive BoundedRun (E : State → State → Prop) : State → Nat → State → Prop
  | empty (s : State) (B : Nat) : BoundedRun E s B s
  | step {s y z : State} {B : Nat} : 
      B > 0 → 
      BoundedRun E s B y → 
      E y z → 
      BoundedRun E s (B - 1) z

/--
  Theorem: Bounded runs are a subset of unbounded reachability.
-/
theorem bounded_implies_reach {E : State → State → Prop} {s s' : State} {B : Nat} 
  (h : BoundedRun E s B s') : Reach E s s' :=
by
  induction h with
  | empty _ _ => exact Reach.refl
  | step _ _ h_edge ih =>
    exact Reach.step ih h_edge

/--
  CTM³⁷: Coverage Metric
  Instead of comparing capabilities, the benchmark evaluates the fraction 
  of Tasks for which there exists a BoundedRun ending in an Accepted state 
  within a constant Budget B.
-/
-- Conceptually: Coverage(B) = P(∃ s', BoundedRun E s_0 B s' ∧ Accept s')

end CTM.LinearBudget
