/-
AUDITORÍA DE ALCANCE · 2026-10-25
FSM pura y seis ejemplos concretos de aceptación/rechazo. No prueba seguridad de todas las trazas, syscalls, sellos de memoria, persistencia WAL o permisos reales. Los nombres de eventos y campos no son observaciones del sistema operativo.
Nombres públicos preservados; este cambio solo corrige comentarios.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

/-! Sección del modelo discreto. El alcance de cada declaración depende de su tipo y sus hipótesis, no del nombre de la sección. -/

set_option warningAsError true

namespace NemesisWave4

/-- Etiquetas abstractas; no acceso a un WAL persistente. -/
inductive WalState where
  | none
  | attemptReserved
  | outcomeUnknown
  | outcomeKnown
deriving Repr, BEq, DecidableEq

/-- Etiquetas de clasificación, no comprobación del aislamiento del host. -/
inductive IsolationStrength where
  | kernelSealedMemfd
  | brokerQuarantinedSnapshot
  | degradedSameUidOrInProcess
deriving Repr, BEq, DecidableEq

/-- Contadores y flags del modelo del monitor. -/
structure ResourceMonitorState where
  durableEpoch    : Nat
  maxEffects      : Nat
  maxTotalBytes   : Nat
  usedEffects     : Nat
  usedBytes       : Nat
  allowedInode    : Nat
  walSlotState    : WalState
deriving Repr, BEq, DecidableEq

/-- Eventos abstractos de reserva, resultado y revocación. -/
inductive EcpEvent where
  | reserveAttempt (epoch : Nat) (targetIno : Nat) (bytes : Nat)
  | recordUnknown  (epoch : Nat)
  | recordKnown    (epoch : Nat)
  | blindRetry     (epoch : Nat)
  | revokeAndFence (newMinEpoch : Nat)
deriving Repr, BEq, DecidableEq

/-- Transición parcial definida por guards de la FSM; no ejecuta efectos externos. -/
def stepEcp (s : ResourceMonitorState) (ev : EcpEvent) : Option ResourceMonitorState :=
  match ev with
  | EcpEvent.reserveAttempt ep ino sz =>
    if ep == s.durableEpoch &&
       ino == s.allowedInode &&
       s.walSlotState == WalState.none &&
       s.usedEffects + 1 <= s.maxEffects &&
       s.usedBytes + sz <= s.maxTotalBytes then
      some { s with
        usedEffects  := s.usedEffects + 1
        usedBytes    := s.usedBytes + sz
        walSlotState := WalState.attemptReserved
      }
    else
      none
  | EcpEvent.recordUnknown ep =>
    if ep == s.durableEpoch && s.walSlotState == WalState.attemptReserved then
      some { s with walSlotState := WalState.outcomeUnknown }
    else
      none
  | EcpEvent.recordKnown ep =>
    if ep == s.durableEpoch &&
       (s.walSlotState == WalState.attemptReserved || s.walSlotState == WalState.outcomeUnknown) then
      some { s with walSlotState := WalState.outcomeKnown }
    else
      none
  | EcpEvent.blindRetry _ =>
    -- Prohibición estricta de reintento automático sobre estado reservado o desconocido
    none
  | EcpEvent.revokeAndFence k =>
    -- Revocación cercada: sólo avanza época cuando no hay intento en vuelo sin resolver
    if k > s.durableEpoch &&
       (s.walSlotState == WalState.none || s.walSlotState == WalState.outcomeKnown) then
      some { s with
        durableEpoch := k
        walSlotState := WalState.none
      }
    else
      none

/-- Verifica que cada paso de una lista sea admitido por stepEcp. -/
def validateEcpTrace (s : ResourceMonitorState) : List EcpEvent → Bool
  | [] => true
  | ev :: rest =>
    match stepEcp s ev with
    | some s' => validateEcpTrace s' rest
    | none    => false

/-- Clasifica flags suministrados; no consulta seals o protección de memoria del SO. -/
def evaluateSealStrength
    (hasWritableSharedMapping : Bool)
    (sealsVerifiedByGetSeals : Bool)
    (reliesOnSameProcessMprotect : Bool)
    (reliesOnSameUidUfImmutable : Bool) : Option IsolationStrength :=
  if hasWritableSharedMapping || !sealsVerifiedByGetSeals then
    none
  else if reliesOnSameProcessMprotect || reliesOnSameUidUfImmutable then
    some IsolationStrength.degradedSameUidOrInProcess
  else
    some IsolationStrength.kernelSealedMemfd

