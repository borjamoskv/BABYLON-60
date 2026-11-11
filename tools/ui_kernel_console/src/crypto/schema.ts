/**
 * Validación estructural estricta de la entrada no confiable.
 *
 * Reglas:
 *  - cada objeto debe tener exactamente las claves esperadas (una clave desconocida es un dato sin
 *    firma ni recomputación, así que se rechaza);
 *  - cada propiedad se lee una sola vez y se copia a una estructura nueva, de modo que el resto de
 *    la verificación nunca vuelve a tocar el valor recibido;
 *  - todo límite de tamaño se comprueba antes de recorrer el contenido;
 *  - los fragmentos de entrada que se citan en un fallo pasan por `preview`, que acota y escapa.
 */

import { fromHexStrict, isWellFormedString } from "./bytes.ts";
import type {
  B3Root,
  Babylon60ExecutionPayload,
  ExecutionDagNode,
  Hex32,
  Hex64,
  Lean4ProofStatus,
  NodeStateStatus,
  PolicyProfile,
  SealFailure,
  SealFailureCode,
} from "../types/babylon60.ts";

/** Cotas del trabajo que el cliente acepta hacer por recibo. */
export const LIMITS = Object.freeze({
  MAX_DAG_NODES: 4096,
  MAX_PARENTS_PER_NODE: 64,
  MAX_DAG_EDGES: 16384,
  MAX_EXECUTION_ID_LENGTH: 128,
  MAX_AGENT_ID_LENGTH: 256,
  MAX_PAYLOAD_RAW_LENGTH: 65536,
  MAX_VIOLATION_REASON_LENGTH: 512,
  MAX_THEOREM_IDENT_LENGTH: 256,
  MAX_REPORTED_FAILURES: 64,
});

const POLICY_PROFILES: readonly PolicyProfile[] = ["STRICT_DETERMINISTIC", "BFT_DEFENSIVE", "NEMESIS_ADVERSARIAL"];
const NODE_STATUSES: readonly NodeStateStatus[] = ["COMMITTED", "REJECTED_POLICY", "INTERCEPTED_NEMESIS", "PENDING_SEAL"];
const LEAN_STATUSES: readonly Lean4ProofStatus[] = ["VERIFIED_NO_SORRY", "FAILED_INVARIANT"];

const EXECUTION_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._:-]*$/;
const MANIFEST_VERSION_RE = /^v(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})$/;
const AGENT_ID_RE = /^[\x21-\x7e]+$/;
const THEOREM_IDENT_RE = /^[A-Za-z_][A-Za-z0-9_'!?]*(\.[A-Za-z_][A-Za-z0-9_'!?]*)*$/;
const EVENT_ID_RE = /^EV_([0-9]{8,20})_([0-9]{6,10})$/;

const U64_MAX_DECIMAL = "18446744073709551615";
const U32_MAX_DECIMAL = "4294967295";

/** Decimal sin ceros sobrantes respecto al ancho mínimo y no mayor que `max` (misma longitud máxima). */
function isCanonicalPaddedDecimal(digits: string, minWidth: number, max: string): boolean {
  if (digits.length > minWidth && digits.charCodeAt(0) === 0x30) return false;
  if (digits.length > max.length) return false;
  if (digits.length === max.length && digits > max) return false;
  return true;
}

/**
 * `EV_{tick:08}_{seq:06}` tal como lo emite `generate_canonical_event_id(tick: u64, seq: u32)`:
 * relleno mínimo de 8 y 6 dígitos, sin ceros adicionales, dentro de u64 y u32.
 */
export function isCanonicalEventId(id: string): boolean {
  const m = EVENT_ID_RE.exec(id);
  if (m === null) return false;
  return isCanonicalPaddedDecimal(m[1]!, 8, U64_MAX_DECIMAL) && isCanonicalPaddedDecimal(m[2]!, 6, U32_MAX_DECIMAL);
}

