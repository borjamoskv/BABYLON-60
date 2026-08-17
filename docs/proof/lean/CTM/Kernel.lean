/-
  CTM.Kernel — Cognitive Transition Machine Formal Kernel (Iteration 10)
  
  The absolute minimal core. 
  Eliminates "verification" as a phase, deriving it directly from type checking.
  
  Luna = heuristic search
  CTM  = control policy
  Lean = trust kernel
  Proof = interface between them
-/

namespace CTM.Kernel

/-- 
  The LLM (Luna/Sol) acts as a stochastic heuristic search over the Problem space,
  attempting to produce a Candidate Proof.
-/
structure Solver (Problem Proof : Type) where
  search : Problem → Proof

/-- 
  The Kernel (Lean/External Verifier) defines what is valid.
  It provides a computable `check` function and a mathematical proof of its `soundness`.
-/
structure Kernel (Proof : Type) where
  valid : Proof → Prop
  check : Proof → Bool
  sound : ∀ p, check p = true → valid p

/-- 
  CertifiedSolve represents the fundamental trust boundary.
  It evaluates a solver's output through the kernel.
-/
def CertifiedSolve {Problem Proof : Type}
    (s : Solver Problem Proof)
    (k : Kernel Proof)
    (t : Problem) : Option Proof :=
  let p := s.search t
  if k.check p then some p else none

/-- 
  Nuclear Theorem (CTM¹⁰): The Theorem of Non-Contamination.
  The final correctness does not depend on Luna being correct or intelligent.
  It ONLY depends on Luna producing a proof acceptable by the Kernel.
  
  ∀ H, Sound(K) ⇒ Accepted_K(H(T)) ⇒ Correct
-/
theorem certified_sound {Problem Proof : Type}
    (k : Kernel Proof)
    (s : Solver Problem Proof)
    (t : Problem)
    (p : Proof)
    (h : CertifiedSolve s k t = some p) :
    k.valid p := 
by
  -- Unfold the definition of CertifiedSolve
  unfold CertifiedSolve at h
  -- We have a conditional logic based on k.check (s.search t)
  split at h
  · -- Case: k.check (s.search t) = true
    -- In this case, `some (s.search t) = some p`, so `p = s.search t`
    have h_eq : s.search t = p := by injection h
    -- The split gave us the hypothesis that the condition was true
    rename_i h_check
    -- Substitute s.search t with p in the check condition
    rw [h_eq] at h_check
    -- Apply the kernel's soundness axiom
    exact k.sound p h_check
  · -- Case: k.check (s.search t) = false
    -- In this case, `none = some p`, which is a contradiction.
    contradiction

end CTM.Kernel