/-- Compara argumentos Nat; no autentica firma o inspecciona dependencias externas. -/
def validateDeploymentPermit
    (permitClosureRoot actualClosureRoot : Nat)
    (permitPolicyEpoch minPolicyEpoch : Nat)
    (currentTick expiresAt : Nat) : Bool :=
  (permitClosureRoot == actualClosureRoot) &&
  (permitPolicyEpoch >= minPolicyEpoch) &&
  (currentTick < expiresAt)

/-- Registro inicial usado en las trazas concretas de prueba. -/
def initialMonitor : ResourceMonitorState := {
  durableEpoch  := 1
  maxEffects    := 2
  maxTotalBytes := 15
  usedEffects   := 0
  usedBytes     := 0
  allowedInode  := 1001
  walSlotState  := WalState.none
}

/-- Una lista concreta admitida por el monitor. -/
def validWave4Trace : List EcpEvent := [
  EcpEvent.reserveAttempt 1 1001 10,
  EcpEvent.recordKnown 1,
  EcpEvent.revokeAndFence 2,
  EcpEvent.reserveAttempt 2 1001 5,
  EcpEvent.recordKnown 2
]

/-- Una lista concreta con reserva en época obsoleta. -/
def corruptFencingRaceTrace : List EcpEvent := [
  EcpEvent.reserveAttempt 1 1001 5,
  EcpEvent.recordKnown 1,
  EcpEvent.revokeAndFence 2,
  EcpEvent.reserveAttempt 1 1001 5
]

/-- Una lista concreta con reintento que la FSM rechaza. -/
def corruptBlindRetryTrace : List EcpEvent := [
  EcpEvent.reserveAttempt 1 1001 10,
  EcpEvent.recordUnknown 1,
  EcpEvent.blindRetry 1
]

/-- Una lista concreta que supera el presupuesto declarado. -/
def corruptBudgetCompositionTrace : List EcpEvent := [
  EcpEvent.reserveAttempt 1 1001 10,
  EcpEvent.recordKnown 1,
  EcpEvent.revokeAndFence 2,
  EcpEvent.reserveAttempt 2 1001 10
]

/-- Aceptación de validWave4Trace, sin cuantificación universal sobre trazas. -/
theorem ecp_v2_valid_trace_certified :
    validateEcpTrace initialMonitor validWave4Trace = true := by decide

/-- Rechazo de corruptFencingRaceTrace concreta; no cuantifica sobre todas las carreras de fencing. -/
theorem fl014_fencing_race_rejected :
    validateEcpTrace initialMonitor corruptFencingRaceTrace = false := by decide

/-- Rechazo de corruptBlindRetryTrace concreta. -/
theorem fl014_blind_retry_rejected :
    validateEcpTrace initialMonitor corruptBlindRetryTrace = false := by decide

/-- Rechazo de corruptBudgetCompositionTrace concreta. -/
theorem fl014_budget_composition_rejected :
    validateEcpTrace initialMonitor corruptBudgetCompositionTrace = false := by decide

/-- Ejemplo de una función sobre flags suministrados; no consulta Darwin, mprotect o flags reales. -/
theorem fl013_darwin_uf_immutable_degraded :
    evaluateSealStrength false true false true = some IsolationStrength.degradedSameUidOrInProcess := by decide

/-- Una comparación de dos roots Nat concretos retorna false; no inspecciona la clausura transitiva de un despliegue. -/
theorem fl015_transitive_drift_rejected :
    validateDeploymentPermit 0xAAA1 0xBBB2 5 5 100 500 = false := by decide

/-- info: 'NemesisWave4.ecp_v2_valid_trace_certified' does not depend on any axioms -/
#guard_msgs in
#print axioms ecp_v2_valid_trace_certified

/-- info: 'NemesisWave4.fl014_fencing_race_rejected' does not depend on any axioms -/
#guard_msgs in
#print axioms fl014_fencing_race_rejected

/-- info: 'NemesisWave4.fl014_blind_retry_rejected' does not depend on any axioms -/
#guard_msgs in
#print axioms fl014_blind_retry_rejected

/-- info: 'NemesisWave4.fl014_budget_composition_rejected' does not depend on any axioms -/
#guard_msgs in
#print axioms fl014_budget_composition_rejected

/-- info: 'NemesisWave4.fl013_darwin_uf_immutable_degraded' does not depend on any axioms -/
#guard_msgs in
#print axioms fl013_darwin_uf_immutable_degraded

/-- info: 'NemesisWave4.fl015_transitive_drift_rejected' does not depend on any axioms -/
#guard_msgs in
#print axioms fl015_transitive_drift_rejected

end NemesisWave4
