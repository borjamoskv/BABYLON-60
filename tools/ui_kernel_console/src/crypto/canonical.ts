/**
 * Preimágenes canónicas del recibo.
 *
 * Siguen el perfil ACS del kernel (`src/acs_bridge.rs`): cada preimagen es un array CBOR restringido
 * (uint, texto, bytes, arrays) cuyo primer elemento es una etiqueta de dominio versionada, y la
 * firma es un COSE_Sign1 con cabecera protegida `a1 01 27` (alg EdDSA), AAD externo vacío y clave
 * fijada por el verificador. De ahí se sigue que:
 *  - la codificación es inyectiva (CBOR delimita cada campo; ningún texto puede imitar un separador);
 *  - ninguna preimagen de un dominio puede leerse como de otro;
 *  - ninguna empieza por los prefijos "B60-LEAF-v1\0" / "B60-NODE-v1\0" / "B60-ROOT-v1\0" del árbol.
 *
 * Los booleanos se codifican como uint 0/1 y el valor opcional como array de 0 o 1 elementos, porque
 * el perfil restringido no tiene valores simples.
 *
 *   NODO       = ["BABYLON60_EXEC_NODE_V1", node_id, [padres ordenados por bytes], state_status,
 *                 smt_verified (0|1), reduction_steps, [] | [violation_reason]]
 *   state_hash = merkle_v1.leaf_hash(NODO)
 *   raíz       = merkle_v1.root(hojas ordenadas por los bytes de node_id)
 *
 *   MANIFIESTO = ["BABYLON60_EXEC_MANIFEST_V1", execution_id, manifest_version, policy_epoch,
 *                 logical_tick, seq_id, agent_id, policy_profile, payload_raw]
 *   phase_one_manifest_hash = BLAKE3(MANIFIESTO)
 *
 *   SOBRE      = ["BABYLON60_EXEC_RECEIPT_V1", execution_id, policy_epoch, logical_tick, seq_id,
 *                 h'manifest_hash', raíz ("b3:…"), h'larsa.trace_hash', larsa.heuristic_weight,
 *                 lean.status, lean.theorem_ident, lean.sorry_count,
 *                 memory_bytes, h'prev_receipt_hash', h'worm_txid']
 *   receipt_hash = BLAKE3(SOBRE)
 *
 *   A_FIRMAR   = ["Signature1", h'a10127', h'', SOBRE]          (Sig_structure, RFC 9052 §4.4)
 */

import { blake3 } from "./blake3.ts";
import { compareBytes, fromHexStrict, toHex, utf8 } from "./bytes.ts";
import { encodeCbor, type CborValue } from "./cbor.ts";
import { leafHash, rootFromLeafHashes } from "./merkleB3.ts";
import type { Babylon60ExecutionPayload, ExecutionDagNode } from "../types/babylon60.ts";

export const NODE_DOMAIN = "BABYLON60_EXEC_NODE_V1";
export const MANIFEST_DOMAIN = "BABYLON60_EXEC_MANIFEST_V1";
export const RECEIPT_DOMAIN = "BABYLON60_EXEC_RECEIPT_V1";

/** Cabecera protegida COSE del perfil ACS para Ed25519: el mapa {1 (alg): -8 (EdDSA)}. */
export const COSE_PROTECTED_ED25519: Uint8Array = Uint8Array.of(0xa1, 0x01, 0x27);
const COSE_SIGN1_CONTEXT = "Signature1";
const EMPTY = new Uint8Array(0);

export type NodeFields = Omit<ExecutionDagNode, "state_hash">;

/** Ordena cadenas por sus bytes UTF-8 (mismo resultado en Rust, Python y JavaScript). */
export function sortByUtf8(values: readonly string[]): string[] {
  return values
    .map((v) => ({ v, bytes: utf8(v) }))
    .sort((a, b) => compareBytes(a.bytes, b.bytes))
    .map((x) => x.v);
}

function hex32ToBytes(value: string): Uint8Array {
  const bytes = value.startsWith("0x") ? fromHexStrict(value.slice(2), 32) : null;
  if (bytes === null) throw new TypeError("se esperaba 0x + 64 dígitos hex en minúsculas");
  return bytes;
}

function bit(value: boolean): number {
  if (typeof value !== "boolean") throw new TypeError("se esperaba un booleano");
  return value ? 1 : 0;
}

function optionalText(value: string | null): CborValue {
  return value === null ? [] : [value];
}

