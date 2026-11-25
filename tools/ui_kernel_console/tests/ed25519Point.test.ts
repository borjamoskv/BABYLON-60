import assert from "node:assert/strict";
import { test } from "node:test";
import { fromHexStrict, toHex } from "../src/crypto/bytes.ts";
import {
  IDENTITY,
  SUBGROUP_ORDER,
  classifyPoint,
  decodePointStrict,
  hasSmallOrder,
  isIdentity,
  isStrictSignatureEncoding,
  pointAdd,
  type AffinePoint,
} from "../src/crypto/ed25519Point.ts";

const unhex = (h: string): Uint8Array => {
  const b = fromHexStrict(h, h.length / 2);
  assert.ok(b);
  return b;
};

const F = "ff".repeat(30);
const Z = "00".repeat(30);
/** Los 8 puntos de orden pequeño en su codificación canónica. */
const SMALL_ORDER = [
  "01" + Z + "00", // identidad (orden 1)
  "ec" + F + "7f", // (0, -1), orden 2
  "00" + Z + "00", // orden 4
  "00" + Z + "80", // orden 4
  "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05", // orden 8 // pragma: allowlist secret
  "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85", // orden 8 // pragma: allowlist secret
  "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a", // orden 8 // pragma: allowlist secret
  "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa", // orden 8 // pragma: allowlist secret
];
/** Codificaciones no canónicas de esos mismos puntos (y ≥ p, o x = 0 con bit de signo). */
const NON_CANONICAL = [
  "01" + Z + "80",
  "ec" + F + "ff",
  "ed" + F + "7f",
  "ed" + F + "ff",
  "ee" + F + "7f",
  "ee" + F + "ff",
];
const RFC8032_KEYS = [
  "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", // pragma: allowlist secret
  "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", // pragma: allowlist secret
  "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025", // pragma: allowlist secret
];
const BASE_POINT = "5866666666666666666666666666666666666666666666666666666666666666";

function scalarMul(k: bigint, p: AffinePoint): AffinePoint {
  let result = IDENTITY;
  let addend = p;
  let e = k;
  while (e > 0n) {
    if ((e & 1n) === 1n) result = pointAdd(result, addend);
    addend = pointAdd(addend, addend);
    e >>= 1n;
  }
  return result;
}

test("puntos Ed25519: los 8 puntos de orden pequeño y sus 6 codificaciones no canónicas se rechazan", () => {
  for (const h of SMALL_ORDER) assert.equal(classifyPoint(unhex(h)), "SMALL_ORDER", h);
  for (const h of NON_CANONICAL) assert.equal(classifyPoint(unhex(h)), "NON_CANONICAL_OR_OFF_CURVE", h);
  assert.equal(new Set([...SMALL_ORDER, ...NON_CANONICAL]).size, 14);
});

