/**
 * Verificador fail-closed del recibo de ejecución.
 *
 * Contrato:
 *  - la entrada es `unknown` (lo que devuelve `JSON.parse` sobre bytes de un transporte no fiable);
 *  - el ancla de confianza (autoridades admitidas, peso LARSA exigido) la aporta el anfitrión y es
 *    obligatoria: no existe modo de obtener `ok: true` sin verificar la firma contra una clave que
 *    el payload no puede elegir;
 *  - la promesa nunca se rechaza: cualquier excepción interna se convierte en un veredicto negativo;
 *  - `ok: true` implica que todas las comprobaciones se ejecutaron y pasaron, y entrega un
 *    `AcceptedReceipt` congelado y registrado, único tipo que la interfaz acepta para dibujar.
 *
 * Qué establece un veredicto positivo, y qué no, está en `AssuranceReport` y en el README: una firma
 * válida no dice quién controla la clave, ni que el efecto descrito ocurriera, ni que la entrada
 * fuera veraz.
 */

import { fromHexStrict, toHex } from "./bytes.ts";
import {
  dagMerkleRoot,
  envelopeFieldsOf,
  manifestHashHex,
  nodeLeafHash,
  receiptEnvelope,
  receiptHashHex,
  signatureInput,
} from "./canonical.ts";
import { ambientSubtle, createEd25519Verifier, type Ed25519Verifier, type SubtleVerifyLike } from "./ed25519.ts";
import { classifyPoint } from "./ed25519Point.ts";
import { JSON_FORM_DETAIL, jsonTextIssue } from "./jsonText.ts";
import { FailureCollector, LIMITS, parseExecutionPayload, preview, sanitizeDetail } from "./schema.ts";
import { topologicalOrder } from "../dag/topology.ts";
import type {
  AssuranceReport,
  Babylon60ExecutionPayload,
  ExecutionDagNode,
  FailureDiagnostics,
  Hex32,
  LaidOutNode,
  TrustPolicy,
  VerificationVerdict,
  AcceptedReceipt,
} from "../types/babylon60.ts";

export { LIMITS } from "./schema.ts";

/** Máximo de autoridades admitidas en un ancla de confianza. */
export const MAX_ADMITTED_AUTHORITIES = 64;
const U32_MAX = 0xffff_ffff;
const HEX32_RE = /^0x[0-9a-f]{64}$/;

const acceptedRegistry = new WeakSet<object>();

/** `true` solo para objetos que este módulo emitió tras una verificación completa. */
export function isAcceptedReceipt(value: unknown): value is AcceptedReceipt {
  return typeof value === "object" && value !== null && acceptedRegistry.has(value);
}

interface NormalizedPolicy {
  /** Clave hex → bytes de la clave. */
  readonly authorities: ReadonlyMap<string, Uint8Array>;
  readonly larsaRequiredWeight: number;
  readonly previous: { readonly receipt_hash: string; readonly seq_id: number } | null;
}

type Rec = Record<string, unknown>;

