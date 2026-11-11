/**
 * Sellado de recibos para pruebas y para la consola de demostración.
 *
 * NO es el emisor del kernel: ningún componente Rust o Python del repositorio produce todavía este
 * formato. Este módulo sirve de especificación ejecutable de lo que un emisor tendría que calcular
 * (hojas, raíz, compromiso del manifiesto, sobre y firma) y permite construir casos adversariales.
 */

import { fromHexStrict, toHex } from "./bytes.ts";
import {
  dagMerkleRoot,
  manifestHashHex,
  nodeLeafHash,
  receiptEnvelope,
  receiptHashHex,
  signatureInput,
  type ManifestFields,
  type NodeFields,
} from "./canonical.ts";
import type { Babylon60ExecutionPayload, ExecutionDagNode } from "../types/babylon60.ts";

/** Forma del recibo tal como viaja en JSON: mutable y sin marcas de tipo. */
export type Wire<T> = T extends string
  ? string
  : T extends number | boolean | null
    ? T
    : T extends readonly (infer U)[]
      ? Wire<U>[]
      : { -readonly [K in keyof T]: Wire<T[K]> };

export type WireExecutionPayload = Wire<Babylon60ExecutionPayload>;
export type WireNode = Wire<ExecutionDagNode>;

/** Lo que aporta un emisor antes de sellar: todo salvo hashes y firma. */
export interface UnsealedReceipt {
  readonly execution_id: string;
  readonly causal_clock: { readonly policy_epoch: number; readonly logical_tick: number; readonly seq_id: number };
  readonly manifest_version: string;
  readonly ingress: { readonly agent_id: string; readonly policy_profile: string; readonly payload_raw: string };
  readonly nodes: readonly Wire<NodeFields>[];
  readonly larsa_commit: { readonly trace_hash: string; readonly heuristic_weight: number };
  readonly lean4_proof: { readonly status: string; readonly theorem_ident: string; readonly sorry_count: number };
  readonly audit_metrics: { readonly memory_bytes: number; readonly prev_receipt_hash: string; readonly worm_txid: string };
}

export interface ReceiptSigner {
  /** `0x` + 64 dígitos hex en minúsculas. */
  readonly publicKey: string;
  sign(message: Uint8Array): Promise<Uint8Array>;
}

interface SubtleSignLike {
  importKey(
    format: "pkcs8",
    keyData: ArrayBuffer,
    algorithm: { name: string },
    extractable: boolean,
    keyUsages: readonly KeyUsage[]
  ): Promise<CryptoKey>;
  generateKey(algorithm: { name: string }, extractable: boolean, keyUsages: readonly KeyUsage[]): Promise<CryptoKeyPair | CryptoKey>;
  exportKey(format: "raw" | "jwk", key: CryptoKey): Promise<ArrayBuffer | JsonWebKey>;
  sign(algorithm: { name: string }, key: CryptoKey, data: ArrayBuffer): Promise<ArrayBuffer>;
}

const ED25519 = Object.freeze({ name: "Ed25519" });
// PrivateKeyInfo (RFC 8410) de una semilla Ed25519 de 32 bytes.
const PKCS8_ED25519_PREFIX = "302e020100300506032b657004220420";

function subtleOrThrow(): SubtleSignLike {
  const subtle = (globalThis as { crypto?: { subtle?: unknown } }).crypto?.subtle;
  if (typeof subtle !== "object" || subtle === null) throw new Error("WebCrypto no disponible");
  return subtle as SubtleSignLike;
}

function base64UrlToBytes(text: string): Uint8Array {
  const b64 = text.replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(b64 + "=".repeat((4 - (b64.length % 4)) % 4));
  return Uint8Array.from(bin, (ch) => ch.charCodeAt(0));
}

function signerFromKeys(subtle: SubtleSignLike, privateKey: CryptoKey, publicKeyBytes: Uint8Array): ReceiptSigner {
  return Object.freeze({
    publicKey: "0x" + toHex(publicKeyBytes),
    async sign(message: Uint8Array): Promise<Uint8Array> {
      return new Uint8Array(await subtle.sign(ED25519, privateKey, message.slice().buffer));
    },
  });
}

/**
 * Firmante a partir de una semilla de 32 bytes en hex. Solo para vectores de prueba reproducibles:
 * una semilla escrita en el código no protege nada.
 */
export async function ed25519SignerFromSeed(seedHex: string): Promise<ReceiptSigner> {
  const subtle = subtleOrThrow();
  const pkcs8 = fromHexStrict(PKCS8_ED25519_PREFIX + seedHex, 48);
  if (pkcs8 === null) throw new TypeError("la semilla debe ser 64 dígitos hex en minúsculas");
  // Extraíble solo para derivar la clave pública vía JWK.
  const privateKey = await subtle.importKey("pkcs8", pkcs8.slice().buffer, ED25519, true, ["sign"]);
  const jwk = (await subtle.exportKey("jwk", privateKey)) as JsonWebKey;
  if (typeof jwk.x !== "string") throw new Error("el runtime no expuso la clave pública Ed25519");
  return signerFromKeys(subtle, privateKey, base64UrlToBytes(jwk.x));
}

