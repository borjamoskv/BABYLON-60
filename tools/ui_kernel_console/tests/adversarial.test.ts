import assert from "node:assert/strict";
import { test } from "node:test";
import { isAcceptedReceipt, verifyExecutionPayload } from "../src/crypto/sealVerifier.ts";
import { MODES, buildFixture, createDemoAuthority } from "../src/demo/fixture.ts";
import { testAuthority } from "./helpers.ts";

test("modos adversariales: cada modo produce exactamente los códigos declarados (ancla efímera y ancla de pruebas)", async () => {
  for (const demo of [await createDemoAuthority(), await testAuthority()]) {
    for (const spec of MODES) {
      const input = await buildFixture(spec.mode, demo);
      const verdict = await verifyExecutionPayload(input, demo.policy);
      const codes = [...new Set(verdict.failures.map((f) => f.code))].sort();
      assert.deepEqual(codes, [...spec.expected].sort(), `${spec.mode}: ${JSON.stringify(verdict.failures)}`);
      assert.equal(verdict.ok, spec.expected.length === 0, spec.mode);
      if (verdict.ok) {
        assert.ok(isAcceptedReceipt(verdict.receipt));
        assert.equal(verdict.receipt.signer, demo.authority.publicKey);
      } else {
        assert.equal(verdict.receipt, null);
      }
    }
  }
});

test("modos adversariales: nombres únicos y un único modo sin fallos", () => {
  assert.equal(new Set(MODES.map((m) => m.mode)).size, MODES.length);
  assert.equal(new Set(MODES.map((m) => m.label)).size, MODES.length);
  assert.deepEqual(MODES.filter((m) => m.expected.length === 0).map((m) => m.mode), ["CLEAN_TRACE"]);
  for (const label of ["Bit-Flip Leaf Hash", "Inject Causal Cycle", "Drop BFT Quorum"]) {
    assert.ok(MODES.some((m) => m.label === label), `falta el mutador ${label}`);
  }
});
