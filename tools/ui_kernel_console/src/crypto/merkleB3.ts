/**
 * Merkle BLAKE3 versionado, esquema v1 (`INV_C5_ONWIRE_CANON`).
 *
 * Tercera implementación bisimilar de `crates/babylon-attest/src/merkle_b3.rs` y
 * `01_KISH_ENGINE/babylon60/attestation/merkle_b3.py`:
 *
 *   hoja  = BLAKE3("B60-LEAF-v1\0" || bytes)
 *   nodo  = BLAKE3("B60-NODE-v1\0" || izq || der)      (nodo impar emparejado consigo mismo)
 *   raíz  = "b3:" + hex(BLAKE3("B60-ROOT-v1\0" || n_hojas_u64_LE || nodo_superior))
 *
 * La separación de dominio impide que una hoja pase por nodo interno y la raíz compromete la
 * cardinalidad, de modo que `[a,b,c]` y `[a,b,c,c]` tienen raíces distintas aunque el nodo impar se
 * duplique. No se define raíz para el árbol vacío.
 */

import { blake3 } from "./blake3.ts";
import { concatBytes, toHex, u64le } from "./bytes.ts";

const ascii = (s: string): Uint8Array => Uint8Array.from(s, (ch) => ch.charCodeAt(0));

const LEAF_TAG = ascii("B60-LEAF-v1\0");
const NODE_TAG = ascii("B60-NODE-v1\0");
const ROOT_TAG_BYTES = ascii("B60-ROOT-v1\0");

/** Etiqueta de versión de las raíces emitidas. */
export const ROOT_TAG = "b3:";

export const DIGEST_BYTES = 32;

export class MerkleError extends Error {
  override readonly name = "MerkleError";
}

/** Hash de hoja con separación de dominio. */
export function leafHash(data: Uint8Array): Uint8Array {
  return blake3(concatBytes(LEAF_TAG, data));
}

/** Hash de nodo interno con separación de dominio. */
export function nodeHash(left: Uint8Array, right: Uint8Array): Uint8Array {
  if (left.length !== DIGEST_BYTES || right.length !== DIGEST_BYTES) {
    throw new MerkleError("nodeHash: cada hijo debe medir exactamente 32 bytes");
  }
  return blake3(concatBytes(NODE_TAG, left, right));
}

/** Sella el nodo superior junto con la cardinalidad y devuelve la raíz etiquetada `b3:<hex>`. */
export function sealRoot(top: Uint8Array, leafCount: number): string {
  if (top.length !== DIGEST_BYTES) {
    throw new MerkleError("sealRoot: el nodo superior debe medir exactamente 32 bytes");
  }
  if (!Number.isSafeInteger(leafCount) || leafCount < 1) {
    throw new MerkleError("sealRoot: cardinalidad inválida");
  }
  return ROOT_TAG + toHex(blake3(concatBytes(ROOT_TAG_BYTES, u64le(leafCount), top)));
}

/**
 * Raíz a partir de hashes de hoja ya calculados, en el orden dado.
 * Lanza `MerkleError("EMPTY_TREE")` si no hay hojas, igual que las implementaciones Rust y Python.
 */
export function rootFromLeafHashes(leafHashes: readonly Uint8Array[]): string {
  if (leafHashes.length === 0) throw new MerkleError("EMPTY_TREE");
  for (const h of leafHashes) {
    if (h.length !== DIGEST_BYTES) {
      throw new MerkleError("rootFromLeafHashes: cada hoja debe medir exactamente 32 bytes");
    }
  }
  let level: Uint8Array[] = [...leafHashes];
  while (level.length > 1) {
    const next: Uint8Array[] = [];
    for (let i = 0; i < level.length; i += 2) {
      const left = level[i]!;
      const right = level[i + 1] ?? left;
      next.push(nodeHash(left, right));
    }
    level = next;
  }
  return sealRoot(level[0]!, leafHashes.length);
}

/** Raíz a partir de los bytes de cada hoja (equivale a `build_root` en Rust y Python). */
export function buildRoot(leaves: readonly Uint8Array[]): string {
  return rootFromLeafHashes(leaves.map((l) => leafHash(l)));
}
