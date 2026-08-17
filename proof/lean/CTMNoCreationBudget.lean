import CTMCore
import CTMBudget

namespace CTMNoCreationBudget

open CTMCore
open CTMBudget

/--
Lemma: BoundedTrace preservation under transition inclusion and cost equivalence.
If E_CTM s1 s2 → E_M s1 s2 and cost_CTM s1 s2 = cost_M s1 s2,
then any trace under CTM with cost c is a valid trace under M with exact cost c.
-/
theorem trace_subset {S : Type}
    (E_CTM E_M : S → S → Prop)
    (cost_CTM cost_M : S → S → Nat)
    (h_sub : ∀ s1 s2, E_CTM s1 s2 → E_M s1 s2)
    (h_cost : ∀ s1 s2, E_CTM s1 s2 → cost_CTM s1 s2 = cost_M s1 s2)
    (start target : S) (c : Nat)
    (h_trace : BoundedTrace E_CTM cost_CTM start c target) :
    BoundedTrace E_M cost_M start c target := by
  induction h_trace with
  | refl =>
    exact BoundedTrace.refl
  | step h_prev h_trans ih =>
    have h_m_trans : E_M _ _ := h_sub _ _ h_trans
    have h_eq_cost : cost_CTM _ _ = cost_M _ _ := h_cost _ _ h_trans
    rw [← h_eq_cost]
    exact BoundedTrace.step ih h_m_trans

/--
The Bounded No-Creation Theorem:
Under identical costs and transition inclusion (E_CTM ⊆ E_M),
the Bounded Reachable space of CTM under budget B is a subset of the Bounded Reachable space of Model M under budget B.
-/
theorem bounded_reach_subset {S : Type}
    (E_CTM E_M : S → S → Prop)
    (cost_CTM cost_M : S → S → Nat)
    (h_sub : ∀ s1 s2, E_CTM s1 s2 → E_M s1 s2)
    (h_cost : ∀ s1 s2, E_CTM s1 s2 → cost_CTM s1 s2 = cost_M s1 s2)
    (B : Nat) (start target : S)
    (h_bounded : BoundedReachable E_CTM cost_CTM B start target) :
    BoundedReachable E_M cost_M B start target := by
  rcases h_bounded with ⟨c, h_bound, h_trace⟩
  have h_m_trace := trace_subset E_CTM E_M cost_CTM cost_M h_sub h_cost start target c h_trace
  exact ⟨c, h_bound, h_m_trace⟩

-- AP-09 AUDIT: Trusted Core Axiom Audits
#print axioms trace_subset
#print axioms bounded_reach_subset

end CTMNoCreationBudget
