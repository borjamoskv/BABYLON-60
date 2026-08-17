/-
  CTM.Metrics — Cognitive Recovery Metrics (Iteration 4)
  
  Separates model capability from orchestration and formalizes
  the Recovery Efficacy (RE) metric mathematically.
-/

import Mathlib.Data.Real.Basic

namespace CTM.Metrics

/-- 
  Recovery Efficacy (RE).
  Measures the portion of the model-gap recovered by the orchestration.
  A: Perf(Luna, Identity, T)
  C: Perf(Luna, CTM, T)
  D: Perf(Sol, Identity, T)
-/
def Recovery (A C D : ℝ) : Option ℝ :=
  if h : D ≠ A then
    some ((C - A) / (D - A))
  else
    none

/--
  Theorem: If orchestration yields no improvement over single-pass, Recovery is 0.
-/
theorem recovery_zero (A C D : ℝ) (h_gap : D ≠ A) (h_no_gain : C = A) : 
  Recovery A C D = some 0 := 
by
  unfold Recovery
  split
  · -- Case D ≠ A (h is true)
    rw [h_no_gain, sub_self, zero_div]
  · -- Case ¬(D ≠ A) (contradicts h_gap)
    contradiction

/--
  Theorem: If orchestration perfectly matches Sol's performance, Recovery is 1.
-/
theorem recovery_one (A C D : ℝ) (h_gap : D ≠ A) (h_perfect : C = D) : 
  Recovery A C D = some 1 := 
by
  unfold Recovery
  split
  · -- Case D ≠ A (h is true)
    rw [h_perfect, div_self]
    exact sub_ne_zero.mpr h_gap
  · -- Case ¬(D ≠ A) (contradicts h_gap)
    contradiction

end CTM.Metrics
