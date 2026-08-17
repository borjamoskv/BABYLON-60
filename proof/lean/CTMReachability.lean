import CTMCore

namespace CTMReachability

open CTMCore

/--
Inductive definition of reachable states under a transition relation E.
-/
inductive Reachable {S : Type} (E : S → S → Prop) (start : S) : S → Prop where
  | refl : Reachable E start start
  | step {curr next : S} : Reachable E start curr → E curr next → Reachable E start next

/--
The No-Creation Theorem:
If every transition allowed by CTM is a subset of the transitions generable by Model M,
then the reachable state space of CTM is a subset of the reachable state space of Model M.

Hypotheses are EXPLICIT in the statement (AP-03 compliant):
- E_CTM : Transition relation of CTM
- E_M   : Transition relation of Model M
- h_sub : ∀ s1 s2, E_CTM s1 s2 → E_M s1 s2
-/
theorem reach_subset {S : Type} (E_CTM E_M : S → S → Prop)
    (h_sub : ∀ s1 s2, E_CTM s1 s2 → E_M s1 s2)
    (start target : S)
    (h_reach : Reachable E_CTM start target) :
    Reachable E_M start target := by
  induction h_reach with
  | refl =>
    exact Reachable.refl
  | step h_prev h_trans ih =>
    have h_m_trans : E_M _ _ := h_sub _ _ h_trans
    exact Reachable.step ih h_m_trans

-- AP-09 AUDIT: Trusted Core Axiom Audit for Reachability Theorem
#print axioms Reachable
#print axioms reach_subset

end CTMReachability