/** Cita acotada y escapada de un valor no confiable para mensajes de fallo. */
export function preview(value: unknown): string {
  let text: string;
  if (typeof value === "string") text = value;
  else if (value === null) return "null";
  else if (Array.isArray(value)) return "array";
  else if (typeof value === "object") return "object";
  else if (typeof value === "number" || typeof value === "boolean") text = String(value);
  else return typeof value;

  let out = "";
  const max = 48;
  let i = 0;
  for (; i < text.length && out.length < max; i++) {
    const c = text.charCodeAt(i);
    if (c >= 0x20 && c <= 0x7e && c !== 0x5c && c !== 0x22) out += text[i]!;
    else out += "\\u" + c.toString(16).padStart(4, "0");
  }
  const suffix = i < text.length ? `…(+${text.length - i})` : "";
  return typeof value === "string" ? `"${out}${suffix}"` : out + suffix;
}

/** Texto de detalle aportado por el anfitrión: acotado y con todo carácter no imprimible escapado. */
export function sanitizeDetail(text: unknown, max = 240): string {
  const source = typeof text === "string" ? text : typeof text;
  let out = "";
  let i = 0;
  for (; i < source.length && out.length < max; i++) {
    const c = source.charCodeAt(i);
    out += c >= 0x20 && c <= 0x7e ? source[i]! : c >= 0xa0 && c <= 0x24f ? source[i]! : "\\u" + c.toString(16).padStart(4, "0");
  }
  return i < source.length ? `${out}…(+${source.length - i})` : out;
}

/** Acumulador de fallos con tope explícito: nunca crece sin límite ante una entrada hostil. */
export class FailureCollector {
  private readonly items: SealFailure[] = [];
  private truncated = false;

  fail(code: SealFailureCode, detail: string): void {
    if (this.items.length < LIMITS.MAX_REPORTED_FAILURES) {
      this.items.push(Object.freeze({ code, detail }));
    } else {
      this.truncated = true;
    }
  }

  /** Número de fallos retenidos (como máximo, el tope). */
  get count(): number {
    return this.items.length;
  }

  /** `true` si ya no cabe ningún fallo más; quien recorre la entrada debe detenerse y declararlo. */
  get full(): boolean {
    return this.items.length >= LIMITS.MAX_REPORTED_FAILURES;
  }

  /** Declara que se dejó de examinar la entrada, de modo que la lista no se lea como exhaustiva. */
  markTruncated(): void {
    this.truncated = true;
  }

  has(code: SealFailureCode): boolean {
    return this.items.some((f) => f.code === code);
  }

  /** Lista congelada; si hubo recorte, la última entrada lo dice. */
  finish(): readonly SealFailure[] {
    const out = [...this.items];
    if (this.truncated && out.length > 0) {
      const last = out[out.length - 1]!;
      out[out.length - 1] = Object.freeze({
        code: last.code,
        detail: `${last.detail} [lista truncada en el tope de ${LIMITS.MAX_REPORTED_FAILURES} fallos; puede haber más]`,
      });
    }
    return Object.freeze(out);
  }
}

type Rec = Record<string, unknown>;

function own(obj: Rec, key: string): unknown {
  return Object.prototype.hasOwnProperty.call(obj, key) ? obj[key] : undefined;
}

/** Devuelve el objeto si es un registro con exactamente `keys`; si no, registra el fallo y devuelve null. */
function exactObject(value: unknown, keys: readonly string[], path: string, c: FailureCollector): Rec | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    c.fail("SCHEMA_INVALID", `${path}: se esperaba un objeto, se recibió ${preview(value)}`);
    return null;
  }
  const obj = value as Rec;
  let ok = true;
  let present: string[];
  try {
    present = Object.keys(obj);
  } catch {
    c.fail("SCHEMA_INVALID", `${path}: objeto no enumerable`);
    return null;
  }
  if (present.length > keys.length + 16) {
    c.fail("SCHEMA_INVALID", `${path}: ${present.length} claves, se esperaban ${keys.length}`);
    return null;
  }
  for (const k of present) {
    if (!keys.includes(k)) {
      c.fail("SCHEMA_INVALID", `${path}: clave no admitida ${preview(k)}`);
      ok = false;
    }
  }
  for (const k of keys) {
    if (!Object.prototype.hasOwnProperty.call(obj, k)) {
      c.fail("SCHEMA_INVALID", `${path}.${k}: falta el campo obligatorio`);
      ok = false;
    }
  }
  return ok ? obj : null;
}

