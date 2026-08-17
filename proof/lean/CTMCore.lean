namespace CTMCore

/--
State Space and Action Space primitives.
Completely agnostic of any particular implementation, modeling
the bare minimal ontology of the CTM.
-/
variable {S A : Type}

/--
Strong Invariant State boundary.
A state wrapped with a formal proof that it satisfies the invariant.
Lean models Subtypes as a value paired with a proof of the property, transparent in runtime.
-/
def SafeState (S : Type) (I : S → Prop) := { s : S // I s }

/--
The Core Cognitive Transition Machine Structure.
It groups the space, the generator, the invariant, the legal collision filter,
and the fundamental preservation theorem.
-/
structure CTM (S A : Type) where
  /-- Untrusted abductive transition generator (e.g. Luna) -/
  transition : S → A → S
  
  /-- The core Invariant -/
  invariant : S → Prop
  
  /-- The Collision Filter / Constraint -/
  legal : S → A → Prop
  
  /-- 
  The Trusted Kernel Proof. 
  The fundamental theorem ensuring that legal transitions preserve the invariant.
  -/
  preservation : ∀ (s : S) (a : A), invariant s → legal s a → invariant (transition s a)

/--
Explicit theorem proving that a valid transition step preserves the state invariant.
-/
theorem step_preserves {S A : Type} (M : CTM S A) (s : SafeState S M.invariant) (a : A) (hlegal : M.legal s.val a) :
    M.invariant (M.transition s.val a) := by
  exact M.preservation s.val a s.property hlegal

/--
The strict transition controller (safeStep).
Constructs a new certified SafeState by pairing the untrusted proposal with the step_preserves proof.
Untrusted proposal -> Legal proof -> Invariant-preserving transition.
-/
def safeStep {S A : Type} (M : CTM S A) (s : SafeState S M.invariant) (a : A) (hlegal : M.legal s.val a) : SafeState S M.invariant :=
  ⟨M.transition s.val a, step_preserves M s a hlegal⟩

-- AP-09 AUDIT: Trusted Core Axiom Audits
-- Must be checked in CI with Lean toolchain to verify zero custom axioms or sorryAx.
#print axioms SafeState
#print axioms step_preserves
#print axioms safeStep

end CTMCore
