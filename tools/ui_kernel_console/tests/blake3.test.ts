import assert from "node:assert/strict";
import { test } from "node:test";
import { blake3 } from "../src/crypto/blake3.ts";
import { toHex } from "../src/crypto/bytes.ts";
import { BLAKE3_ABC, BLAKE3_KAT, BLAKE3_KAT_SOURCE } from "./fixtures/blake3Kat.ts";

test("blake3: vectores de respuesta conocida de la implementación oficial (0 a 102400 bytes)", () => {
  assert.match(BLAKE3_KAT_SOURCE, /blake3/);
  assert.equal(BLAKE3_KAT.length, 35);
  for (const [len, hash] of BLAKE3_KAT) {
    const input = new Uint8Array(len);
    for (let i = 0; i < len; i++) input[i] = i % 251;
    assert.equal(toHex(blake3(input)), hash, `len=${len}`);
  }
});

test("blake3: entrada vacía y 'abc'", () => {
  assert.equal(toHex(blake3(new Uint8Array(0))), BLAKE3_KAT[0]![1]);
  assert.equal(toHex(blake3(new TextEncoder().encode("abc"))), BLAKE3_ABC);
});

test("blake3: no depende del desplazamiento de la vista ni muta la entrada", () => {
  const backing = new Uint8Array(5000);
  for (let i = 0; i < backing.length; i++) backing[i] = (i * 7 + 3) % 256;
  const view = backing.subarray(11, 11 + 3000);
  const copy = view.slice();
  const before = backing.slice();
  assert.equal(toHex(blake3(view)), toHex(blake3(copy)));
  assert.deepEqual(backing, before);
});
