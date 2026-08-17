/-
  CTM.Architecture — Cognitive Transition Machine Formal Kernel (Iteration 30)
  
  The absolute theoretical apex.
  CTM = (S, A, T, L)
  
  Luna (Model) proposes.
  CTM (TransitionSystem) transitions and restricts (L).
  Checker (Kernel) decides acceptance.
  Benchmark measures (Task, Model, TransitionSystem, Checker, Budget).
-/

namespace CTM.Architecture

/-- 
  The bare CTM Transition System. 
  It knows nothing about "truth", "strategies", or "agents".
-/
structure TransitionSystem (State Action : Type) where
  step : State → Action → State
  legal : State → Action → Prop

/-- 
  The External Checker (Kernel) only knows about acceptance.
-/
structure Checker (State : Type) where
  accept : State → Prop

/-- 
  A Run is a sequence of Actions applied from an initial state.
-/
def run {S A : Type} (ts : TransitionSystem S A) (s : S) (actions : List A) : S :=
  actions.foldl ts.step s

/-- 
  A Run is Valid if every action taken was legal in the state it was applied.
-/
inductive ValidRun {S A : Type} (ts : TransitionSystem S A) : S → List A → Prop
  | empty (s : S) : ValidRun ts s []
  | step (s : S) (a : A) (as : List A) : 
      ts.legal s a → 
      ValidRun ts (ts.step s a) as → 
      ValidRun ts s (a :: as)

/-- 
  Nuclear Theorem (CTM²⁹): A valid run guarantees legality everywhere.
  This completely isolates the properties of the execution from the "intelligence" of the proposer.
-/
theorem valid_run_implies_legal {S A : Type} 
  (ts : TransitionSystem S A) 
  (s : S) 
  (actions : List A)
  (h_valid : ValidRun ts s actions) :
  ∀ (a : A), a ∈ actions → ∃ (s' : S), ts.legal s' a :=
by
  intro a ha
  induction h_valid with
  | empty _ => 
    -- 'a ∈ []' is false
    contradiction
  | step s_cur a_cur as_tail h_leg h_val_tail ih =>
    cases ha with
    | head _ => 
      -- a = a_cur
      exact ⟨s_cur, h_leg⟩
    | tail _ ha_tail => 
      -- a ∈ as_tail
      exact ih ha_tail

/--
  The Experimental Unit (CTM³⁰).
  We no longer measure "agents". We measure a 5-tuple.
-/
structure Experiment (Task Model State Action Budget : Type) where
  task : Task
  model : Model
  ts : TransitionSystem State Action
  checker : Checker State
  budget : Budget

end CTM.Architecture
