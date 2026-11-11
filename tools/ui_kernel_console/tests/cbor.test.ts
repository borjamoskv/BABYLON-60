import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { blake3 } from "../src/crypto/blake3.ts";
import { fromHexStrict, toHex } from "../src/crypto/bytes.ts";
import { COSE_PROTECTED_ED25519, signatureInput } from "../src/crypto/canonical.ts";
import { CborEncodeError, encodeCbor, type CborValue } from "../src/crypto/cbor.ts";
import { CBOR_SOURCE, CBOR_VECTORS, type Desc } from "./fixtures/cborVectors.ts";
import { testSigners } from "./helpers.ts";
import { lcgBytes } from "./lcg.ts";

const unhex = (h: string): Uint8Array => {
  const b = fromHexStrict(h, h.length / 2);
  assert.ok(b, `hex inválido: ${h.slice(0, 16)}`);
  return b;
};

function build(d: Desc): CborValue {
  switch (d.t) {
    case "int":
      return d.v;
    case "text":
      return d.v;
    case "textRepeat":
      return d.unit.repeat(d.count);
    case "bytesLcg":
      return lcgBytes(d.seed, d.count);
    case "array":
      return d.v.map(build);
  }
}

test("cbor: coincide con cbor2 (canonical) en todos los vectores del perfil restringido", () => {
  assert.match(CBOR_SOURCE, /^cbor2 /);
  assert.ok(CBOR_VECTORS.length >= 40);
  for (const c of CBOR_VECTORS) {
    const encoded = encodeCbor(build(c.value));
    if (c.hex !== undefined) {
      assert.equal(toHex(encoded), c.hex, c.name);
    } else {
      assert.equal(encoded.length, c.len, c.name);
      assert.equal(toHex(blake3(encoded)), c.blake3, c.name);
    }
  }
});

test("cbor: todo lo que queda fuera del perfil del kernel se rechaza", () => {
  const bad: unknown[] = [
    -1,
    1.5,
    Number.NaN,
    Number.POSITIVE_INFINITY,
    2 ** 53,
    "\ud800",
    "a\udc00b",
    true,
    false,
    null,
    undefined,
    10n,
    { plain: "object" },
    new Map(),
    new Date(0),
    Symbol("x"),
    () => 0,
    [1, [2, [null]]],
    new Uint16Array(2),
  ];
  for (const v of bad) {
    assert.throws(() => encodeCbor(v as CborValue), CborEncodeError, String(v));
  }
  let deep: CborValue = [];
  for (let i = 0; i < 12; i++) deep = [deep];
  assert.throws(() => encodeCbor(deep), CborEncodeError);
});

test("cbor: -0 y 0 comparten codificación", () => {
  assert.equal(toHex(encodeCbor(-0)), "00");
  assert.equal(toHex(encodeCbor([0, -0])), "820000");
});

/** Localiza el archivo dorado del kernel subiendo desde el directorio del paquete. */
function kernelGoldenFile(): string {
  let dir = process.cwd();
  for (let i = 0; i < 6; i++) {
    const candidate = path.join(dir, "tests", "acs_cbor_golden.txt");
    if (existsSync(candidate)) return candidate;
    dir = path.dirname(dir);
  }
  assert.fail("no se encontró tests/acs_cbor_golden.txt del repositorio subiendo desde " + process.cwd());
}

test("bisimulación con el kernel: Sig_structure y claves idénticas a los vectores dorados de tests/acs_cbor_golden.txt", async () => {
  const golden = new Map<string, string>();
  for (const line of readFileSync(kernelGoldenFile(), "utf8").split("\n")) {
    const [name, hex] = line.trim().split(/\s+/);
    if (name !== undefined && hex !== undefined) golden.set(name, hex);
  }
  for (const name of ["root", "delegated", "grant", "call", "call_signing", "forensic", "forensic_signing", "cose_ed"]) {
    assert.ok(golden.has(name), `falta el vector ${name}`);
  }
  assert.equal(toHex(COSE_PROTECTED_ED25519), "a10127");

  // Las claves públicas `root` y `delegated` del kernel salen de las semillas 0x11 y 0x22 repetidas:
  // la derivación semilla → clave de las pruebas coincide con la del kernel.
  const { authorities } = await testSigners();
  assert.equal(authorities[0]!.publicKey, "0x" + golden.get("root"));
  assert.equal(authorities[1]!.publicKey, "0x" + golden.get("delegated"));

  // call_signing y forensic_signing son signing_bytes(clave Ed25519, payload) del kernel.
  assert.equal(toHex(signatureInput(unhex(golden.get("call")!))), golden.get("call_signing"));
  assert.equal(toHex(signatureInput(unhex(golden.get("forensic")!))), golden.get("forensic_signing"));

  // `grant` es ya una Sig_structure: se extrae su payload y se vuelve a envolver.
  const grant = golden.get("grant")!;
  const prefix = "846a5369676e61747572653143a1012740"; // pragma: allowlist secret
  assert.ok(grant.startsWith(prefix + "59"));
  const payloadLength = Number.parseInt(grant.slice(prefix.length + 2, prefix.length + 6), 16);
  const payloadHex = grant.slice(prefix.length + 6);
  assert.equal(payloadHex.length, payloadLength * 2);
  assert.equal(toHex(signatureInput(unhex(payloadHex))), grant);

  // El objeto exportado por el kernel lleva la misma cabecera protegida y el mismo payload.
  const forensic = golden.get("forensic")!;
  assert.ok(golden.get("cose_ed")!.startsWith("d28443a10127a0" + toHex(encodeCbor(unhex(forensic)))));
});