export function nodePreimage(node: NodeFields): Uint8Array {
  return encodeCbor([
    NODE_DOMAIN,
    node.node_id,
    sortByUtf8(node.parent_ids),
    node.state_status,
    bit(node.smt_verified),
    node.reduction_steps,
    optionalText(node.violation_reason),
  ]);
}

/** Hash de hoja Merkle v1 del nodo, como bytes. */
export function nodeLeafHash(node: NodeFields): Uint8Array {
  return leafHash(nodePreimage(node));
}

/**
 * Raíz Merkle v1 del DAG a partir de hashes de hoja ya calculados (uno por nodo, en el orden de
 * `nodeIds`). Las hojas se ordenan por los bytes de `node_id`, así que el orden de llegada del
 * array es irrelevante. Precondición: identificadores únicos.
 */
export function dagMerkleRoot(nodeIds: readonly string[], leafHashes: readonly Uint8Array[]): string {
  if (nodeIds.length !== leafHashes.length) throw new RangeError("dagMerkleRoot: longitudes distintas");
  const order = nodeIds
    .map((id, i) => ({ i, bytes: utf8(id) }))
    .sort((a, b) => compareBytes(a.bytes, b.bytes));
  return rootFromLeafHashes(order.map((o) => leafHashes[o.i]!));
}

export type ManifestFields = Pick<Babylon60ExecutionPayload, "execution_id" | "manifest_version" | "causal_clock" | "ingress">;

export function manifestPreimage(p: ManifestFields): Uint8Array {
  return encodeCbor([
    MANIFEST_DOMAIN,
    p.execution_id,
    p.manifest_version,
    p.causal_clock.policy_epoch,
    p.causal_clock.logical_tick,
    p.causal_clock.seq_id,
    p.ingress.agent_id,
    p.ingress.policy_profile,
    p.ingress.payload_raw,
  ]);
}

export function manifestHashHex(p: ManifestFields): string {
  return "0x" + toHex(blake3(manifestPreimage(p)));
}

/** Campos que cubre el sobre firmado; los hashes van tal como los declara el recibo. */
export interface EnvelopeFields {
  readonly execution_id: string;
  readonly causal_clock: Babylon60ExecutionPayload["causal_clock"];
  readonly phase_one_manifest_hash: string;
  readonly phase_two_merkle_root: string;
  readonly larsa_commit: { readonly trace_hash: string; readonly heuristic_weight: number };
  readonly lean4_proof: { readonly status: string; readonly theorem_ident: string; readonly sorry_count: number };
  readonly audit_metrics: { readonly memory_bytes: number; readonly prev_receipt_hash: string; readonly worm_txid: string };
}

export function envelopeFieldsOf(p: Babylon60ExecutionPayload): EnvelopeFields {
  return {
    execution_id: p.execution_id,
    causal_clock: p.causal_clock,
    phase_one_manifest_hash: p.cryptographic_seal.phase_one_manifest_hash,
    phase_two_merkle_root: p.cryptographic_seal.phase_two_merkle_root,
    larsa_commit: p.cryptographic_seal.larsa_commit,
    lean4_proof: p.cryptographic_seal.lean4_proof,
    audit_metrics: p.audit_metrics,
  };
}

/** Sobre canónico del sello: los bytes que resume `receipt_hash` y que cubre la firma. */
export function receiptEnvelope(f: EnvelopeFields): Uint8Array {
  return encodeCbor([
    RECEIPT_DOMAIN,
    f.execution_id,
    f.causal_clock.policy_epoch,
    f.causal_clock.logical_tick,
    f.causal_clock.seq_id,
    hex32ToBytes(f.phase_one_manifest_hash),
    f.phase_two_merkle_root,
    hex32ToBytes(f.larsa_commit.trace_hash),
    f.larsa_commit.heuristic_weight,
    f.lean4_proof.status,
    f.lean4_proof.theorem_ident,
    f.lean4_proof.sorry_count,
    f.audit_metrics.memory_bytes,
    hex32ToBytes(f.audit_metrics.prev_receipt_hash),
    hex32ToBytes(f.audit_metrics.worm_txid),
  ]);
}

export function receiptHashHex(envelope: Uint8Array): string {
  return "0x" + toHex(blake3(envelope));
}

/**
 * Bytes que firma la autoridad: Sig_structure de COSE_Sign1 sobre `payload`, idéntica a
 * `signing_bytes` del kernel para una clave Ed25519.
 */
export function signatureInput(payload: Uint8Array): Uint8Array {
  return encodeCbor([COSE_SIGN1_CONTEXT, COSE_PROTECTED_ED25519, EMPTY, payload]);
}