function readString(
  value: unknown,
  path: string,
  maxLength: number,
  c: FailureCollector,
  pattern?: RegExp
): string | null {
  if (typeof value !== "string") {
    c.fail("SCHEMA_INVALID", `${path}: se esperaba una cadena, se recibió ${preview(value)}`);
    return null;
  }
  if (value.length > maxLength) {
    c.fail("LIMIT_EXCEEDED", `${path}: longitud ${value.length} supera el máximo ${maxLength}`);
    return null;
  }
  if (!isWellFormedString(value)) {
    c.fail("SCHEMA_INVALID", `${path}: la cadena contiene sustitutos UTF-16 sueltos`);
    return null;
  }
  if (pattern !== undefined && !pattern.test(value)) {
    c.fail("SCHEMA_INVALID", `${path}: formato no admitido ${preview(value)}`);
    return null;
  }
  return value;
}

function readUint(value: unknown, path: string, c: FailureCollector): number | null {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) {
    c.fail("SCHEMA_INVALID", `${path}: se esperaba un entero en [0, 2^53-1], se recibió ${preview(value)}`);
    return null;
  }
  return value === 0 ? 0 : value; // normaliza -0
}

/** Entero sin signo de 32 bits (los pesos LARSA son u32 en el kernel). */
export function readU32(value: unknown, path: string, c: FailureCollector): number | null {
  const n = readUint(value, path, c);
  if (n !== null && n > 0xffff_ffff) {
    c.fail("SCHEMA_INVALID", `${path}: ${n} excede 2^32-1`);
    return null;
  }
  return n;
}

function readEnum<T extends string>(value: unknown, allowed: readonly T[], path: string, c: FailureCollector): T | null {
  if (typeof value === "string" && (allowed as readonly string[]).includes(value)) return value as T;
  c.fail("SCHEMA_INVALID", `${path}: valor no admitido ${preview(value)}`);
  return null;
}

function readBoolean(value: unknown, path: string, c: FailureCollector): boolean | null {
  if (typeof value === "boolean") return value;
  c.fail("SCHEMA_INVALID", `${path}: se esperaba un booleano, se recibió ${preview(value)}`);
  return null;
}

function readPrefixedHex(value: unknown, prefix: string, bytes: number, path: string, c: FailureCollector): string | null {
  if (typeof value !== "string") {
    c.fail("SCHEMA_MALFORMED_HEX", `${path}: se esperaba una cadena hex, se recibió ${preview(value)}`);
    return null;
  }
  if (
    value.length !== prefix.length + bytes * 2 ||
    !value.startsWith(prefix) ||
    fromHexStrict(value.slice(prefix.length), bytes) === null
  ) {
    c.fail(
      "SCHEMA_MALFORMED_HEX",
      `${path}: se esperaba "${prefix}" seguido de ${bytes * 2} dígitos hex en minúsculas, se recibió ${preview(value)}`
    );
    return null;
  }
  return value;
}

export function readHex32(value: unknown, path: string, c: FailureCollector): Hex32 | null {
  return readPrefixedHex(value, "0x", 32, path, c) as Hex32 | null;
}

function readHex64(value: unknown, path: string, c: FailureCollector): Hex64 | null {
  return readPrefixedHex(value, "0x", 64, path, c) as Hex64 | null;
}

function readB3Root(value: unknown, path: string, c: FailureCollector): B3Root | null {
  return readPrefixedHex(value, "b3:", 32, path, c) as B3Root | null;
}

