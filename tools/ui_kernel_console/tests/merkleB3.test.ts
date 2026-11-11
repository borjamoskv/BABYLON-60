import assert from "node:assert/strict";
import { test } from "node:test";
import { toHex } from "../src/crypto/bytes.ts";
import { MerkleError, buildRoot, leafHash, nodeHash, rootFromLeafHashes, sealRoot } from "../src/crypto/merkleB3.ts";
import { BINARY_ROOTS, LEAF_HASHES, MERKLE_V1_SOURCE, NODE_HASHES, TEXT_ROOTS, type LeafData } from "./fixtures/merkleV1Vectors.ts";
import { lcgBytes } from "./lcg.ts";

const enc = new TextEncoder();
const bytesOf = (d: LeafData): Uint8Array => (d.t === "utf8" ? enc.encode(d.v) : lcgBytes(d.seed, d.len));

test("merkle v1: leaf_hash y node_hash coinciden con el módulo Python canónico del repositorio", () => {
  assert.match(MERKLE_V1_SOURCE, /merkle_b3\.py/);
  assert.ok(LEAF_HASHES.length >= 7 && NODE_HASHES.length >= 4);
  for (const v of LEAF_HASHES) assert.equal(toHex(leafHash(bytesOf(v.data))), v.hash, JSON.stringify(v.data));
  for (const v of NODE_HASHES) assert.equal(toHex(nodeHash(lcgBytes(v.leftSeed, 32), lcgBytes(v.rightSeed, 32))), v.hash);
});

test("merkle v1: raíces BISIM_LEAF_{i} coinciden para n = 1..17, 31..33, 64, 65, 100, 101, 257", () => {
  assert.ok(TEXT_ROOTS.length >= 25);
  for (const [n, root] of TEXT_ROOTS) {
    const leaves = Array.from({ length: n }, (_, i) => enc.encode(`BISIM_LEAF_${i}`));
    assert.equal(buildRoot(leaves), root, `n=${n}`);
  }
});

test("merkle v1: raíces sobre hojas binarias (incluida la hoja vacía) coinciden", () => {
  for (const v of BINARY_ROOTS) {
    const leaves = Array.from({ length: v.n }, (_, i) => lcgBytes(v.seed * 1000 + i, (i * 37) % 200));
    assert.equal(buildRoot(leaves), v.root, `n=${v.n}`);
  }
});

test("merkle v1: la raíz compromete la cardinalidad y el orden", () => {
  const [a, b, c] = ["a", "b", "c"].map((s) => enc.encode(s)) as [Uint8Array, Uint8Array, Uint8Array];
  assert.notEqual(buildRoot([a, b, c]), buildRoot([a, b, c, c]));
  assert.notEqual(buildRoot([a, b, c]), buildRoot([a, c, b]));
  assert.notEqual(buildRoot([a]), buildRoot([a, a]));
  // Una hoja no puede hacerse pasar por nodo interno: el hash de nodo no es hash de hoja de la concatenación.
  const forged = new Uint8Array(64);
  forged.set(leafHash(a), 0);
  forged.set(leafHash(b), 32);
  assert.notEqual(buildRoot([forged]), buildRoot([a, b]));
});

test("merkle v1: entradas inválidas se rechazan en lugar de producir una raíz", () => {
  assert.throws(() => buildRoot([]), MerkleError);
  assert.throws(() => rootFromLeafHashes([new Uint8Array(31)]), MerkleError);
  assert.throws(() => nodeHash(new Uint8Array(32), new Uint8Array(33)), MerkleError);
  assert.throws(() => sealRoot(new Uint8Array(32), 0), MerkleError);
  assert.throws(() => sealRoot(new Uint8Array(32), 1.5), MerkleError);
});
