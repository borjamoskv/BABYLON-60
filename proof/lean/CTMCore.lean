namespace CTMCore

/--
State Space and Action Space primitives.
These are completely agnostic of any particular implementation, modeling
the bare minimal ontology of the CTM.
-/
variable {S A : Type}

/--
Strong Invariant State boundary.
A state wrapped with a formal proof that it satisfies the invariant.
This ensures the machine cannot represent invalid states.
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
The strict transition controller.
It takes a certified `SafeState`, an `Action`, and a formal proof of legality.
It outputs a new certified `SafeState`.
This enforces the strict boundary between abduction (generation) and deduction (certification).
-/
def step {S A : Type} (M : CTM S A) (s_safe : SafeState S M.invariant) (a : A) (h_legal : M.legal s_safe.val a) : SafeState S M.invariant :=
  -- Extract the bare state and its proof of invariant
  let s_val := s_safe.val
  let h_inv := s_safe.property
  
  -- Generate the next state via the untrusted transition
  let s_next := M.transition s_val a
  
  -- Apply the preservation theorem to certify the next state
  let h_next_inv := M.preservation s_val a h_inv h_legal
  
  -- Package and return the new Strong State
  ⟨s_next, h_next_inv⟩

-- AP-09 AUDIT: No custom axioms or sorryAx used. 
-- Validating that the core CTM transition engine is constructively sound.
#print axioms step

end CTMCore
