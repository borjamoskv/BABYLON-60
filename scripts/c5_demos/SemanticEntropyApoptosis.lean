-- Modelo de clasificación de resúmenes de entropía y resultado tipado suministrado.
-- Constantes alineadas con semantic_entropy.rs; no calcula ni valida matrices.
-- Verified y Apoptosis son constructores puros: no prueban verdad ni ejecutan efectos.

namespace Babylon60.Epistemology

set_option warningAsError true

def tauSemQ16 : Nat := 55706
def errConfabulation : Nat := 0xDEAD_6060
def errIncorrectBelief : Nat := 0xDEAD_6061

-- 1. Resultado externo declarado; este tipo no autentica ni ejecuta un solver.
inductive SolverError where
  | Timeout
  | Transport
  | Protocol
  | Execution
  deriving Repr, DecidableEq

inductive SolverOutcome where
  | Sat
  | Unsat
  | Unknown
  | Error (reason : SolverError)
  deriving Repr, DecidableEq

-- Estados abstractos; Verified agrupa las dos variantes positivas de Rust.
inductive CausalStatus where
  | Pending
  | Verified
  | Apoptosis (code : Nat)
  | SolverUnknown
  | SolverFailure (reason : SolverError)
  deriving Repr, DecidableEq

-- 2. Resumen suministrado; la validez de la partición queda fuera de este modelo.
structure CausalClaim where
  claimId     : Nat
  hSemScaled  : Nat   -- Q16; para una partición válida n≤8 el máximo es 196608.
  tauSem      : Nat   -- Nat no impone cotas; el perfil Rust usa 55706 ≈ 0.85 bits.
  solverOutcome : SolverOutcome  -- Resultado externo, sin evidencia factual.
  deriving Repr, DecidableEq

-- 3. UNKNOWN/error no son UNSAT. Los errores de matriz quedan fuera del resumen.
def evaluateCausalGate (claim : CausalClaim) : CausalStatus :=
  match claim.solverOutcome with
  | .Sat => .Verified
  | .Unsat =>
    if claim.hSemScaled > claim.tauSem then
      .Apoptosis errConfabulation
    else
      .Apoptosis errIncorrectBelief
  | .Unknown => .SolverUnknown
  | .Error reason => .SolverFailure reason

-- 4. Resúmenes sintéticos de los cuatro cuadrantes; nombres históricos conservados.
def claim_genuine : CausalClaim :=
  { claimId := 1, hSemScaled := 1200, tauSem := tauSemQ16, solverOutcome := .Sat }

def claim_confabulation : CausalClaim :=
  { claimId := 2, hSemScaled := 58000, tauSem := tauSemQ16, solverOutcome := .Unsat }

def claim_incorrect_belief : CausalClaim :=
  { claimId := 3, hSemScaled := 800, tauSem := tauSemQ16, solverOutcome := .Unsat }

def claim_polysemy : CausalClaim :=
  { claimId := 4, hSemScaled := 63633, tauSem := tauSemQ16, solverOutcome := .Sat }

-- 5. Teoremas de Demostración por Reflexión (`by decide`)

-- Evaluación cerrada de Sat suministrado; no expresa una transición de producción.
theorem genuine_knowledge_is_verified :
  evaluateCausalGate claim_genuine = CausalStatus.Verified := by
  decide

-- Evaluación cerrada de Unsat y entropía alta; sufijo histórico del nombre.
theorem confabulation_triggers_0x6060 :
  evaluateCausalGate claim_confabulation = CausalStatus.Apoptosis errConfabulation := by
  decide

-- Evaluación cerrada de Unsat y entropía baja; no demuestra falsedad factual.
theorem incorrect_belief_triggers_0x6061 :
  evaluateCausalGate claim_incorrect_belief = CausalStatus.Apoptosis errIncorrectBelief := by
  decide

-- Evaluación cerrada de Sat y entropía alta.
theorem polysemy_is_verified :
  evaluateCausalGate claim_polysemy = CausalStatus.Verified := by
  decide

-- Propiedad de la clasificación; no prueba procedencia ni corrección del resultado.
theorem verified_requires_solver_sat (claim : CausalClaim)
    (h : evaluateCausalGate claim = CausalStatus.Verified) :
    claim.solverOutcome = SolverOutcome.Sat := by
  cases hs : claim.solverOutcome with
  | Sat => rfl
  | Unsat =>
    unfold evaluateCausalGate at h
    rw [hs] at h
    by_cases high : claim.hSemScaled > claim.tauSem
    · rw [ite_eq_left high] at h
      cases h
    · rw [ite_eq_right high] at h
      cases h
  | Unknown =>
    unfold evaluateCausalGate at h
    rw [hs] at h
    cases h
  | Error reason =>
    unfold evaluateCausalGate at h
    rw [hs] at h
    cases h

-- Nombre histórico conservado: Unsat no equivale a falsedad factual ni a un commit.
theorem falsity_never_reaches_ring1_commit (claim : CausalClaim)
    (h : claim.solverOutcome = SolverOutcome.Unsat) :
    evaluateCausalGate claim ≠ CausalStatus.Verified := by
  intro accepted
  have sat := verified_requires_solver_sat claim accepted
  rw [h] at sat
  cases sat

theorem solver_sat_is_verified (claim : CausalClaim)
    (h : claim.solverOutcome = SolverOutcome.Sat) :
    evaluateCausalGate claim = CausalStatus.Verified := by
  unfold evaluateCausalGate
  rw [h]

theorem verified_iff_solver_sat (claim : CausalClaim) :
    evaluateCausalGate claim = CausalStatus.Verified ↔
      claim.solverOutcome = SolverOutcome.Sat :=
  Iff.intro (verified_requires_solver_sat claim) (solver_sat_is_verified claim)

theorem unknown_never_reaches_verified (claim : CausalClaim)
    (h : claim.solverOutcome = SolverOutcome.Unknown) :
    evaluateCausalGate claim ≠ CausalStatus.Verified := by
  intro accepted
  have sat := verified_requires_solver_sat claim accepted
  rw [h] at sat
  cases sat

theorem solver_error_never_reaches_verified (claim : CausalClaim) (reason : SolverError)
    (h : claim.solverOutcome = SolverOutcome.Error reason) :
    evaluateCausalGate claim ≠ CausalStatus.Verified := by
  intro accepted
  have sat := verified_requires_solver_sat claim accepted
  rw [h] at sat
  cases sat

end Babylon60.Epistemology