function isRecord(v: unknown): v is Rec {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function hasOnlyKeys(obj: Rec, allowed: readonly string[]): boolean {
  return Object.keys(obj).every((k) => allowed.includes(k));
}

/** Valida y copia el ancla de confianza. Un ancla defectuosa rechaza todo recibo. */
function normalizePolicy(policy: unknown, c: FailureCollector): NormalizedPolicy | null {
  const bad = (detail: string): null => {
    c.fail("TRUST_POLICY_INVALID", detail);
    return null;
  };
  if (!isRecord(policy) || !hasOnlyKeys(policy, ["admitted_authorities", "larsa_required_weight", "previous_receipt"])) {
    return bad("el ancla de confianza debe ser { admitted_authorities, larsa_required_weight, previous_receipt? }");
  }
  const rawAuthorities = policy["admitted_authorities"];
  if (!Array.isArray(rawAuthorities) || rawAuthorities.length === 0 || rawAuthorities.length > MAX_ADMITTED_AUTHORITIES) {
    return bad(`admitted_authorities debe ser un array de 1 a ${MAX_ADMITTED_AUTHORITIES} claves`);
  }
  const authorities = new Map<string, Uint8Array>();
  for (let i = 0; i < rawAuthorities.length; i++) {
    const key: unknown = rawAuthorities[i];
    if (typeof key !== "string" || !HEX32_RE.test(key)) {
      return bad(`admitted_authorities[${i}] debe ser 0x + 64 dígitos hex en minúsculas`);
    }
    if (authorities.has(key)) return bad(`admitted_authorities[${i}] repite una clave`);
    const keyBytes = fromHexStrict(key.slice(2), 32);
    if (keyBytes === null) return bad(`admitted_authorities[${i}] no es hex válido`);
    const pointVerdict = classifyPoint(keyBytes);
    if (pointVerdict !== "OK") {
      return bad(`admitted_authorities[${i}] no es una clave Ed25519 aceptable (${pointVerdict})`);
    }
    authorities.set(key, keyBytes);
  }

  // Igual que en el kernel: un umbral cero nunca puede confirmar (ZeroHeuristicThreshold).
  const required = policy["larsa_required_weight"];
  if (typeof required !== "number" || !Number.isSafeInteger(required) || required < 1 || required > U32_MAX) {
    return bad("larsa_required_weight debe ser un entero en [1, 2^32-1]");
  }

  let previous: NormalizedPolicy["previous"] = null;
  const rawPrev = policy["previous_receipt"];
  if (rawPrev !== undefined) {
    if (!isRecord(rawPrev) || !hasOnlyKeys(rawPrev, ["receipt_hash", "seq_id"])) {
      return bad("previous_receipt debe ser { receipt_hash, seq_id }");
    }
    const receipt_hash = rawPrev["receipt_hash"];
    const seq_id = rawPrev["seq_id"];
    if (typeof receipt_hash !== "string" || !HEX32_RE.test(receipt_hash)) {
      return bad("previous_receipt.receipt_hash debe ser 0x + 64 dígitos hex en minúsculas");
    }
    if (typeof seq_id !== "number" || !Number.isSafeInteger(seq_id) || seq_id < 0) {
      return bad("previous_receipt.seq_id debe ser un entero ≥ 0");
    }
    previous = { receipt_hash, seq_id };
  }
  return { authorities, larsaRequiredWeight: required, previous };
}

interface MutableDiagnostics {
  declared_merkle_root: string | null;
  computed_merkle_root: string | null;
  declared_manifest_hash: string | null;
  computed_manifest_hash: string | null;
  node_count: number | null;
}

function emptyDiagnostics(): MutableDiagnostics {
  return {
    declared_merkle_root: null,
    computed_merkle_root: null,
    declared_manifest_hash: null,
    computed_manifest_hash: null,
    node_count: null,
  };
}

function reject(c: FailureCollector, d: MutableDiagnostics): VerificationVerdict {
  if (c.count === 0) {
    c.fail("VERIFIER_INTERNAL_ERROR", "rechazo sin causa registrada");
  }
  const diagnostics: FailureDiagnostics = Object.freeze({ ...d });
  return Object.freeze({ ok: false, receipt: null, failures: c.finish(), diagnostics });
}

/** Compuertas sobre la forma del DAG. Devuelve el orden topológico si el grafo es válido. */
function checkDag(dag: readonly ExecutionDagNode[], c: FailureCollector): readonly LaidOutNode[] | null {
  const byId = new Map<string, ExecutionDagNode>();
  let sound = true;
  for (const node of dag) {
    if (byId.has(node.node_id)) {
      c.fail("DAG_DUPLICATE_NODE_ID", `identificador de nodo duplicado: ${node.node_id}`);
      sound = false;
    } else {
      byId.set(node.node_id, node);
    }
  }
  for (const node of dag) {
    const seen = new Set<string>();
    for (const parentId of node.parent_ids) {
      if (seen.has(parentId)) {
        c.fail("DAG_DUPLICATE_PARENT_REF", `el nodo ${node.node_id} repite el padre ${parentId}`);
        sound = false;
      }
      seen.add(parentId);
      if (!byId.has(parentId)) {
        c.fail("DAG_DANGLING_PARENT_REF", `el nodo ${node.node_id} referencia un padre inexistente: ${parentId}`);
        sound = false;
      }
    }
  }
  if (!sound) return null;

  const topo = topologicalOrder(dag);
  if (topo.precondition_violated) {
    c.fail("VERIFIER_INTERNAL_ERROR", "el orden topológico recibió un grafo incoherente");
    return null;
  }
  if (!topo.acyclic) {
    const shown = topo.unresolved.slice(0, 8).join(", ");
    const more = topo.unresolved.length > 8 ? ` (+${topo.unresolved.length - 8})` : "";
    c.fail(
      "DAG_CYCLE_DETECTED",
      `ciclo causal: ${topo.order.length}/${dag.length} nodos ordenables; sin ordenar: ${shown}${more}`
    );
    return null;
  }
  return Object.freeze(topo.order.map((id, i) => Object.freeze({ node: byId.get(id)!, depth: topo.depths[i]! })));
}

const ASSURANCES_BASE = {
  structure: "COINCIDE",
  dag_acyclic: "COINCIDE",
  leaf_hashes: "COINCIDE",
  merkle_root: "COINCIDE",
  manifest_binding: "COINCIDE",
  authority_signature: "COINCIDE",
  larsa_commit: "DECLARADO",
  lean4_proof: "DECLARADO",
  worm_audit: "DECLARADO",
} as const;

export interface VerifierEnvironment {
  /** WebCrypto a usar. Por defecto, el del entorno en el momento de cada verificación. */
  readonly subtle?: SubtleVerifyLike | undefined;
}

export type ReceiptVerifier = (input: unknown, policy: TrustPolicy) => Promise<VerificationVerdict>;

/** Crea un verificador. `env` existe para probar runtimes sin Ed25519; no relaja ninguna compuerta. */
export function createReceiptVerifier(env?: VerifierEnvironment): ReceiptVerifier {
  const injected = env !== undefined && Object.prototype.hasOwnProperty.call(env, "subtle");
  let cached: { subtle: SubtleVerifyLike | undefined; verifier: Ed25519Verifier } | null = null;

  const ed25519 = (): Ed25519Verifier => {
    const subtle = injected ? env!.subtle : ambientSubtle();
    if (cached === null || cached.subtle !== subtle) {
      cached = { subtle, verifier: createEd25519Verifier(subtle) };
    }
    return cached.verifier;
  };

  return async function verifyExecutionPayload(input: unknown, policy: TrustPolicy): Promise<VerificationVerdict> {
    const c = new FailureCollector();
    const d = emptyDiagnostics();

    try {
      const trust = normalizePolicy(policy, c);
      if (trust === null) return reject(c, d);

      const payload: Babylon60ExecutionPayload | null = parseExecutionPayload(input, c);
      if (payload === null) return reject(c, d);

      const dag = payload.execution_dag;
      const seal = payload.cryptographic_seal;
      d.node_count = dag.length;
      d.declared_merkle_root = seal.phase_two_merkle_root;
      d.declared_manifest_hash = seal.phase_one_manifest_hash;

      // 1. Forma del DAG.
      const order = checkDag(dag, c);

      // 2. Coherencia nodo-SMT.
      for (const node of dag) {
        if (node.state_status === "COMMITTED" && !node.smt_verified) {
          c.fail("COMMITTED_WITHOUT_SMT", `nodo ${node.node_id} marcado COMMITTED con smt_verified=false`);
        }
      }

      // 3. Hojas y raíz Merkle v1, recalculadas desde el contenido de cada nodo.
      const leafHashes = dag.map((node) => nodeLeafHash(node));
      for (let i = 0; i < dag.length; i++) {
        const expected = "0x" + toHex(leafHashes[i]!);
        if (expected !== dag[i]!.state_hash) {
          c.fail(
            "LEAF_HASH_MISMATCH",
            `nodo ${dag[i]!.node_id}: state_hash recalculado ${expected}, recibido ${dag[i]!.state_hash}`
          );
        }
      }
      if (!c.has("DAG_DUPLICATE_NODE_ID")) {
        const computedRoot = dagMerkleRoot(
          dag.map((n) => n.node_id),
          leafHashes
        );
        d.computed_merkle_root = computedRoot;
        if (computedRoot !== seal.phase_two_merkle_root) {
          c.fail("MERKLE_ROOT_MISMATCH", `raíz recalculada ${computedRoot}, declarada ${seal.phase_two_merkle_root}`);
        }
      }

      // 4. Fase 1: el manifiesto de entrada debe coincidir con su compromiso.
      const computedManifest = manifestHashHex(payload);
      d.computed_manifest_hash = computedManifest;
      if (computedManifest !== seal.phase_one_manifest_hash) {
        c.fail(
          "MANIFEST_HASH_MISMATCH",
          `hash de manifiesto recalculado ${computedManifest}, declarado ${seal.phase_one_manifest_hash}`
        );
      }

      // 5. Declaraciones del emisor. El peso exigido lo fija el ancla, no el recibo.
      if (seal.larsa_commit.heuristic_weight < trust.larsaRequiredWeight) {
        c.fail(
          "QUORUM_INSUFFICIENT",
          `peso heurístico LARSA declarado ${seal.larsa_commit.heuristic_weight} < peso exigido por el ancla ${trust.larsaRequiredWeight}`
        );
      }
      if (seal.lean4_proof.status !== "VERIFIED_NO_SORRY" || seal.lean4_proof.sorry_count !== 0) {
        c.fail(
          "LEAN4_PROOF_INVALID",
          `constancia Lean 4 declarada ${seal.lean4_proof.status} con sorry_count=${seal.lean4_proof.sorry_count}`
        );
      }

      // 6. Firma del sobre por una autoridad admitida.
      const envelope = receiptEnvelope(envelopeFieldsOf(payload));
      const signerKey = trust.authorities.get(seal.ed25519_public_key);
      if (signerKey === undefined) {
        c.fail(
          "AUTHORITY_NOT_ADMITTED",
          `la clave firmante ${seal.ed25519_public_key} no figura entre las ${trust.authorities.size} autoridades admitidas`
        );
      } else {
        const signature = fromHexStrict(seal.ed25519_signature.slice(2), 64);
        const outcome =
          signature === null ? "INVALID" : await ed25519().verify(signerKey, signature, signatureInput(envelope));
        if (outcome === "UNSUPPORTED_RUNTIME") {
          c.fail("ED25519_UNSUPPORTED_RUNTIME", "el runtime no ofrece Ed25519 nativo fiable; la firma no puede verificarse");
        } else if (outcome === "BAD_PUBLIC_KEY") {
          c.fail("TRUST_POLICY_INVALID", `la autoridad admitida ${seal.ed25519_public_key} no es una clave Ed25519 importable`);
        } else if (outcome !== "VALID") {
          c.fail("ED25519_SIGNATURE_INVALID", `firma inválida de la autoridad ${seal.ed25519_public_key} sobre el sobre canónico`);
        }
      }

      // 7. Encadenamiento con el recibo anterior, si el anfitrión aporta un punto de control.
      if (trust.previous !== null) {
        if (payload.audit_metrics.prev_receipt_hash !== trust.previous.receipt_hash) {
          c.fail(
            "CHAIN_LINK_MISMATCH",
            `prev_receipt_hash ${payload.audit_metrics.prev_receipt_hash} no coincide con el punto de control ${trust.previous.receipt_hash}`
          );
        }
        if (payload.causal_clock.seq_id <= trust.previous.seq_id) {
          c.fail(
            "CHAIN_LINK_MISMATCH",
            `seq_id ${payload.causal_clock.seq_id} no es posterior al del punto de control (${trust.previous.seq_id})`
          );
        }
      }

      if (c.count > 0 || order === null) return reject(c, d);

      const assurances: AssuranceReport = Object.freeze({
        ...ASSURANCES_BASE,
        chain_link: trust.previous !== null ? "COINCIDE" : "NO_VERIFICADO",
      });
      const receipt = Object.freeze({
        payload,
        nodes: order,
        receipt_hash: receiptHashHex(envelope) as Hex32,
        signer: seal.ed25519_public_key,
        larsa_required_weight: trust.larsaRequiredWeight,
        assurances,
      }) as AcceptedReceipt;
      acceptedRegistry.add(receipt);
      return Object.freeze({ ok: true, receipt, failures: Object.freeze([]) as readonly [] });
    } catch (error) {
      const name = error instanceof Error ? error.name : typeof error;
      const message = error instanceof Error ? error.message : "";
      c.fail("VERIFIER_INTERNAL_ERROR", `excepción interna ${preview(name)}: ${preview(message)}`);
      return reject(c, d);
    }
  };
}

/** Códigos con los que un anfitrión puede expresar que no llegó a haber recibo que verificar. */
export type HostRejectionCode = "SCHEMA_INVALID" | "ED25519_UNSUPPORTED_RUNTIME" | "VERIFIER_INTERNAL_ERROR" | "UNVERIFIED_INPUT";

/**
 * Veredicto negativo para fallos previos a la verificación (transporte caído, JSON ilegible,
 * excepción del anfitrión). Permite que la interfaz trate todo fallo por el mismo camino cerrado.
 */
export function rejectionVerdict(code: HostRejectionCode, detail: string): VerificationVerdict {
  const c = new FailureCollector();
  c.fail(code, sanitizeDetail(detail));
  return reject(c, emptyDiagnostics());
}

/** Tamaño máximo del texto JSON que `verifyExecutionPayloadJson` acepta interpretar. */
export const MAX_JSON_TEXT_LENGTH = 4 * 1024 * 1024;

/** Verificador por defecto, ligado al WebCrypto del entorno. */
export const verifyExecutionPayload: ReceiptVerifier = createReceiptVerifier();

/**
 * Verifica un recibo recibido como texto JSON. Un texto demasiado largo o ilegible produce un
 * veredicto negativo, nunca una excepción.
 */
export async function verifyExecutionPayloadJson(
  text: string,
  policy: TrustPolicy,
  verify: ReceiptVerifier = verifyExecutionPayload
): Promise<VerificationVerdict> {
  if (typeof text !== "string") return rejectionVerdict("SCHEMA_INVALID", "el transporte no entregó texto");
  if (text.length > MAX_JSON_TEXT_LENGTH) {
    return rejectionVerdict("SCHEMA_INVALID", `texto JSON de ${text.length} caracteres supera el máximo ${MAX_JSON_TEXT_LENGTH}`);
  }
  let value: unknown;
  try {
    value = JSON.parse(text) as unknown;
  } catch {
    return rejectionVerdict("SCHEMA_INVALID", JSON_FORM_DETAIL);
  }
  // Mismos textos que acepta `serde_json` en el crate de referencia (ver jsonText.ts).
  const issue = jsonTextIssue(text);
  if (issue !== null) return rejectionVerdict("SCHEMA_INVALID", issue);
  return verify(value, policy);
}

/**
 * Verifica un recibo tal como llegó del transporte: bytes que deben ser UTF-8 válido. No retira
 * una marca BOM inicial (`JSON.parse` la rechaza, igual que `serde_json`).
 */
export async function verifyExecutionPayloadUtf8(
  bytes: Uint8Array,
  policy: TrustPolicy,
  verify: ReceiptVerifier = verifyExecutionPayload
): Promise<VerificationVerdict> {
  if (!(bytes instanceof Uint8Array)) return rejectionVerdict("SCHEMA_INVALID", "el transporte no entregó bytes");
  if (bytes.length > 3 * MAX_JSON_TEXT_LENGTH) {
    return rejectionVerdict("SCHEMA_INVALID", `${bytes.length} bytes superan el máximo admitido`);
  }
  let text: string;
  try {
    text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
  } catch {
    return rejectionVerdict("SCHEMA_INVALID", "el recibo no es UTF-8 válido");
  }
  return verifyExecutionPayloadJson(text, policy, verify);
}

/** Tope de fallos que lista un veredicto negativo. */
export const MAX_REPORTED_FAILURES = LIMITS.MAX_REPORTED_FAILURES;
