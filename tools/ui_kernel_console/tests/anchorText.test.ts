import assert from "node:assert/strict";
import { test } from "node:test";
import {
  MAX_ANCHOR_TEXT_LENGTH,
  parseAnchorText,
  verifyExecutionPayloadJson,
  verifyExecutionPayloadWithAnchorText,
} from "../src/crypto/sealVerifier.ts";
import { jsonTextIssue } from "../src/crypto/jsonText.ts";
import { GOLDEN_POLICY, GOLDEN_RECEIPT } from "./fixtures/goldenReceipt.ts";

const receiptBytes = new TextEncoder().encode(JSON.stringify(GOLDEN_RECEIPT));
const KEY = GOLDEN_POLICY.admitted_authorities[0];
const anchor = (weight: string, extra = ""): string =>
  `{"admitted_authorities":["${KEY}"],"larsa_required_weight":${weight}${extra}}`;

test("ancla como texto: un entero vale en cualquier escritura que denote un entero seguro", async () => {
  for (const weight of ["4", "4.0", "4e0", "0.4e1", "4.000"]) {
    const verdict = await verifyExecutionPayloadWithAnchorText(receiptBytes, anchor(weight));
    assert.equal(verdict.ok, true, weight);
  }
});

test("ancla como texto: fracciones, cero, rangos y desbordamientos son TRUST_POLICY_INVALID", async () => {
  for (const weight of ["4.5", "0", "0.0", "-4", "4294967296", "9007199254740993", "1e400"]) {
    const verdict = await verifyExecutionPayloadWithAnchorText(receiptBytes, anchor(weight));
    assert.deepEqual(verdict.failures.map((f) => f.code), ["TRUST_POLICY_INVALID"], weight);
  }
});

test("ancla como texto: el seq_id del punto de control sigue la misma regla", async () => {
  const chain = (seq: string): string =>
    anchor("4", `,"previous_receipt":{"receipt_hash":"0x${"ab".repeat(32)}","seq_id":${seq}}`);
  for (const seq of ["0.0", "0e0", "-0.0"]) {
    const verdict = await verifyExecutionPayloadWithAnchorText(receiptBytes, chain(seq));
    assert.deepEqual(verdict.failures.map((f) => f.code), ["CHAIN_LINK_MISMATCH"], seq);
  }
  for (const seq of ["0.5", "-1", "1e400"]) {
    const verdict = await verifyExecutionPayloadWithAnchorText(receiptBytes, chain(seq));
    assert.deepEqual(verdict.failures.map((f) => f.code), ["TRUST_POLICY_INVALID"], seq);
  }
});

test("ancla como texto: una clave repetida, o un texto que no es JSON, es TRUST_POLICY_INVALID", async () => {
  const repeated = await verifyExecutionPayloadWithAnchorText(
    receiptBytes,
    anchor("4", `,"larsa_required_weight":1`)
  );
  assert.deepEqual(repeated.failures.map((f) => f.code), ["TRUST_POLICY_INVALID"]);
  for (const text of ["", "no es json", "[1,2]", "\uFEFF{}"]) {
    const verdict = await verifyExecutionPayloadWithAnchorText(receiptBytes, text);
    assert.deepEqual(verdict.failures.map((f) => f.code), ["TRUST_POLICY_INVALID"], JSON.stringify(text));
  }
});

test("ancla como texto: longitud máxima y tipo", () => {
  assert.equal(parseAnchorText(anchor("4")).ok, true);
  const tooLong = parseAnchorText("x".repeat(MAX_ANCHOR_TEXT_LENGTH + 1));
  assert.equal(tooLong.ok, false);
  assert.equal(parseAnchorText(42).ok, false);
});

test("recibo: una clave repetida se rechaza aunque la última copia sea la válida", async () => {
  const text = JSON.stringify(GOLDEN_RECEIPT);
  const id = GOLDEN_RECEIPT.execution_id;
  const forged = text.replace(
    `"execution_id":"${id}"`,
    `"execution_id":"FORGED-first","execution_id":"${id}"`
  );
  assert.notEqual(forged, text);
  assert.equal(jsonTextIssue(forged), "clave duplicada: execution_id");
  const verdict = await verifyExecutionPayloadJson(forged, GOLDEN_POLICY);
  assert.deepEqual(verdict.failures.map((f) => f.code), ["SCHEMA_INVALID"]);
});
