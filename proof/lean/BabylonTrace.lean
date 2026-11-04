/-
AUDITORÍA DE ALCANCE · 2026-10-25
Modelo de eventos con secuencias declaradas y autor del escritor. Los teoremas no modelan payload ni cargas físicas de memoria; no_torn_reads_universal expresa paridad de los eventos aceptados, no ausencia universal de torn reads en Rust.
Nombres públicos preservados; este cambio solo corrige comentarios.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

import Init

namespace B60.Ledger

-- 1. ESTRUCTURAS EMPÍRICAS (Físicamente reducibles)
-- `deriving Repr, BEq, DecidableEq` es el blindaje crítico. 
-- Obliga a Lean a generar código C nativo para comparar estas estructuras en memoria (==).
inductive Action where
  | writeBegin
  | writeEnd
  | read
  deriving Repr, BEq, DecidableEq

structure Event where
  threadId : Nat
  seq      : Nat
  action   : Action
  deriving Repr, BEq, DecidableEq

structure LockState where
  seq    : Nat
  writer : Option Nat
  deriving Repr, BEq, DecidableEq

-- 2. EL MOTOR DE CAUSALIDAD (Transición de Estado Determinista)
-- Evalúa la física del Seqlock: Par = Reposo, Impar = Mutación.
-- Retorna `Option LockState`: el nuevo estado si la entropía es 0, o `none` si hay paradoja.
def step (state : LockState) (event : Event) : Option LockState :=
  match event.action with
  | Action.writeBegin =>
      -- LEY 1: Un WriteBegin DEBE transicionar de estado par a impar rígidamente.
      if state.seq % 2 == 0 && event.seq == state.seq + 1 && state.writer == none then
        some { seq := event.seq, writer := some event.threadId }
      else 
        none
        
  | Action.writeEnd =>
      -- LEY 2: Un WriteEnd DEBE cerrar la secuencia a par, y solo por el autor original.
      if state.seq % 2 == 1 && event.seq == state.seq + 1 && state.writer == some event.threadId then
        some { seq := event.seq, writer := none }
      else 
        none
        
  | Action.read =>
      -- LEY 3: La secuencia declarada por el lector es par y no futura.
      -- No se modelan payload, cargas físicas ni dos versiones de un snapshot.
      if event.seq % 2 == 0 && event.seq <= state.seq then
        some state -- Las lecturas puras no alteran la memoria causal global
      else 
        none

-- 3. INGESTA ESTRICTA FUNCIONAL O(N) Y ENCADENAMIENTO DE AEONES
-- `runAeon` propaga el estado exacto del LockState al finalizar el bloque de eventos.
def runAeon : Option LockState → List Event → Option LockState
  | none, _ => none
  | some state, [] => some state
  | some state, ev :: rest => runAeon (step state ev) rest

def validateTraceRecursive (s : Option LockState) (trace : List Event) : Bool :=
  match runAeon s trace with
  | some _ => true
  | none => false

def validateTrace (trace : List Event) : Bool :=
  validateTraceRecursive (some { seq := 0, writer := none }) trace

-- ============================================================================
-- 4. EL TRIBUNAL DE REFLEXIÓN (Simulador de la Pasarela Rust)
-- ============================================================================

-- [ LA INYECCIÓN ]: Una traza válida empírica simulada
def trace_perfect : List Event := [
  { threadId := 1, seq := 1, action := Action.writeBegin },
  { threadId := 1, seq := 2, action := Action.writeEnd },
  { threadId := 2, seq := 2, action := Action.read },
  { threadId := 3, seq := 3, action := Action.writeBegin },
  { threadId := 3, seq := 4, action := Action.writeEnd }
]

-- ⚡ EL TEOREMA A+ (End-to-End Core) ⚡
-- Al usar `by decide`, Lean 4 aborta la búsqueda lógica profunda. 
-- Compila `validateTrace` a código binario, lo ejecuta a máxima velocidad 
-- contra la lista, ve que la ALU devuelve `true`, y SELLA el teorema en su Kernel.
theorem trace_is_paradox_free : validateTrace trace_perfect = true := by
  decide

-- [ LA PARADOJA ]: Una traza corrupta simulada (Torn Read / Colisión Temporal)
def trace_corrupt : List Event := [
  { threadId := 1, seq := 1, action := Action.writeBegin },
  { threadId := 2, seq := 1, action := Action.read }, -- PARADOJA: Leyendo estado impar (en mutación)
  { threadId := 1, seq := 2, action := Action.writeEnd }
]

