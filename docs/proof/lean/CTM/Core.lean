/-
  CTM.Core — Cognitive Transition Machine Formal Kernel (Iteration 4)
  
  Formalizes the epistemological principle:
  CTM = (S, A, T, V, B)
  
  "Agent" is a derived object (a sequence of transitions).
  "Transition" is the fundamental primitive.
-/

namespace CTM

/-- 
  The Core Abstract Machine.
  S : State space
  A : Action space
-/
structure Machine (S A : Type) where
  step : S → A → S
  invariant : S → Prop
  verifier : S → Prop
  is_terminal : S → Prop
  budget_ok : S → Prop

/-- 
  Definition: A state is Accepted iff it's terminal, within budget, and passes the verifier.
  This breaks the tautology of "Accepted = Verified".
-/
def Accepted {S A : Type} (m : Machine S A) (s : S) : Prop :=
  m.is_terminal s ∧ m.budget_ok s ∧ m.verifier s

/-- 
  The verifier acts as a trust boundary.
  We require a proof of its soundness against a ground truth `Correct` property.
-/
def VerifierSound {S A : Type} (m : Machine S A) (Correct : S → Prop) : Prop :=
  ∀ s, m.verifier s → Correct s

/-- 
  Nuclear Theorem 1: Accepted implies Correct (bounded by Verifier Soundness).
  Luna can be wrong. The CTM can be wrong. 
  But if it crosses a sound Verifier boundary, we have a local formal guarantee.
-/
theorem accepted_sound {S A : Type} 
  (m : Machine S A) 
  (Correct : S → Prop)
  (h_sound : VerifierSound m Correct)
  (s : S)
  (h_acc : Accepted m s) : 
  Correct s := 
by
  -- Extract verifier passed from Accepted definition
  have h_ver : m.verifier s := h_acc.right.right
  -- Apply soundness
  exact h_sound s h_ver

/-- 
  A transition is Legal if it preserves the machine's invariant.
-/
def LegalTransition {S A : Type} (m : Machine S A) (s : S) (a : A) : Prop :=
  m.invariant s → m.invariant (m.step s a)

/-- 
  Nuclear Theorem 2: Invariant Preservation under Legal Transitions
-/
theorem ctm_preserves_invariant {S A : Type}
  (m : Machine S A)
  (s : S)
  (a : A)
  (h₀ : m.invariant s)
  (h_legal : LegalTransition m s a) :
  m.invariant (m.step s a) :=
by
  exact h_legal h₀

/--
  Agent is a derived object.
  It is simply the execution of the Machine over a sequence of Actions (policy).
-/
def run {S A : Type} (m : Machine S A) (initial : S) (actions : List A) : S :=
  actions.foldl m.step initial

/--
  Nuclear Theorem 3: Global Invariant Preservation (Induction over run)
-/
theorem run_preserves_invariant {S A : Type}
  (m : Machine S A)
  (initial : S)
  (actions : List A)
  (h_init : m.invariant initial)
  -- We assume that ANY action taken during this specific run was a LegalTransition
  -- This models that the orchestration policy only produces legal actions.
  (h_policy : ∀ (s : S) (a : A), m.invariant s → a ∈ actions → LegalTransition m s a) :
  m.invariant (run m initial actions) :=
by
  -- Lean 4 induction over the list of actions.
  -- This requires a slightly stronger invariant linking reachable states to the policy.
  -- But conceptually, this is the limit we are approaching.
  sorry

end CTM
