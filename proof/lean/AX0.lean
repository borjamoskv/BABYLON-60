-- ===============================================================================
-- FORMALIZACIÓN EN LEAN 4 CORE: AX-0 EXECUTOR Y AUTH_001
-- Proyecto: BABYLON-60 (Kernel C5-REAL)
--
-- Teorema constructivo: Un nonce consumido no puede despachar dos veces (AUTH_001).
-- Demostración constructiva en tiempo de compilación por reflexión (rfl).
-- ===============================================================================

set_option warningAsError true

-- Definición del Estado de la Autorización
inductive AuthState where
  | Proposed
  | Reserved
  | Dispatched
  | Executed
  | Unknown
deriving Repr, BEq, DecidableEq

-- Definición de Eventos Causales
inductive AuthEvent where
  | reserve
  | dispatch
  | ackSuccess
  | ackCrash
deriving Repr, BEq, DecidableEq

-- Motor de Causalidad (FSM step) - Exhaustivo para evitar 'propext' del equation compiler
def step : AuthState → AuthEvent → Option AuthState
  | .Proposed, .reserve => some .Reserved
  | .Proposed, .dispatch => none
  | .Proposed, .ackSuccess => none
  | .Proposed, .ackCrash => none
  | .Reserved, .reserve => none
  | .Reserved, .dispatch => some .Dispatched
  | .Reserved, .ackSuccess => none
  | .Reserved, .ackCrash => none
  | .Dispatched, .reserve => none
  | .Dispatched, .dispatch => none
  | .Dispatched, .ackSuccess => some .Executed
  | .Dispatched, .ackCrash => some .Unknown
  | .Executed, .reserve => none
  | .Executed, .dispatch => none
  | .Executed, .ackSuccess => none
  | .Executed, .ackCrash => none
  | .Unknown, .reserve => none
  | .Unknown, .dispatch => none
  | .Unknown, .ackSuccess => none
  | .Unknown, .ackCrash => none

-- Validación computacional recursiva final sobre una traza de eventos
def validateTrace : List AuthEvent → AuthState → Bool
  | [], _ => true
  | e :: rest, initial =>
    match step initial e with
    | some nextState => validateTrace rest nextState
    | none => false

-- ===============================================================================
-- TEOREMAS MEDIANTE REFLEXIÓN PURA (Prop -> Bool)
-- ===============================================================================

-- 1. Transición Legal (Camino Feliz)
def trace_happy : List AuthEvent := [.reserve, .dispatch, .ackSuccess]

theorem auth_001_valid_execution : validateTrace trace_happy .Proposed = true := rfl

-- 2. Detección de Doble Despacho (Colapso Causal)
def trace_double_dispatch : List AuthEvent := [.reserve, .dispatch, .dispatch]

theorem auth_001_reject_double_dispatch : validateTrace trace_double_dispatch .Proposed = false := rfl

-- 3. Detección de Falsificación de Reserva (Salto Ilegal)
def trace_illegal_dispatch : List AuthEvent := [.dispatch]

theorem auth_001_reject_illegal_dispatch : validateTrace trace_illegal_dispatch .Proposed = false := rfl

-- 4. Crash Recovery (Despacho sin confirmación pasa a Unknown)
def trace_crash : List AuthEvent := [.reserve, .dispatch, .ackCrash]

theorem auth_001_crash_recovery : validateTrace trace_crash .Proposed = true := rfl

-- ===============================================================================
-- TEOREMAS INDUCTIVOS UNIVERSALES (Sobre cualquier traza finita arbitraria)
-- ===============================================================================

def countDispatches : List AuthEvent → Nat
  | [] => 0
  | .dispatch :: rest => 1 + countDispatches rest
  | _ :: rest => countDispatches rest

def maxAllowedDispatches : AuthState → Nat
  | .Proposed => 1
  | .Reserved => 1
  | .Dispatched => 0
  | .Executed => 0
  | .Unknown => 0

theorem max_dispatches_from_state (trace : List AuthEvent) (s : AuthState) :
  validateTrace trace s = true → countDispatches trace ≤ maxAllowedDispatches s := by
  induction trace generalizing s with
  | nil =>
    intro _
    cases s <;> decide
  | cons e rest ih =>
    intro h
    dsimp [validateTrace] at h
    cases hs : step s e with
    | none =>
      rw [hs] at h
      contradiction
    | some nextState =>
      rw [hs] at h
      have ih_res := ih nextState h
      cases s <;> cases e <;> (try revert hs; intro hs; contradiction)
      · -- Proposed, reserve -> Reserved
        injection hs with h_eq
        subst h_eq
        dsimp [countDispatches, maxAllowedDispatches]
        exact ih_res
      · -- Reserved, dispatch -> Dispatched
        injection hs with h_eq
        subst h_eq
        dsimp [countDispatches, maxAllowedDispatches]
        dsimp [maxAllowedDispatches] at ih_res
        have h_zero : countDispatches rest = 0 := Nat.le_zero.mp ih_res
        rw [h_zero]
        decide
      · -- Dispatched, ackSuccess -> Executed
        injection hs with h_eq
        subst h_eq
        dsimp [countDispatches, maxAllowedDispatches]
        exact ih_res
      · -- Dispatched, ackCrash -> Unknown
        injection hs with h_eq
        subst h_eq
        dsimp [countDispatches, maxAllowedDispatches]
        exact ih_res

/--
  TEOREMA CANÓNICO AUTH_001:
  Para CUALQUIER traza de longitud arbitraria, si la ejecución es válida
  comenzando en Proposed, el evento 'dispatch' ocurre como máximo UNA vez.
-/
theorem auth_001_universal_inductive_safety (trace : List AuthEvent) :
  validateTrace trace .Proposed = true → countDispatches trace ≤ 1 := by
  intro h
  have h_max := max_dispatches_from_state trace .Proposed h
  exact h_max

-- ===============================================================================
-- PURGA AXIOMÁTICA
-- ===============================================================================

/-- info: 'auth_001_valid_execution' does not depend on any axioms -/
#guard_msgs in
#print axioms auth_001_valid_execution

/-- info: 'auth_001_reject_double_dispatch' does not depend on any axioms -/
#guard_msgs in
#print axioms auth_001_reject_double_dispatch

/-- info: 'auth_001_universal_inductive_safety' depends on axioms: [propext] -/
#guard_msgs in
#print axioms auth_001_universal_inductive_safety


