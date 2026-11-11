import assert from "node:assert/strict";
import { test } from "node:test";
import { isCanonicalEventId, preview } from "../src/crypto/schema.ts";
import { LIMITS, verifyExecutionPayload } from "../src/crypto/sealVerifier.ts";
import { expectRejected, sealed, testAuthority, viaJson } from "./helpers.ts";

type Path = readonly (string | number)[];

function* positions(value: unknown, path: Path = []): Generator<Path> {
  yield path;
  if (Array.isArray(value)) {
    for (let i = 0; i < value.length; i++) yield* positions(value[i], [...path, i]);
  } else if (typeof value === "object" && value !== null) {
    for (const key of Object.keys(value)) yield* positions((value as Record<string, unknown>)[key], [...path, key]);
  }
}

function getAt(root: unknown, path: Path): unknown {
  let cur = root;
  for (const key of path) cur = (cur as Record<string | number, unknown>)[key];
  return cur;
}

function withAt(root: unknown, path: Path, value: unknown): unknown {
  if (path.length === 0) return value;
  const copy = viaJson(root);
  const parent = getAt(copy, path.slice(0, -1)) as Record<string | number, unknown>;
  parent[path[path.length - 1]!] = value;
  return copy;
}

const REPLACEMENTS: readonly unknown[] = [
  null,
  true,
  false,
  0,
  1,
  -1,
  1.5,
  2 ** 53,
  1e21,
  "",
  "x",
  "0x" + "00".repeat(32),
  "0x" + "00".repeat(64),
  "b3:" + "00".repeat(32),
  "EV_00000000_000000",
  "COMMITTED",
  "PENDING_SEAL",
  [],
  [[]],
  {},
];

function noControlCharacters(text: string): boolean {
  for (let i = 0; i < text.length; i++) {
    const c = text.charCodeAt(i);
    if (c < 0x20 || (c >= 0x7f && c <= 0x9f) || (c >= 0x200b && c <= 0x200f) || (c >= 0x2028 && c <= 0x202e) || (c >= 0x2060 && c <= 0x206f)) return false;
  }
  return true;
}

test("toda mutación de un solo valor del recibo se rechaza", async () => {
  const strict = (await testAuthority()).policy;
  const clean = await sealed();
  assert.equal((await verifyExecutionPayload(clean, strict)).ok, true);

  let cases = 0;
  for (const path of positions(clean)) {
    const original = getAt(clean, path);
    for (const replacement of REPLACEMENTS) {
      if (JSON.stringify(replacement) === JSON.stringify(original)) continue;
      const mutated = withAt(clean, path, replacement);
      const verdict = await verifyExecutionPayload(mutated, strict);
      const where = `$.${path.join(".")} := ${JSON.stringify(replacement)}`;
      assert.equal(verdict.ok, false, `mutación aceptada: ${where}`);
      assert.equal(verdict.receipt, null, where);
      assert.ok(verdict.failures.length >= 1 && verdict.failures.length <= LIMITS.MAX_REPORTED_FAILURES, where);
      for (const f of verdict.failures) {
        assert.ok(f.detail.length <= 700, `detalle demasiado largo en ${where}`);
        assert.ok(noControlCharacters(f.detail), `detalle con caracteres de control en ${where}`);
      }
      cases++;
    }
  }
  assert.ok(cases > 1000, `solo ${cases} mutaciones`);
});

test("toda clave eliminada o añadida en cualquier objeto del recibo se rechaza", async () => {
  const strict = (await testAuthority()).policy;
  const clean = await sealed();
  let cases = 0;
  for (const path of positions(clean)) {
    const value = getAt(clean, path);
    if (typeof value !== "object" || value === null || Array.isArray(value)) continue;
    for (const key of Object.keys(value)) {
      const copy = viaJson(clean);
      delete (getAt(copy, path) as Record<string, unknown>)[key];
      expectRejected(await verifyExecutionPayload(copy, strict), ["SCHEMA_INVALID"], `sin ${path.join(".")}.${key}`);
      cases++;
    }
    for (const extra of ["extra", "__proto__", "constructor", "toString", "timestamp_unix", "enforceEd25519"]) {
      const copy = viaJson(clean);
      const target = getAt(copy, path) as Record<string, unknown>;
      Object.defineProperty(target, extra, { value: 1, enumerable: true, configurable: true, writable: true });
      expectRejected(await verifyExecutionPayload(copy, strict), ["SCHEMA_INVALID"], `con ${path.join(".")}.${extra}`);
      cases++;
    }
  }
  assert.ok(cases >= 100, `solo ${cases} casos`);
});

test("identificadores de evento: solo la forma canónica EV_{tick:08}_{seq:06}", () => {
  const ok = ["EV_00000000_000000", "EV_00001048_000003", "EV_99999999_999999", "EV_100000000_000000", "EV_00000001_1000000", "EV_18446744073709551615_4294967295"];
  const bad = [
    "",
    "n0_ingress_gate",
    "EV_1048_0",
    "EV_0001048_000003",
    "EV_00001048_00003",
    "EV_000001048_000003",
    "EV_00001048_0000003",
    "EV_18446744073709551616_000000",
    "EV_00000001_4294967296",
    "EV_100000000000000000000_000000",
    "ev_00001048_000003",
    "EV_00001048_000003 ",
    " EV_00001048_000003",
    "EV_00001048_000003\n",
    "EV_\uff10\uff10\uff1001048_000003",
    "EV_-0001048_000003",
    "EV_0000104a_000003",
    "EV_00001048-000003",
  ];
  for (const id of ok) assert.ok(isCanonicalEventId(id), id);
  for (const id of bad) assert.ok(!isCanonicalEventId(id), JSON.stringify(id));
});