-- ============================================================================
-- 5. TEOREMAS INDUCTIVOS UNIVERSALES (Paridad de secuencias de lectura declaradas)
-- ============================================================================

def TraceReadsEven : List Event → Prop
  | [] => True
  | ev :: rest => (ev.action = Action.read → ev.seq % 2 = 0) ∧ TraceReadsEven rest

theorem step_read_even (s : LockState) (ev : Event) (next : LockState) :
  step s ev = some next → (ev.action = Action.read → ev.seq % 2 = 0) := by
  intro h_step h_read
  dsimp [step] at h_step
  cases h_act : ev.action with
  | read =>
    rw [h_act] at h_step
    dsimp at h_step
    split at h_step
    · rename_i h_cond
      have h_even : (ev.seq % 2 == 0) = true := (Bool.and_eq_true _ _).mp h_cond |>.1
      exact of_decide_eq_true h_even
    · contradiction
  | writeBegin =>
    rw [h_act] at h_read
    contradiction
  | writeEnd =>
    rw [h_act] at h_read
    contradiction

theorem runAeon_reads_even (s : LockState) (trace : List Event) (finalState : LockState) :
  runAeon (some s) trace = some finalState → TraceReadsEven trace := by
  induction trace generalizing s with
  | nil =>
    intro _
    exact trivial
  | cons ev rest ih =>
    intro h
    dsimp [runAeon] at h
    cases hs : step s ev with
    | none =>
      rw [hs] at h
      simp [runAeon] at h
    | some s' =>
      rw [hs] at h
      have h_ev := step_read_even s ev s' hs
      have h_rest := ih s' h
      exact ⟨h_ev, h_rest⟩

/--
  TEOREMA CANÓNICO SEQLOCK (C5-REAL):
  Para CUALQUIER traza de longitud arbitraria, si la ejecución es válida
  a partir del estado inicial en reposo (seq=0, writer=none), TODA lectura
  declara una secuencia par. No implica que el estado global sea par durante
  la lectura ni demuestra coherencia del payload o ausencia física de torn reads.
  El nombre histórico se conserva por compatibilidad con consumidores.
-/
theorem no_torn_reads_universal (trace : List Event) :
  validateTrace trace = true → TraceReadsEven trace := by
  intro h
  dsimp [validateTrace, validateTraceRecursive] at h
  cases h_aeon : runAeon (some { seq := 0, writer := none }) trace with
  | none =>
    rw [h_aeon] at h
    contradiction
  | some finalState =>
    exact runAeon_reads_even { seq := 0, writer := none } trace finalState h_aeon

/-- Testigo de firma anti-debilitamiento (bloquea mutación m3 de tautología vacía) -/
abbrev NoTornReadsProp : Prop :=
  ∀ (trace : List Event), validateTrace trace = true → TraceReadsEven trace

example : NoTornReadsProp := no_torn_reads_universal

/--
info: no_torn_reads_universal : ∀ (trace : List Event), validateTrace trace = true → TraceReadsEven trace
-/
#guard_msgs in
#check @no_torn_reads_universal

/-- info: 'B60.Ledger.no_torn_reads_universal' depends on axioms: [propext] -/
#guard_msgs in
#print axioms no_torn_reads_universal

-- Contraejemplo explícito al claim más fuerte: se admite una secuencia pasada
-- par mientras existe un escritor activo. Es alcance del modelo, no evidencia física.
example : step { seq := 1, writer := some 1 }
    { threadId := 2, seq := 0, action := Action.read } =
    some { seq := 1, writer := some 1 } := by decide

-- El contador wire de 32 bits no puede envolver en el modelo Nat.
example : step { seq := 4294967295, writer := some 1 }
    { threadId := 1, seq := 0, action := Action.writeEnd } = none := by decide

-- ============================================================================
-- 6. TRANSICIÓN BICAMERAL (FL-011 + LARSA): B60-01 / B60-02 / B60-03 / B60-05
-- ============================================================================

structure BabylonEvent where
  agentId         : Nat
  seqStart        : Nat
  seqEnd          : Nat
  kernelEpoch     : Nat
  leaseEpoch      : Nat
  formalWitnessOk : Bool
  formalVeto      : Bool
  heuristicWeight : Nat
  quorumThreshold : Nat
  deriving Repr, DecidableEq