test("puntos Ed25519: claves de RFC 8032, el punto base y claves recién generadas se aceptan", async () => {
  for (const h of [...RFC8032_KEYS, BASE_POINT]) assert.equal(classifyPoint(unhex(h)), "OK", h);
  for (let i = 0; i < 12; i++) {
    const pair = (await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"])) as CryptoKeyPair;
    const raw = new Uint8Array(await crypto.subtle.exportKey("raw", pair.publicKey));
    assert.equal(classifyPoint(raw), "OK", toHex(raw));
  }
});

test("puntos Ed25519: la ley de grupo implementada tiene el orden correcto ([ℓ]P = identidad, [8]P ≠ identidad)", async () => {
  const base = decodePointStrict(unhex(BASE_POINT));
  assert.ok(base);
  assert.equal(base.y * 5n % (2n ** 255n - 19n), 4n); // y = 4/5
  assert.ok(isIdentity(scalarMul(SUBGROUP_ORDER, base)));
  assert.ok(!hasSmallOrder(base));

  const pair = (await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"])) as CryptoKeyPair;
  const point = decodePointStrict(new Uint8Array(await crypto.subtle.exportKey("raw", pair.publicKey)));
  assert.ok(point);
  assert.ok(isIdentity(scalarMul(SUBGROUP_ORDER, point)));
  assert.ok(isIdentity(pointAdd(scalarMul(SUBGROUP_ORDER - 1n, point), point)));

  // Los puntos de orden pequeño tienen exactamente el orden que dice su etiqueta.
  const orders = [1n, 2n, 4n, 4n, 8n, 8n, 8n, 8n];
  SMALL_ORDER.forEach((h, i) => {
    const p = decodePointStrict(unhex(h));
    assert.ok(p, h);
    assert.ok(isIdentity(scalarMul(orders[i]!, p)), `orden de ${h}`);
    if (orders[i]! > 1n) assert.ok(!isIdentity(scalarMul(orders[i]! / 2n, p)), `orden mínimo de ${h}`);
  });
});

test("puntos Ed25519: la decodificación coincide con el criterio de Euler para y pequeños", () => {
  const P = 2n ** 255n - 19n;
  const pow = (b: bigint, e: bigint): bigint => {
    let r = 1n;
    let x = ((b % P) + P) % P;
    for (let k = e; k > 0n; k >>= 1n) {
      if (k & 1n) r = (r * x) % P;
      x = (x * x) % P;
    }
    return r;
  };
  const d = (((-121665n * pow(121666n, P - 2n)) % P) + P) % P;
  let onCurve = 0;
  let offCurve = 0;
  for (let y = 2n; y < 80n; y++) {
    const u = (y * y - 1n + P) % P;
    const v = (d * y * y + 1n) % P;
    const ratio = (u * pow(v, P - 2n)) % P;
    const isSquare = ratio === 0n || pow(ratio, (P - 1n) / 2n) === 1n;
    const bytes = new Uint8Array(32);
    bytes[0] = Number(y);
    assert.equal(decodePointStrict(bytes) !== null, isSquare, `y=${y}`);
    if (isSquare) onCurve++;
    else offCurve++;
  }
  assert.ok(onCurve > 10 && offCurve > 10);
});

test("puntos Ed25519: este runtime acepta la firma trivial con claves degeneradas (motivo del filtro)", async (t) => {
  const degenerate = new Uint8Array(64);
  degenerate[0] = 1; // R = identidad, S = 0
  let accepted = 0;
  for (const h of SMALL_ORDER) {
    let key: CryptoKey;
    try {
      key = await crypto.subtle.importKey("raw", unhex(h).slice().buffer, { name: "Ed25519" }, false, ["verify"]);
    } catch {
      continue;
    }
    for (let m = 0; m < 32; m++) {
      if (await crypto.subtle.verify({ name: "Ed25519" }, key, degenerate, new Uint8Array([m]))) {
        accepted++;
        break;
      }
    }
  }
  t.diagnostic(`claves de orden pequeño con las que el Ed25519 nativo aceptó la firma trivial: ${accepted}/8`);
  // Observación del runtime, no requisito: un runtime estricto daría 0 y el filtro seguiría siendo correcto.
  assert.ok(accepted >= 0);
});

test("firma estricta: R de orden pequeño o S no canónico se rechazan sin consultar al runtime", async () => {
  const pair = (await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"])) as CryptoKeyPair;
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, pair.privateKey, new Uint8Array([1, 2, 3])));
  assert.ok(isStrictSignatureEncoding(sig));

  const smallR = sig.slice();
  smallR.set(unhex(SMALL_ORDER[0]!), 0);
  assert.ok(!isStrictSignatureEncoding(smallR));

  // S' = S + ℓ: mismo escalar módulo ℓ, codificación no canónica.
  let s = 0n;
  for (let i = 63; i >= 32; i--) s = (s << 8n) | BigInt(sig[i]!);
  let sPrime = s + SUBGROUP_ORDER;
  const malleated = sig.slice();
  for (let i = 32; i < 64; i++) {
    malleated[i] = Number(sPrime & 0xffn);
    sPrime >>= 8n;
  }
  assert.ok(!isStrictSignatureEncoding(malleated));
  assert.ok(!isStrictSignatureEncoding(sig.subarray(0, 63)));
});