/** Devuelve el array si lo es y no supera `max` elementos. El contenido aún no se ha recorrido. */
function readArray(value: unknown, path: string, max: number, c: FailureCollector): readonly unknown[] | null {
  if (!Array.isArray(value)) {
    c.fail("SCHEMA_INVALID", `${path}: se esperaba un array, se recibió ${preview(value)}`);
    return null;
  }
  if (value.length > max) {
    c.fail("LIMIT_EXCEEDED", `${path}: ${value.length} elementos superan el máximo ${max}`);
    return null;
  }
  return value;
}

const NODE_KEYS = ["node_id", "parent_ids", "state_status", "smt_verified", "reduction_steps", "state_hash", "violation_reason"];

function readNode(value: unknown, path: string, c: FailureCollector): ExecutionDagNode | null {
  const obj = exactObject(value, NODE_KEYS, path, c);
  if (obj === null) return null;

  const rawId = readString(own(obj, "node_id"), `${path}.node_id`, 40, c);
  let node_id: string | null = null;
  if (rawId !== null) {
    if (isCanonicalEventId(rawId)) node_id = rawId;
    else c.fail("SCHEMA_INVALID", `${path}.node_id: no es un identificador canónico EV_{tick:08}_{seq:06}: ${preview(rawId)}`);
  }

  let parent_ids: string[] | null = null;
  const rawParents = readArray(own(obj, "parent_ids"), `${path}.parent_ids`, LIMITS.MAX_PARENTS_PER_NODE, c);
  if (rawParents !== null) {
    parent_ids = [];
    for (let i = 0; i < rawParents.length; i++) {
      const p = readString(rawParents[i], `${path}.parent_ids[${i}]`, 40, c);
      if (p === null) {
        parent_ids = null;
        break;
      }
      if (!isCanonicalEventId(p)) {
        c.fail("SCHEMA_INVALID", `${path}.parent_ids[${i}]: no es un identificador canónico: ${preview(p)}`);
        parent_ids = null;
        break;
      }
      parent_ids.push(p);
    }
  }

  const state_status = readEnum(own(obj, "state_status"), NODE_STATUSES, `${path}.state_status`, c);
  const smt_verified = readBoolean(own(obj, "smt_verified"), `${path}.smt_verified`, c);
  const reduction_steps = readUint(own(obj, "reduction_steps"), `${path}.reduction_steps`, c);
  const state_hash = readHex32(own(obj, "state_hash"), `${path}.state_hash`, c);

  const rawReason = own(obj, "violation_reason");
  let violation_reason: string | null | undefined;
  if (rawReason === null) violation_reason = null;
  else {
    const r = readString(rawReason, `${path}.violation_reason`, LIMITS.MAX_VIOLATION_REASON_LENGTH, c);
    violation_reason = r === null ? undefined : r;
    if (r !== null && r.length === 0) {
      c.fail("SCHEMA_INVALID", `${path}.violation_reason: cadena vacía; use null si no hay violación`);
      violation_reason = undefined;
    }
  }

  if (
    node_id === null ||
    parent_ids === null ||
    state_status === null ||
    smt_verified === null ||
    reduction_steps === null ||
    state_hash === null ||
    violation_reason === undefined
  ) {
    return null;
  }
  return Object.freeze({
    node_id,
    parent_ids: Object.freeze(parent_ids),
    state_status,
    smt_verified,
    reduction_steps,
    state_hash,
    violation_reason,
  });
}

const ROOT_KEYS = ["execution_id", "causal_clock", "manifest_version", "ingress", "execution_dag", "cryptographic_seal", "audit_metrics"];
const CLOCK_KEYS = ["policy_epoch", "logical_tick", "seq_id"];
const INGRESS_KEYS = ["agent_id", "policy_profile", "payload_raw"];
const SEAL_KEYS = [
  "phase_one_manifest_hash",
  "phase_two_merkle_root",
  "ed25519_public_key",
  "ed25519_signature",
  "larsa_commit",
  "lean4_proof",
];
const LARSA_KEYS = ["trace_hash", "heuristic_weight"];
const LEAN_KEYS = ["status", "theorem_ident", "sorry_count"];
const AUDIT_KEYS = ["memory_bytes", "prev_receipt_hash", "worm_txid"];