/-- Predicado unificado FL-011 (Seqlock + Lease) y LARSA bicameral. -/
def ValidBabylonTransition (e : BabylonEvent) : Prop :=
  (e.seqStart % 2 = 0) ∧
  (e.seqStart = e.seqEnd) ∧
  (e.kernelEpoch ≤ e.leaseEpoch) ∧
  (e.formalWitnessOk = true) ∧
  (e.formalVeto = false) ∧
  (e.quorumThreshold ≤ e.heuristicWeight)

instance (e : BabylonEvent) : Decidable (ValidBabylonTransition e) := by
  unfold ValidBabylonTransition
  exact inferInstance

/-- B60-01: ninguna mayoría heurística valida una transición con veto formal. -/
theorem no_heuristic_override_on_veto (e : BabylonEvent)
    (h_veto : e.formalVeto = true) : ¬ ValidBabylonTransition e := by
  intro h_valid
  rcases h_valid with ⟨_, _, _, _, h_no_veto, _⟩
  rw [h_veto] at h_no_veto
  contradiction

/-- B60-01 (dual): sin testigo formal no hay transición válida, con cualquier peso. -/
theorem no_commit_without_witness (e : BabylonEvent)
    (h_nw : e.formalWitnessOk = false) : ¬ ValidBabylonTransition e := by
  intro h_valid
  rcases h_valid with ⟨_, _, _, h_w, _, _⟩
  rw [h_nw] at h_w
  contradiction

/-- B60-02: un lease expirado respecto al kernelEpoch jamás es válido. -/
theorem expired_lease_rejected (e : BabylonEvent)
    (h_exp : e.leaseEpoch < e.kernelEpoch) : ¬ ValidBabylonTransition e := by
  intro h_valid
  rcases h_valid with ⟨_, _, h_lease, _, _, _⟩
  omega

/-- B60-03: seq impar o desgarro (seqStart ≠ seqEnd) aborta. -/
theorem fl011_seqlock_integrity (e : BabylonEvent)
    (h_valid : ValidBabylonTransition e) :
    e.seqStart % 2 = 0 ∧ e.seqStart = e.seqEnd := by
  rcases h_valid with ⟨h_even, h_eq, _, _, _, _⟩
  exact ⟨h_even, h_eq⟩

theorem torn_seq_rejected (e : BabylonEvent)
    (h_torn : e.seqStart ≠ e.seqEnd) : ¬ ValidBabylonTransition e := by
  intro h_valid
  exact h_torn (fl011_seqlock_integrity e h_valid).2

/-- Evento positivo de control: la transición válida existe (no vacuidad). -/
def trace_step_ok : BabylonEvent :=
  { agentId := 0, seqStart := 2, seqEnd := 2, kernelEpoch := 10, leaseEpoch := 15,
    formalWitnessOk := true, formalVeto := false, heuristicWeight := 100, quorumThreshold := 100 }

theorem trace_step_ok_valid : ValidBabylonTransition trace_step_ok := by
  decide

/-- info: 'B60.Ledger.no_heuristic_override_on_veto' does not depend on any axioms -/
#guard_msgs in
#print axioms no_heuristic_override_on_veto

/-- info: 'B60.Ledger.no_commit_without_witness' does not depend on any axioms -/
#guard_msgs in
#print axioms no_commit_without_witness

/-- info: 'B60.Ledger.fl011_seqlock_integrity' does not depend on any axioms -/
#guard_msgs in
#print axioms fl011_seqlock_integrity

-- ============================================================================
-- 7. FL-018 COMPOSITE SAFETY GATE & FL-026 BOUND WITNESS (BitVec 64)
-- ============================================================================

structure CompositeGateState where
  requiredCriticalMask : BitVec 64
  verifiedCriticalMask : BitVec 64
  acceptedArtifactHash : BitVec 64
  verifiedArtifactHash : BitVec 64
  minPolicyEpoch       : BitVec 64
  evidenceEpoch        : BitVec 64
  heuristicWeight      : BitVec 64
  quorumThreshold      : BitVec 64
  deriving Repr, DecidableEq

