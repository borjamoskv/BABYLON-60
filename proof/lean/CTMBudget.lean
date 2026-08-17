import CTMCore

namespace CTMBudget

open CTMCore

/--
Inductive definition of a trace with accumulated transition cost.
`BoundedTrace E cost start c target` means `target` is reachable from `start`
via transition relation `E` with an exact accumulated cost of `c`.
-/
inductive BoundedTrace {S : Type} (E : S → S → Prop) (cost : S → S → Nat) (start : S) : Nat → S → Prop where
  | refl : BoundedTrace E cost start 0 start
  | step {curr next : S} {c : Nat} :
      BoundedTrace E cost start c curr →
      E curr next →
      BoundedTrace E cost start (c + cost curr next) next

/--
Bounded Reachability definition:
`BoundedReachable E cost B start target` holds if there exists an accumulated cost `c ≤ B`
such that `BoundedTrace E cost start c target`.
-/
def BoundedReachable {S : Type} (E : S → S → Prop) (cost : S → S → Nat) (B : Nat) (start target : S) : Prop :=
  ∃ c : Nat, c ≤ B ∧ BoundedTrace E cost start c target

/--
Budget Preservation Lemma:
If accumulated cost `c` is bounded by `B`, and we take a step with cost `step_cost` such that
`c + step_cost ≤ B`, then the new accumulated cost is bounded by `B`.
-/
theorem budget_preservation (c step_cost B : Nat) (h_bound : c ≤ B) (h_step : c + step_cost ≤ B) :
    c + step_cost ≤ B := by
  exact h_step

/--
Monotonicity of Bounded Trace:
If a trace has accumulated cost `c`, and `c ≤ B`, then it satisfies `BoundedReachable`.
-/
theorem trace_to_bounded {S : Type} (E : S → S → Prop) (cost : S → S → Nat) (B : Nat) (start target : S) (c : Nat)
    (h_cost : c ≤ B) (h_trace : BoundedTrace E cost start c target) :
    BoundedReachable E cost B start target := by
  exact ⟨c, h_cost, h_trace⟩

-- AP-09 AUDIT: Trusted Core Axiom Audits
#print axioms BoundedTrace
#print axioms BoundedReachable
#print axioms trace_to_bounded

end CTMBudget
