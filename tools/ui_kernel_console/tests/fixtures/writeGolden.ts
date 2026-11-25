/**
 * Regenera `goldenReceipt.ts`: el recibo de la traza base sellado con la semilla de prueba 0x11
 * repetida, junto a cada valor intermedio. Uso, tras `npm test` (que compila las pruebas):
 *
 *   node scratch/test-build/tests/fixtures/writeGolden.js > tests/fixtures/goldenReceipt.ts
 *
 * El archivo fija los bytes del formato y sirve de objetivo a implementaciones independientes.
 */

import { toHex } from "../../src/crypto/bytes.ts";
import { manifestPreimage, nodePreimage, signatureInput, type ManifestFields, type NodeFields } from "../../src/crypto/canonical.ts";
import { ed25519SignerFromSeed, sealReceipt, unsealedOf, wireEnvelope, wireReceiptHash } from "../../src/crypto/receiptSealer.ts";
import { DEMO_LARSA_REQUIRED_WEIGHT, baseUnsealedReceipt } from "../../src/demo/fixture.ts";

const PRAGMA = " // pragma: allowlist secret";

function withPragma(text: string): string {
  return text
    .split("\n")
    .map((line) => (/[0-9a-f]{20,}/.test(line) ? line + PRAGMA : line))
    .join("\n");
}

const signer = await ed25519SignerFromSeed("11".repeat(32));
const wire = await sealReceipt(baseUnsealedReceipt(), signer);
const unsealed = unsealedOf(wire);
const envelope = wireEnvelope(wire);

const intermediate = {
  node_preimages: Object.fromEntries(unsealed.nodes.map((n) => [n.node_id, toHex(nodePreimage(n as unknown as NodeFields))])),
  manifest_preimage: toHex(manifestPreimage(wire as unknown as ManifestFields)),
  envelope: toHex(envelope),
  signature_input: toHex(signatureInput(envelope)),
  receipt_hash: wireReceiptHash(wire),
};
const policy = { admitted_authorities: [signer.publicKey], larsa_required_weight: DEMO_LARSA_REQUIRED_WEIGHT };

const out = [
  "// Generado por tests/fixtures/writeGolden.ts. No editar a mano.",
  "",
  "/** Semilla Ed25519 de prueba: este byte repetido 32 veces (la misma que usan los vectores ACS del kernel). */",
  'export const GOLDEN_SEED_BYTE = "11";',
  "",
  `export const GOLDEN_POLICY = ${JSON.stringify(policy, null, 2)};`,
  "",
  "/** Recibo tal como viaja en JSON. */",
  `export const GOLDEN_RECEIPT = ${JSON.stringify(wire, null, 2)};`,
  "",
  "/** Bytes intermedios en hex: preimagen de cada nodo, manifiesto, sobre y entrada de la firma. */",
  `export const GOLDEN_INTERMEDIATE = ${JSON.stringify(intermediate, null, 2)};`,
  "",
].join("\n");

process.stdout.write(withPragma(out));
