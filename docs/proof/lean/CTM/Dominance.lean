/-
  CTM.Dominance — Cognitive Transition Machine Formal Kernel (Iteration 25)
  
  Formalizes Policy Dominance and the CTM Calculus.
  
  "Conservative(π_CTM) ∧ ValidRepair ⇒ Success_CTM ≥ Success_base"
-/

import Mathlib.Data.Real.Basic

namespace CTM.Dominance

axiom Task : Type
axiom State : Type

/-- A Policy maps a Task and a Compute Budget (Nat) to a final State -/
def Policy := Task → Nat → State

/-- The Kernel acts as a strict boundary, accepting or rejecting a state -/
axiom Accept : State → Prop

/-- A policy is Successful on a task if its final state is Accepted by the Kernel -/
def Success (pi : Policy) (t : Task) (b : Nat) : Prop :=
  Accept (pi t b)

/--
  A CTM policy is Conservative with respect to a base policy if it never discards a valid certificate.
  If the base policy succeeds under budget B, the CTM policy MUST succeed under budget B + b.
-/
def Conservative (pi_base pi_ctm : Policy) : Prop :=
  ∀ t B b, Success pi_base t B → Success pi_ctm t (B + b)

/--
  Nuclear Theorem (CTM²⁰ / CTM²³): Monotonic Improvement under Expanded Budget.
  If the CTM policy is conservative, it guarantees dominance over the baseline.
  It cannot destroy successes. Gain emerges exclusively from the residuals (base failures).
-/
theorem ctm_dominance 
  (pi_base pi_ctm : Policy)
  (t : Task)
  (B : Nat)
  (b : Nat)
  (h_cons : Conservative pi_base pi_ctm)
  (h_base_success : Success pi_base t B) :
  Success pi_ctm t (B + b) :=
by
  exact h_cons t B b h_base_success

/--
  CTM Calculus Decomposition (CTM²⁴).
  Observed Performance = Intrinsic Capability + Search Efficiency + External Computation.
  
  We model the experimental branches as Empirical Probabilities (Reals).
-/
structure EmpiricalPerformance where
  A : ℝ -- Luna / 1 pass (Identity)
  B : ℝ -- Luna / N passes / random retry
  C : ℝ -- Luna / CTM / N passes (Structured Policy)
  D : ℝ -- Luna / CTM + External Tools
  E : ℝ -- Sol / matched budget

/-- G_policy: Better transition selection (Search Efficiency) -/
def G_policy (perf : EmpiricalPerformance) : ℝ := perf.C - perf.B

/-- G_tools: External capabilities (Verification / SMT / Computation) -/
def G_tools (perf : EmpiricalPerformance) : ℝ := perf.D - perf.C

/-- G_capability: Intrinsic model capability residual -/
def G_capability (perf : EmpiricalPerformance) : ℝ := perf.E - perf.D

end CTM.Dominance
