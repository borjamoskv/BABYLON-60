/**
 * Contratos de tipos del recibo de ejecución que verifica el cliente.
 *
 * Dos niveles, que el compilador mantiene separados:
 *  - lo que llega por el transporte es `unknown` y solo `verifyExecutionPayload` lo interpreta;
 *  - `AcceptedReceipt` es opaco: únicamente lo construye el verificador cuando todas las
 *    comprobaciones pasan, y los componentes de la interfaz solo aceptan ese tipo para dibujar.
 *
 * Los tipos con marca (`Hex32`, `Hex64`, `B3Root`) no se obtienen por conversión directa de un
 * `string`: solo los emite la validación estructural, de modo que llevar el tipo implica haber
 * pasado el formato estricto (minúsculas, longitud exacta).
 */

export type PolicyProfile = "STRICT_DETERMINISTIC" | "BFT_DEFENSIVE" | "NEMESIS_ADVERSARIAL";

export type NodeStateStatus = "COMMITTED" | "REJECTED_POLICY" | "INTERCEPTED_NEMESIS" | "PENDING_SEAL";

export type Lean4ProofStatus = "VERIFIED_NO_SORRY" | "FAILED_INVARIANT";

declare const hex32Brand: unique symbol;
declare const hex64Brand: unique symbol;
declare const b3RootBrand: unique symbol;

/** `0x` + 64 dígitos hex en minúsculas (32 bytes). */
export type Hex32 = `0x${string}` & { readonly [hex32Brand]: true };
/** `0x` + 128 dígitos hex en minúsculas (64 bytes, firma Ed25519). */
export type Hex64 = `0x${string}` & { readonly [hex64Brand]: true };
/** Raíz Merkle v1 etiquetada: `b3:` + 64 dígitos hex en minúsculas. */
export type B3Root = `b3:${string}` & { readonly [b3RootBrand]: true };

/** Tiempo lógico causal. Enteros en [0, 2^53 − 1]; ningún reloj físico entra en hashes canónicos. */
export interface CausalLogicalClock {
  readonly policy_epoch: number;
  readonly logical_tick: number;
  readonly seq_id: number;
}

export interface ExecutionDagNode {
  /** Identificador canónico de evento `EV_{tick:08}_{seq:06}` (`INV_C5_DAG_EVENT_ID`). */
  readonly node_id: string;
  /** Identificadores de los padres causales; sin duplicados ni autorreferencia. */
  readonly parent_ids: readonly string[];
  readonly state_status: NodeStateStatus;
  readonly smt_verified: boolean;
  /** Coste determinista en pasos de reducción (gas lógico), no tiempo de reloj. */
  readonly reduction_steps: number;
  /**
   * Hash de hoja Merkle v1 del nodo:
   * `BLAKE3("B60-LEAF-v1\0" || CBOR(["B60-EXEC-NODE-v1", node_id, padres_ordenados, state_status,
   * smt_verified, reduction_steps, violation_reason]))`.
   */
  readonly state_hash: Hex32;
  readonly violation_reason: string | null;
}

export interface Lean4ProofAttestation {
  readonly status: Lean4ProofStatus;
  readonly theorem_ident: string;
  readonly sorry_count: number;
}

/**
 * Commit LARSA con los dos campos que define el kernel (`ConsensusOutcome::Committed`): el hash de
 * la traza asociada al testigo formal y el peso heurístico acumulado. El peso exigido NO viaja en el
 * recibo: lo fija quien verifica (`TrustPolicy.larsa_required_weight`), igual que en `BicameralQuorum`.
 */
export interface LarsaCommitDeclaration {
  readonly trace_hash: Hex32;
  /** Entero en [0, 2^32 − 1] (u32 en el kernel). */
  readonly heuristic_weight: number;
}

export interface TwoPhaseCryptographicSeal {
  /** Fase 1: compromiso con el manifiesto de entrada (el cliente lo recalcula desde `ingress`). */
  readonly phase_one_manifest_hash: Hex32;
  /** Fase 2: raíz Merkle v1 del DAG de ejecución (el cliente la recalcula hoja a hoja). */
  readonly phase_two_merkle_root: B3Root;
  /**
   * Clave que firma el sobre. Solo sirve para elegir entre las autoridades admitidas por el
   * verificador: una clave que no esté en `TrustPolicy.admitted_authorities` se rechaza.
   */
  readonly ed25519_public_key: Hex32;
  /** Firma Ed25519 del Sig_structure COSE_Sign1 del sobre canónico. */
  readonly ed25519_signature: Hex64;
  /** Declaración del emisor, cubierta por la firma; el cliente no observa el consenso. */
  readonly larsa_commit: LarsaCommitDeclaration;
  /** Declaración del emisor, cubierta por la firma; el cliente no ejecuta Lean. */
  readonly lean4_proof: Lean4ProofAttestation;
}

export interface WormAuditMetrics {
  readonly memory_bytes: number;
  readonly prev_receipt_hash: Hex32;
  readonly worm_txid: Hex32;
}

export interface IngressManifest {
  readonly agent_id: string;
  readonly policy_profile: PolicyProfile;
  readonly payload_raw: string;
}

export interface Babylon60ExecutionPayload {
  readonly execution_id: string;
  readonly causal_clock: CausalLogicalClock;
  readonly manifest_version: string;
  readonly ingress: IngressManifest;
  readonly execution_dag: readonly ExecutionDagNode[];
  readonly cryptographic_seal: TwoPhaseCryptographicSeal;
  readonly audit_metrics: WormAuditMetrics;
}

