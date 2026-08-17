import CTMCore
import CTMBudget

namespace CTMRefinement

open CTMCore
open CTMBudget

/--
Raw unverified Evidence step supplied by runtime (BABYLON-60).
Notice that `is_legal_diagnostic` is strictly diagnostic telemetry and NEVER trusted by the Lean Kernel.
-/
structure RawRuntimeStep (S A : Type) where
  src_state : S
  dst_state : S
  action : A
  cost_tokens : Nat
  is_legal_diagnostic : Bool  -- Untrusted runtime reporting, ignored by formal proof

/--
Sequence of raw evidence steps emitted by the runtime.
-/
def RawRuntimeTrace (S A : Type) := List (RawRuntimeStep S A)

/--
The Sound Refinement Relation (`Refines`):
Requires that for every step supplied by the runtime:
1. The transition `E curr next` is valid under the formal relation.
2. The legal predicate `Legal curr action` is RECOMPUTED and PROVEN by the verifier.
3. The cost function `cost curr next` matches the reported tokens.
The runtime's diagnostic reporting (`is_legal_diagnostic`) is completely bypassed.
-/
inductive Refines {S A : Type} (E : S → S → Prop) (Legal : S → A → Prop) (cost : S → S → Nat) (start : S) : RawRuntimeTrace S A → Nat → S → Prop where
  | nil : Refines E Legal cost start [] 0 start
  | cons {curr next : S} {action : A} {rest : RawRuntimeTrace S A} {c : Nat} {step : RawRuntimeStep S A} :
      step.src_state = curr →
      step.dst_state = next →
      step.action = action →
      Legal curr action →  -- Recomputed / Proven by verifier, NOT trusted from step.is_legal_diagnostic
      E curr next →
      cost curr next = step.cost_tokens →
      Refines E Legal cost start rest c curr →
      Refines E Legal cost start (rest ++ [step]) (c + step.cost_tokens) next

/--
The Refinement Soundness Theorem:
If raw runtime evidence refines to a Lean trace of accumulated cost `c`,
then there exists a valid, formally certified `BoundedTrace` in the Lean Kernel.
No trust is placed in the runtime's self-reported diagnostics.
-/
theorem runtime_evidence_soundness {S A : Type}
    (E : S → S → Prop) (Legal : S → A → Prop) (cost : S → S → Nat)
    (start target : S) (raw_trace : RawRuntimeTrace S A) (c : Nat)
    (h_refine : Refines E Legal cost start raw_trace c target) :
    BoundedTrace E cost start c target := by
  induction h_refine with
  | nil =>
    exact BoundedTrace.refl
  | cons h_src h_dst h_action h_legal h_e h_cost h_prev ih =>
    subst h_src h_dst h_cost h_action
    exact BoundedTrace.step ih h_e

-- AP-09 AUDIT: Trusted Core Axiom Audits
#print axioms Refines
#print axioms runtime_evidence_soundness

end CTMRefinement
