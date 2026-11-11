/**
 * Superficie pública del paquete.
 *
 * - `verifyExecutionPayload` / `verifyExecutionPayloadJson`: verificación fail-closed de un recibo.
 * - `DeterministicDagViewer`, `TwoPhaseSealInspector`, `StaticReceiptReport`: vistas que solo
 *   dibujan un `AcceptedReceipt`.
 * - `BabylonKernelConsole`: consola de demostración con escenarios adversariales.
 */

export { BabylonKernelConsole } from "./components/BabylonKernelConsole.tsx";
export { DeterministicDagViewer } from "./components/DeterministicDagViewer.tsx";
export { StaticReceiptReport } from "./components/StaticReceiptReport.tsx";
export { TwoPhaseSealInspector } from "./components/TwoPhaseSealInspector.tsx";
export {
  LIMITS,
  MAX_ADMITTED_AUTHORITIES,
  MAX_JSON_TEXT_LENGTH,
  createReceiptVerifier,
  isAcceptedReceipt,
  rejectionVerdict,
  verifyExecutionPayload,
  verifyExecutionPayloadJson,
  verifyExecutionPayloadUtf8,
  verifyExecutionPayloadWithAnchorText,
  parseAnchorText,
  MAX_ANCHOR_TEXT_LENGTH,
} from "./crypto/sealVerifier.ts";
export { MAX_JSON_DEPTH } from "./crypto/jsonText.ts";
export type { ReceiptVerifier, VerifierEnvironment } from "./crypto/sealVerifier.ts";
export type {
  AcceptedReceipt,
  AssuranceLevel,
  AssuranceReport,
  Babylon60ExecutionPayload,
  CausalLogicalClock,
  ChainCheckpoint,
  ExecutionDagNode,
  FailureDiagnostics,
  LarsaCommitDeclaration,
  Lean4ProofAttestation,
  NodeStateStatus,
  PolicyProfile,
  SealFailure,
  SealFailureCode,
  TrustPolicy,
  TwoPhaseCryptographicSeal,
  VerificationVerdict,
  WormAuditMetrics,
} from "./types/babylon60.ts";
