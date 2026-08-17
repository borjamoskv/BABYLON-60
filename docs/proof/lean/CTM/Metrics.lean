/-
  CTM.Metrics — Formalization of Cognitive Recovery Metrics
  
  Formalizes the RE (Recovery Efficacy) metric:
  RE = (Score(CTM) - Score(A)) / (Score(Sol) - Score(A))
  
  and its guarded bounds.
-/

namespace CTM.Metrics

/-- Scores are represented as Reals, but here we can abstract them as Floats for the benchmark logic -/
structure BenchmarkScores where
  score_A : Float  -- Luna Single-Pass
  score_D : Float  -- Sol Single-Pass
  score_C : Float  -- Luna CTM (Recovered)
  
/-- 
  Recovery Efficacy (RE).
  We define it guarded by an epsilon to avoid division by zero.
-/
def RE (scores : BenchmarkScores) (epsilon : Float) : Option Float :=
  let gap := scores.score_D - scores.score_A
  if gap.abs < epsilon then
    none -- Guard against instability if Score(D) ≈ Score(A)
  else
    some ((scores.score_C - scores.score_A) / gap)

/-- 
  Properties of RE:
  1. If Score(C) == Score(A) and gap > epsilon, RE == 0.0
  2. If Score(C) == Score(D) and gap > epsilon, RE == 1.0
-/
-- These can be proven as theorems in Lean.

end CTM.Metrics