/-- Predicado conjuntivo FL-018 + FL-026/H4 en aritmética de ancho fijo BitVec 64. -/
def ValidCompositeAcceptance (s : CompositeGateState) : Prop :=
  (s.requiredCriticalMask ≠ 0#64) ∧
  ((s.verifiedCriticalMask &&& s.requiredCriticalMask) = s.requiredCriticalMask) ∧
  (s.acceptedArtifactHash = s.verifiedArtifactHash) ∧
  (s.minPolicyEpoch ≤ s.evidenceEpoch) ∧
  (0#64 < s.quorumThreshold) ∧
  (s.quorumThreshold ≤ s.heuristicWeight)

instance (s : CompositeGateState) : Decidable (ValidCompositeAcceptance s) := by
  unfold ValidCompositeAcceptance
  exact inferInstance

/-- B60-06 (FL-018): cualquier bit crítico obligatorio no verificado invalida la aceptación,
    sin importar cuántos otros controles hayan pasado. -/
theorem fl018_missing_critical_check_rejected (s : CompositeGateState)
    (h_incomplete : (s.verifiedCriticalMask &&& s.requiredCriticalMask) ≠ s.requiredCriticalMask) :
    ¬ ValidCompositeAcceptance s :=
  fun h_valid => h_incomplete h_valid.2.1

/-- B60-07 (FL-018): si el hash del artefacto aceptado difiere del verificado, se rechaza. -/
theorem fl018_artifact_hash_mismatch_rejected (s : CompositeGateState)
    (h_diff : s.acceptedArtifactHash ≠ s.verifiedArtifactHash) :
    ¬ ValidCompositeAcceptance s :=
  fun h_valid => h_diff h_valid.2.2.1

/-- B60-08 (FL-018): evidencia de una época anterior a minPolicyEpoch es rechazada. -/
theorem fl018_stale_epoch_rejected (s : CompositeGateState)
    (h_stale : ¬ (s.minPolicyEpoch ≤ s.evidenceEpoch)) :
    ¬ ValidCompositeAcceptance s :=
  fun h_valid => h_stale h_valid.2.2.2.1

/-- B60-09 (FL-026/H4): un umbral heurístico nulo (0#64) jamás produce aceptación válida. -/
theorem fl026_zero_threshold_rejected (s : CompositeGateState)
    (h_zero : s.quorumThreshold = 0#64) :
    ¬ ValidCompositeAcceptance s := by
  intro h_valid
  have h_pos := h_valid.2.2.2.2.1
  rw [h_zero] at h_pos
  contradiction

/-- Testigo constructivo de no-vacuidad (INV_C5_NON_VACUITY_WITNESS). -/
def composite_gate_ok : CompositeGateState :=
  { requiredCriticalMask := 0x7FF#64,
    verifiedCriticalMask := 0x7FF#64,
    acceptedArtifactHash := 0xCAFE_BABE_0000_0001#64,
    verifiedArtifactHash := 0xCAFE_BABE_0000_0001#64,
    minPolicyEpoch       := 40#64,
    evidenceEpoch        := 40#64,
    heuristicWeight      := 10#64,
    quorumThreshold      := 3#64 }

theorem composite_gate_ok_valid : ValidCompositeAcceptance composite_gate_ok := by
  decide

theorem fl018_composite_acceptance_inhabited : ∃ s : CompositeGateState, ValidCompositeAcceptance s :=
  ⟨composite_gate_ok, composite_gate_ok_valid⟩

/-- Contraejemplo PLE (90.9% = 10/11 bits críticos verificados: 0x3FF vs 0x7FF) rechazado por decisión. -/
def composite_gate_ple_91pct_fail : CompositeGateState :=
  { composite_gate_ok with verifiedCriticalMask := 0x3FF#64 }

theorem composite_gate_ple_91pct_rejected : ¬ ValidCompositeAcceptance composite_gate_ple_91pct_fail := by
  decide

/-- info: 'B60.Ledger.fl018_missing_critical_check_rejected' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms fl018_missing_critical_check_rejected

/-- info: 'B60.Ledger.fl018_artifact_hash_mismatch_rejected' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms fl018_artifact_hash_mismatch_rejected

/-- info: 'B60.Ledger.fl018_stale_epoch_rejected' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms fl018_stale_epoch_rejected

/-- info: 'B60.Ledger.fl026_zero_threshold_rejected' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms fl026_zero_threshold_rejected

/-- info: 'B60.Ledger.fl018_composite_acceptance_inhabited' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms fl018_composite_acceptance_inhabited

end B60.Ledger