test("campos de texto y números: solo se aceptan formas con codificación canónica única", async () => {
  const authority = await testAuthority();
  const reject = async (label: string, mutate: (w: Awaited<ReturnType<typeof sealed>>) => void, expected: string[]): Promise<void> => {
    const w = await sealed();
    mutate(w);
    expectRejected(await verifyExecutionPayload(w, authority.policy), expected, label);
  };
  const any = (w: unknown): Record<string, Record<string, unknown>> => w as Record<string, Record<string, unknown>>;

  for (const version of ["5.1.0", "v05.1.0", "v1e3.0.0", "v1.0", "v1.0.0-rc1", "v1.0.0 ", "V1.0.0", "v1.0.00"]) {
    await reject(`manifest_version ${version}`, (w) => void (w.manifest_version = version), ["SCHEMA_INVALID"]);
  }
  for (const id of ["", "a|b", "a b", "-a", "ñ", "a\u0000b", "x".repeat(LIMITS.MAX_EXECUTION_ID_LENGTH + 1)]) {
    await reject(`execution_id ${JSON.stringify(id).slice(0, 20)}`, (w) => void (w.execution_id = id), id.length > LIMITS.MAX_EXECUTION_ID_LENGTH ? ["LIMIT_EXCEEDED"] : ["SCHEMA_INVALID"]);
  }
  for (const agent of ["", "agent with space", "agente://ñ", "a\tb", "a\u202eb"]) {
    await reject(`agent_id ${JSON.stringify(agent)}`, (w) => void (w.ingress.agent_id = agent), ["SCHEMA_INVALID"]);
  }
  await reject("payload_raw con sustituto suelto", (w) => void (w.ingress.payload_raw = "a\ud800b"), ["SCHEMA_INVALID"]);
  await reject("violation_reason con sustituto suelto", (w) => void (w.execution_dag[2]!.violation_reason = "\udc00"), ["SCHEMA_INVALID"]);
  await reject("violation_reason vacío", (w) => void (w.execution_dag[2]!.violation_reason = ""), ["SCHEMA_INVALID"]);

  for (const n of [-1, 1.5, 2 ** 53, 1e21, Number.MAX_VALUE, "5", null, true, [], {}]) {
    await reject(`policy_epoch ${String(n)}`, (w) => void (any(w)["causal_clock"]!["policy_epoch"] = n), ["SCHEMA_INVALID"]);
    await reject(`reduction_steps ${String(n)}`, (w) => void ((w.execution_dag[0] as unknown as Record<string, unknown>)["reduction_steps"] = n), ["SCHEMA_INVALID"]);
  }
  for (const b of ["true", "false", 0, 1, null]) {
    await reject(`smt_verified ${String(b)}`, (w) => void ((w.execution_dag[0] as unknown as Record<string, unknown>)["smt_verified"] = b), ["SCHEMA_INVALID"]);
  }

  const hash = (await sealed()).execution_dag[0]!.state_hash;
  for (const h of [hash.toUpperCase(), "0X" + hash.slice(2), hash.slice(2), hash + "00", hash.slice(0, -1), hash.slice(0, -2), "0x" + "g".repeat(64), 5, null]) {
    await reject(`state_hash ${String(h).slice(0, 12)}`, (w) => void ((w.execution_dag[0] as unknown as Record<string, unknown>)["state_hash"] = h), ["SCHEMA_MALFORMED_HEX"]);
  }
  await reject("raíz con prefijo 0x", (w) => void (w.cryptographic_seal.phase_two_merkle_root = "0x" + "00".repeat(32)), ["SCHEMA_MALFORMED_HEX"]);
  await reject("DAG vacío", (w) => void (w.execution_dag = []), ["DAG_EMPTY"]);
});

test("-0 se trata como 0 y no abre una segunda forma del recibo", async () => {
  const authority = await testAuthority();
  const w = await sealed((u) => void (u.nodes[0]!.reduction_steps = 0));
  const text = JSON.stringify(w).replace('"reduction_steps":0', '"reduction_steps":-0');
  assert.ok(text.includes('"reduction_steps":-0'));
  const verdict = await verifyExecutionPayload(JSON.parse(text) as unknown, authority.policy);
  assert.ok(verdict.ok, JSON.stringify(verdict.failures));
  assert.ok(Object.is(verdict.receipt.payload.execution_dag[0]!.reduction_steps, 0));
});

test("preview: cita acotada y sin caracteres invisibles de una entrada hostil", () => {
  const hostile = "\u202e<script>alert(1)</script>\u0000" + "A".repeat(10_000);
  const quoted = preview(hostile);
  assert.ok(quoted.length < 200);
  assert.ok(noControlCharacters(quoted));
  assert.ok(quoted.startsWith('"\\u202e<script>'));
  assert.match(quoted, /…\(\+\d+\)"$/);
  assert.equal(preview({ a: 1 }), "object");
  assert.equal(preview([1]), "array");
  assert.equal(preview(null), "null");
  assert.equal(preview(undefined), "undefined");
});