/** Firmante efímero: la clave privada no es extraíble y desaparece con la página. */
export async function generateEphemeralSigner(): Promise<ReceiptSigner> {
  const subtle = subtleOrThrow();
  const pair = (await subtle.generateKey(ED25519, false, ["sign", "verify"])) as CryptoKeyPair;
  const raw = (await subtle.exportKey("raw", pair.publicKey)) as ArrayBuffer;
  return signerFromKeys(subtle, pair.privateKey, new Uint8Array(raw));
}

/** Sobre canónico de un recibo en forma de transporte (usa los hashes que el recibo declara). */
export function wireEnvelope(wire: WireExecutionPayload): Uint8Array {
  return receiptEnvelope({
    execution_id: wire.execution_id,
    causal_clock: wire.causal_clock,
    phase_one_manifest_hash: wire.cryptographic_seal.phase_one_manifest_hash,
    phase_two_merkle_root: wire.cryptographic_seal.phase_two_merkle_root,
    larsa_commit: wire.cryptographic_seal.larsa_commit,
    lean4_proof: wire.cryptographic_seal.lean4_proof,
    audit_metrics: wire.audit_metrics,
  });
}

/** `receipt_hash` de un recibo en forma de transporte. */
export function wireReceiptHash(wire: WireExecutionPayload): string {
  return receiptHashHex(wireEnvelope(wire));
}

/** Sustituye clave y firma por las de `signer` sobre el sobre actual del recibo. */
export async function signWire(wire: WireExecutionPayload, signer: ReceiptSigner): Promise<WireExecutionPayload> {
  const signature = await signer.sign(signatureInput(wireEnvelope(wire)));
  return {
    ...wire,
    cryptographic_seal: {
      ...wire.cryptographic_seal,
      ed25519_public_key: signer.publicKey,
      ed25519_signature: "0x" + toHex(signature),
    },
  };
}

/** Sella un recibo completo: hojas, raíz, compromiso del manifiesto y firma de `signer`. */
export async function sealReceipt(u: UnsealedReceipt, signer: ReceiptSigner): Promise<WireExecutionPayload> {
  const leafHashes = u.nodes.map((n) => nodeLeafHash(n as unknown as NodeFields));
  const execution_dag: WireNode[] = u.nodes.map((n, i) => ({
    node_id: n.node_id,
    parent_ids: [...n.parent_ids],
    state_status: n.state_status,
    smt_verified: n.smt_verified,
    reduction_steps: n.reduction_steps,
    state_hash: "0x" + toHex(leafHashes[i]!),
    violation_reason: n.violation_reason,
  }));
  const manifest = {
    execution_id: u.execution_id,
    manifest_version: u.manifest_version,
    causal_clock: { ...u.causal_clock },
    ingress: { ...u.ingress },
  };
  const unsigned: WireExecutionPayload = {
    ...manifest,
    execution_dag,
    cryptographic_seal: {
      phase_one_manifest_hash: manifestHashHex(manifest as unknown as ManifestFields),
      phase_two_merkle_root: dagMerkleRoot(
        u.nodes.map((n) => n.node_id),
        leafHashes
      ),
      ed25519_public_key: signer.publicKey,
      ed25519_signature: "0x" + "00".repeat(64),
      larsa_commit: { ...u.larsa_commit },
      lean4_proof: { ...u.lean4_proof },
    },
    audit_metrics: { ...u.audit_metrics },
  };
  return signWire(unsigned, signer);
}

/** Extrae de un recibo en forma de transporte los campos que un emisor aporta (sin hashes ni firma). */
export function unsealedOf(wire: WireExecutionPayload): UnsealedReceipt {
  return {
    execution_id: wire.execution_id,
    causal_clock: { ...wire.causal_clock },
    manifest_version: wire.manifest_version,
    ingress: { ...wire.ingress },
    nodes: wire.execution_dag.map((n) => ({
      node_id: n.node_id,
      parent_ids: [...n.parent_ids],
      state_status: n.state_status,
      smt_verified: n.smt_verified,
      reduction_steps: n.reduction_steps,
      violation_reason: n.violation_reason,
    })) as Wire<NodeFields>[],
    larsa_commit: { ...wire.cryptographic_seal.larsa_commit },
    lean4_proof: { ...wire.cryptographic_seal.lean4_proof },
    audit_metrics: { ...wire.audit_metrics },
  };
}
