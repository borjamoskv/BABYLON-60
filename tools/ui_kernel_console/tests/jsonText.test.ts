import assert from "node:assert/strict";
import { test } from "node:test";
import { JSON_FORM_DETAIL, MAX_JSON_DEPTH, jsonTextIssue } from "../src/crypto/jsonText.ts";
import { verifyExecutionPayloadJson, verifyExecutionPayloadUtf8 } from "../src/crypto/sealVerifier.ts";
import { GOLDEN_POLICY, GOLDEN_RECEIPT } from "./fixtures/goldenReceipt.ts";

const goldenText = JSON.stringify(GOLDEN_RECEIPT);

test("jsonTextIssue: solo enteros canónicos", () => {
  assert.equal(jsonTextIssue('{"a":[0,1,23,-5,9007199254740991],"b":"1.5e3"}'), null);
  for (const token of ["1.0", "1e3", "2E-1", "-0", "0.5"]) {
    assert.equal(jsonTextIssue(`{"a":${token}}`), `número no entero o no canónico en el texto: ${token}`, token);
  }
});

test("jsonTextIssue: anidamiento hasta 127 contenedores, como serde_json", () => {
  const nested = (n: number): string => "[".repeat(n) + "]".repeat(n);
  assert.equal(MAX_JSON_DEPTH, 127);
  assert.equal(jsonTextIssue(nested(127)), null);
  assert.equal(jsonTextIssue(nested(128)), JSON_FORM_DETAIL);
});

test("jsonTextIssue: sustitutos UTF-16 solo en pares", () => {
  assert.equal(jsonTextIssue('"\\ud83d\\ude00"'), null);
  assert.equal(jsonTextIssue('"\u{1F600}"'), null);
  for (const text of ['"\\ud800"', '"\\udc00"', '"\\ud800\\u0041"', '"\\ud800x"', '"\ud800"', '"\udc00"']) {
    assert.equal(jsonTextIssue(text), JSON_FORM_DETAIL, text);
  }
});

test("jsonTextIssue: los defectos de forma prevalecen sobre los números", () => {
  assert.equal(jsonTextIssue('[1.5,"\\ud800"]'), JSON_FORM_DETAIL);
});

test("verifyExecutionPayloadJson/Utf8: el recibo dorado pasa por ambas entradas", async () => {
  assert.equal((await verifyExecutionPayloadJson(goldenText, GOLDEN_POLICY)).ok, true);
  assert.equal((await verifyExecutionPayloadUtf8(new TextEncoder().encode(goldenText), GOLDEN_POLICY)).ok, true);
});

test("verifyExecutionPayloadJson: 14.0 es válido para JSON.parse pero no para serde_json", async () => {
  const altered = goldenText.replace('"reduction_steps":14', '"reduction_steps":14.0');
  assert.notEqual(altered, goldenText);
  const verdict = await verifyExecutionPayloadJson(altered, GOLDEN_POLICY);
  assert.equal(verdict.ok, false);
  assert.deepEqual(verdict.failures.map((f) => f.code), ["SCHEMA_INVALID"]);
});

test("verifyExecutionPayloadUtf8: UTF-8 inválido, BOM y escapes sueltos se rechazan", async () => {
  const bytes = new TextEncoder().encode(goldenText);
  const cases: Uint8Array[] = [
    Uint8Array.from([...bytes, 0xff]),
    Uint8Array.from([0xef, 0xbb, 0xbf, ...bytes]),
    new TextEncoder().encode(goldenText.replace('\\"op\\"', '\\"\\ud800op\\"')),
  ];
  for (const input of cases) {
    const verdict = await verifyExecutionPayloadUtf8(input, GOLDEN_POLICY);
    assert.deepEqual(verdict.failures.map((f) => f.code), ["SCHEMA_INVALID"]);
  }
  assert.notEqual(new TextDecoder().decode(cases[2]), goldenText);
});