// ---------------------------------------------------------------------------------------------
// Ancla de confianza: la aporta la aplicación anfitriona, nunca el payload.
// ---------------------------------------------------------------------------------------------

/** Punto de control del recibo anterior, si el anfitrión lo conoce. */
export interface ChainCheckpoint {
  /** `receipt_hash` del recibo inmediatamente anterior: `0x` + 64 dígitos hex en minúsculas. */
  readonly receipt_hash: string;
  readonly seq_id: number;
}

export interface TrustPolicy {
  /**
   * Claves públicas Ed25519 admitidas (`0x` + 64 dígitos hex en minúsculas), provistas por un canal
   * de confianza. Basta la firma válida de una de ellas, como en `admitted_authorities` del ejecutor.
   */
  readonly admitted_authorities: readonly string[];
  /** Peso heurístico LARSA mínimo exigido, entero en [1, 2^32 − 1]. */
  readonly larsa_required_weight: number;
  /** Si se aporta, el recibo debe encadenar con él; si no, el encadenamiento queda NO_VERIFICADO. */
  readonly previous_receipt?: ChainCheckpoint;
}

// ---------------------------------------------------------------------------------------------
// Veredicto
// ---------------------------------------------------------------------------------------------

export type SealFailureCode =
  | "TRUST_POLICY_INVALID"
  | "SCHEMA_INVALID"
  | "SCHEMA_MALFORMED_HEX"
  | "LIMIT_EXCEEDED"
  | "DAG_EMPTY"
  | "DAG_DUPLICATE_NODE_ID"
  | "DAG_DUPLICATE_PARENT_REF"
  | "DAG_DANGLING_PARENT_REF"
  | "DAG_CYCLE_DETECTED"
  | "COMMITTED_WITHOUT_SMT"
  | "LEAF_HASH_MISMATCH"
  | "MERKLE_ROOT_MISMATCH"
  | "MANIFEST_HASH_MISMATCH"
  | "QUORUM_INSUFFICIENT"
  | "LEAN4_PROOF_INVALID"
  | "AUTHORITY_NOT_ADMITTED"
  | "ED25519_UNSUPPORTED_RUNTIME"
  | "ED25519_SIGNATURE_INVALID"
  | "CHAIN_LINK_MISMATCH"
  | "VERIFIER_INTERNAL_ERROR"
  | "UNVERIFIED_INPUT";

export interface SealFailure {
  readonly code: SealFailureCode;
  readonly detail: string;
}

/**
 * Qué respalda cada dato mostrado. Los valores son también la etiqueta visible:
 *  - COINCIDE: el cliente lo recalculó o lo comprobó contra el ancla de confianza y coincide.
 *  - DECLARADO: lo declara el emisor y lo cubre la firma comprobada; el cliente no puede
 *    comprobarlo por sí mismo.
 *  - NO_VERIFICADO: no se comprobó (falta el dato necesario) y la interfaz debe decirlo.
 */
export type AssuranceLevel = "COINCIDE" | "DECLARADO" | "NO_VERIFICADO";

export interface AssuranceReport {
  readonly structure: "COINCIDE";
  readonly dag_acyclic: "COINCIDE";
  readonly leaf_hashes: "COINCIDE";
  readonly merkle_root: "COINCIDE";
  readonly manifest_binding: "COINCIDE";
  readonly authority_signature: "COINCIDE";
  readonly larsa_commit: "DECLARADO";
  readonly lean4_proof: "DECLARADO";
  readonly worm_audit: "DECLARADO";
  readonly chain_link: "COINCIDE" | "NO_VERIFICADO";
}

export interface LaidOutNode {
  readonly node: ExecutionDagNode;
  /** Profundidad causal: camino más largo desde una raíz. */
  readonly depth: number;
}

declare const acceptedReceiptBrand: unique symbol;

/**
 * Recibo que superó todas las comprobaciones locales. Inmutable (congelado en profundidad) y
 * registrado por el verificador; `isAcceptedReceipt` distingue en ejecución un valor legítimo de un
 * objeto con la misma forma construido a mano. «Aceptado» describe el resultado de esas
 * comprobaciones, no la veracidad de lo que el emisor declara.
 */
export interface AcceptedReceipt {
  readonly [acceptedReceiptBrand]: true;
  readonly payload: Babylon60ExecutionPayload;
  /** Nodos en orden topológico determinista, con su profundidad. */
  readonly nodes: readonly LaidOutNode[];
  /** `0x` + BLAKE3 del sobre canónico: el valor que el recibo siguiente debe citar como previo. */
  readonly receipt_hash: Hex32;
  /** Autoridad admitida cuya firma se verificó. */
  readonly signer: Hex32;
  /** Peso LARSA exigido por el ancla de confianza con el que se comparó el declarado. */
  readonly larsa_required_weight: number;
  readonly assurances: AssuranceReport;
}

/** Valores recalculados y declarados, para cotejo forense cuando la verificación falla. */
export interface FailureDiagnostics {
  readonly declared_merkle_root: string | null;
  readonly computed_merkle_root: string | null;
  readonly declared_manifest_hash: string | null;
  readonly computed_manifest_hash: string | null;
  readonly node_count: number | null;
}

export type VerificationVerdict =
  | {
      readonly ok: true;
      readonly receipt: AcceptedReceipt;
      readonly failures: readonly [];
    }
  | {
      readonly ok: false;
      readonly receipt: null;
      readonly failures: readonly SealFailure[];
      readonly diagnostics: FailureDiagnostics;
    };
