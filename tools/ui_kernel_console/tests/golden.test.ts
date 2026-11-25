import assert from "node:assert/strict";
import { test } from "node:test";
import { blake3 } from "../src/crypto/blake3.ts";
import { fromHexStrict, toHex } from "../src/crypto/bytes.ts";
import { manifestPreimage, nodePreimage, signatureInput, type ManifestFields, type NodeFields } from "../src/crypto/canonical.ts";
import { leafHash } from "../src/crypto/merkleB3.ts";
import { ed25519SignerFromSeed, sealReceipt, unsealedOf, wireEnvelope, wireReceiptHash, type WireExecutionPayload } from "../src/crypto/receiptSealer.ts";
import { verifyExecutionPayload } from "../src/crypto/sealVerifier.ts";
import { baseUnsealedReceipt } from "../src/demo/fixture.ts";
import { GOLDEN_INTERMEDIATE, GOLDEN_POLICY, GOLDEN_RECEIPT, GOLDEN_SEED_BYTE } from "./fixtures/goldenReceipt.ts";

const golden = GOLDEN_RECEIPT as WireExecutionPayload;

test("recibo dorado: la implementación reproduce byte a byte el recibo y cada valor intermedio", async () => {
  const signer = await ed25519SignerFromSeed(GOLDEN_SEED_BYTE.repeat(32));
  const wire = await sealReceipt(baseUnsealedReceipt(), signer);
  assert.deepEqual(JSON.parse(JSON.stringify(wire)), golden);
  assert.deepEqual(GOLDEN_POLICY.admitted_authorities, [signer.publicKey]);

  const unsealed = unsealedOf(wire);
  assert.equal(unsealed.nodes.length, 4);
  for (const node of unsealed.nodes) {
    const preimage = nodePreimage(node as unknown as NodeFields);
    assert.equal(toHex(preimage), (GOLDEN_INTERMEDIATE.node_preimages as Record<string, string>)[node.node_id], node.node_id);
    const declared = golden.execution_dag.find((n) => n.node_id === node.node_id);
    assert.equal("0x" + toHex(leafHash(preimage)), declared?.state_hash, node.node_id);
  }
  assert.equal(toHex(manifestPreimage(wire as unknown as ManifestFields)), GOLDEN_INTERMEDIATE.manifest_preimage);
  const envelope = wireEnvelope(wire);
  assert.equal(toHex(envelope), GOLDEN_INTERMEDIATE.envelope);
  assert.equal(toHex(signatureInput(envelope)), GOLDEN_INTERMEDIATE.signature_input);
  assert.equal(wireReceiptHash(wire), GOLDEN_INTERMEDIATE.receipt_hash);
  assert.equal("0x" + toHex(blake3(envelope)), GOLDEN_INTERMEDIATE.receipt_hash);
});

test("recibo dorado: se acepta con su ancla y la firma valida exactamente la entrada de firma registrada", async () => {
  const verdict = await verifyExecutionPayload(JSON.parse(JSON.stringify(golden)) as unknown, GOLDEN_POLICY);
  assert.ok(verdict.ok, JSON.stringify(verdict.failures));
  assert.equal(verdict.receipt.receipt_hash, GOLDEN_INTERMEDIATE.receipt_hash);

  const unhex = (h: string): ArrayBuffer => {
    const b = fromHexStrict(h, h.length / 2);
    assert.ok(b);
    return b.slice().buffer;
  };
  const key = await crypto.subtle.importKey("raw", unhex(golden.cryptographic_seal.ed25519_public_key.slice(2)), { name: "Ed25519" }, false, ["verify"]);
  const ok = await crypto.subtle.verify({ name: "Ed25519" }, key, unhex(golden.cryptographic_seal.ed25519_signature.slice(2)), unhex(GOLDEN_INTERMEDIATE.signature_input));
  assert.equal(ok, true);
});