/**
 * Interpreta `input` como recibo. Devuelve una copia congelada con tipos validados, o `null` tras
 * registrar en `c` cada motivo de rechazo. No comprueba todavía hashes, firmas ni la forma del DAG.
 */
export function parseExecutionPayload(input: unknown, c: FailureCollector): Babylon60ExecutionPayload | null {
  const root = exactObject(input, ROOT_KEYS, "$", c);
  if (root === null) return null;

  const execution_id = readString(own(root, "execution_id"), "$.execution_id", LIMITS.MAX_EXECUTION_ID_LENGTH, c, EXECUTION_ID_RE);
  const manifest_version = readString(own(root, "manifest_version"), "$.manifest_version", 32, c, MANIFEST_VERSION_RE);

  let causal_clock: Babylon60ExecutionPayload["causal_clock"] | null = null;
  const clock = exactObject(own(root, "causal_clock"), CLOCK_KEYS, "$.causal_clock", c);
  if (clock !== null) {
    const policy_epoch = readUint(own(clock, "policy_epoch"), "$.causal_clock.policy_epoch", c);
    const logical_tick = readUint(own(clock, "logical_tick"), "$.causal_clock.logical_tick", c);
    const seq_id = readUint(own(clock, "seq_id"), "$.causal_clock.seq_id", c);
    if (policy_epoch !== null && logical_tick !== null && seq_id !== null) {
      causal_clock = Object.freeze({ policy_epoch, logical_tick, seq_id });
    }
  }

  let ingress: Babylon60ExecutionPayload["ingress"] | null = null;
  const ing = exactObject(own(root, "ingress"), INGRESS_KEYS, "$.ingress", c);
  if (ing !== null) {
    const agent_id = readString(own(ing, "agent_id"), "$.ingress.agent_id", LIMITS.MAX_AGENT_ID_LENGTH, c, AGENT_ID_RE);
    const policy_profile = readEnum(own(ing, "policy_profile"), POLICY_PROFILES, "$.ingress.policy_profile", c);
    const payload_raw = readString(own(ing, "payload_raw"), "$.ingress.payload_raw", LIMITS.MAX_PAYLOAD_RAW_LENGTH, c);
    if (agent_id !== null && policy_profile !== null && payload_raw !== null) {
      ingress = Object.freeze({ agent_id, policy_profile, payload_raw });
    }
  }

  let execution_dag: ExecutionDagNode[] | null = null;
  const rawDag = readArray(own(root, "execution_dag"), "$.execution_dag", LIMITS.MAX_DAG_NODES, c);
  if (rawDag !== null) {
    if (rawDag.length === 0) {
      c.fail("DAG_EMPTY", "$.execution_dag: un recibo sin nodos no tiene raíz Merkle definida");
    } else {
      execution_dag = [];
      let edges = 0;
      for (let i = 0; i < rawDag.length; i++) {
        const node = readNode(rawDag[i], `$.execution_dag[${i}]`, c);
        if (node === null) {
          execution_dag = null;
          // Se sigue recorriendo para informar de más nodos, hasta el tope del acumulador.
          if (c.full) {
            if (i < rawDag.length - 1) c.markTruncated();
            break;
          }
          continue;
        }
        edges += node.parent_ids.length;
        if (edges > LIMITS.MAX_DAG_EDGES) {
          c.fail("LIMIT_EXCEEDED", `$.execution_dag: más de ${LIMITS.MAX_DAG_EDGES} aristas`);
          execution_dag = null;
          break;
        }
        if (execution_dag !== null) execution_dag.push(node);
      }
    }
  }

  let cryptographic_seal: Babylon60ExecutionPayload["cryptographic_seal"] | null = null;
  const seal = exactObject(own(root, "cryptographic_seal"), SEAL_KEYS, "$.cryptographic_seal", c);
  if (seal !== null) {
    const phase_one_manifest_hash = readHex32(own(seal, "phase_one_manifest_hash"), "$.cryptographic_seal.phase_one_manifest_hash", c);
    const phase_two_merkle_root = readB3Root(own(seal, "phase_two_merkle_root"), "$.cryptographic_seal.phase_two_merkle_root", c);
    const ed25519_public_key = readHex32(own(seal, "ed25519_public_key"), "$.cryptographic_seal.ed25519_public_key", c);
    const ed25519_signature = readHex64(own(seal, "ed25519_signature"), "$.cryptographic_seal.ed25519_signature", c);

    let larsa_commit: Babylon60ExecutionPayload["cryptographic_seal"]["larsa_commit"] | null = null;
    const larsa = exactObject(own(seal, "larsa_commit"), LARSA_KEYS, "$.cryptographic_seal.larsa_commit", c);
    if (larsa !== null) {
      const trace_hash = readHex32(own(larsa, "trace_hash"), "$.cryptographic_seal.larsa_commit.trace_hash", c);
      const heuristic_weight = readU32(own(larsa, "heuristic_weight"), "$.cryptographic_seal.larsa_commit.heuristic_weight", c);
      if (trace_hash !== null && heuristic_weight !== null) {
        larsa_commit = Object.freeze({ trace_hash, heuristic_weight });
      }
    }

    let lean4_proof: Babylon60ExecutionPayload["cryptographic_seal"]["lean4_proof"] | null = null;
    const lean = exactObject(own(seal, "lean4_proof"), LEAN_KEYS, "$.cryptographic_seal.lean4_proof", c);
    if (lean !== null) {
      const status = readEnum(own(lean, "status"), LEAN_STATUSES, "$.cryptographic_seal.lean4_proof.status", c);
      const theorem_ident = readString(
        own(lean, "theorem_ident"),
        "$.cryptographic_seal.lean4_proof.theorem_ident",
        LIMITS.MAX_THEOREM_IDENT_LENGTH,
        c,
        THEOREM_IDENT_RE
      );
      const sorry_count = readUint(own(lean, "sorry_count"), "$.cryptographic_seal.lean4_proof.sorry_count", c);
      if (status !== null && theorem_ident !== null && sorry_count !== null) {
        lean4_proof = Object.freeze({ status, theorem_ident, sorry_count });
      }
    }

    if (
      phase_one_manifest_hash !== null &&
      phase_two_merkle_root !== null &&
      ed25519_public_key !== null &&
      ed25519_signature !== null &&
      larsa_commit !== null &&
      lean4_proof !== null
    ) {
      cryptographic_seal = Object.freeze({
        phase_one_manifest_hash,
        phase_two_merkle_root,
        ed25519_public_key,
        ed25519_signature,
        larsa_commit,
        lean4_proof,
      });
    }
  }

  let audit_metrics: Babylon60ExecutionPayload["audit_metrics"] | null = null;
  const audit = exactObject(own(root, "audit_metrics"), AUDIT_KEYS, "$.audit_metrics", c);
  if (audit !== null) {
    const memory_bytes = readUint(own(audit, "memory_bytes"), "$.audit_metrics.memory_bytes", c);
    const prev_receipt_hash = readHex32(own(audit, "prev_receipt_hash"), "$.audit_metrics.prev_receipt_hash", c);
    const worm_txid = readHex32(own(audit, "worm_txid"), "$.audit_metrics.worm_txid", c);
    if (memory_bytes !== null && prev_receipt_hash !== null && worm_txid !== null) {
      audit_metrics = Object.freeze({ memory_bytes, prev_receipt_hash, worm_txid });
    }
  }

  if (
    execution_id === null ||
    manifest_version === null ||
    causal_clock === null ||
    ingress === null ||
    execution_dag === null ||
    cryptographic_seal === null ||
    audit_metrics === null
  ) {
    return null;
  }
  return Object.freeze({
    execution_id,
    causal_clock,
    manifest_version,
    ingress,
    execution_dag: Object.freeze(execution_dag),
    cryptographic_seal,
    audit_metrics,
  });
}
