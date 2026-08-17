/-
  CTM.Core — Cognitive Transition Machine Formal Kernel
  
  Formalizes the epistemological principle:
  "CTM + External Verification => Correctness Preservation"
  
  The model separates generation (Model) from truth declaration (Verifier).
-/

namespace CTM

/-- Representation of a Problem/Task -/
structure Task where
  id : String

/-- Representation of a Solution Candidate -/
structure Solution where
  id : String
  isOptimal : Bool

/-- Status of the CTM Execution -/
inductive Status
  | generating
  | verifying
  | terminal_success
  | terminal_failure (reason : String)
  deriving Repr, BEq

/-- The state of the Cognitive Transition Machine -/
structure State where
  task : Task
  currentSolution : Option Solution
  status : Status
  iterations : Nat
  maxIterations : Nat

/-- 
  The External Verifier is modeled as a Sound Oracle.
  If the verifier accepts a solution, the solution is formally correct (isOptimal = true).
-/
structure ExternalVerifier where
  check : Task → Solution → Bool
  soundness : ∀ t s, check t s = true → s.isOptimal = true

/-- Actions that the CTM can take -/
inductive Action
  | propose (sol : Solution)
  | accept
  | reject (feedback : String)
  | abort_stagnation

/-- The State Transition Function of the CTM -/
def step (state : State) (action : Action) : State :=
  match state.status with
  | Status.terminal_success => state
  | Status.terminal_failure _ => state
  | _ =>
    if state.iterations >= state.maxIterations then
      { state with status := Status.terminal_failure "budget_exhausted" }
    else
      match action with
      | Action.propose sol =>
        { state with 
          currentSolution := some sol,
          status := Status.verifying,
          iterations := state.iterations + 1 }
      | Action.accept =>
        { state with status := Status.terminal_success }
      | Action.reject _ =>
        { state with status := Status.generating }
      | Action.abort_stagnation =>
        { state with status := Status.terminal_failure "stagnation_detected" }

/-- 
  Theorem: Correctness Preservation (Soundness of Terminal Success)
  If the CTM reaches a Terminal Success via an 'accept' action approved by the verifier,
  the current solution is guaranteed to be optimal.
-/
theorem correctness_preservation 
  (s : State) 
  (v : ExternalVerifier)
  (sol : Solution)
  (h_status : s.status = Status.verifying)
  (h_sol : s.currentSolution = some sol)
  (h_check : v.check s.task sol = true)
  (h_budget : s.iterations < s.maxIterations)
  : 
  let next_state := step s Action.accept;
  next_state.status = Status.terminal_success ∧ sol.isOptimal = true := 
by
  intro next_state
  have h_optimal : sol.isOptimal = true := v.soundness s.task sol h_check
  
  have h_not_term_succ : s.status ≠ Status.terminal_success := by 
    rw [h_status]; decide
  have h_not_term_fail : ∀ r, s.status ≠ Status.terminal_failure r := by 
    intro r; rw [h_status]; decide
    
  have h_step : step s Action.accept = { s with status := Status.terminal_success } := by
    unfold step
    split
    · contradiction
    · contradiction
    · split
      · exact False.elim (not_le_of_lt h_budget (by assumption))
      · rfl

  constructor
  · rw [h_step]
  · exact h_optimal

end CTM
