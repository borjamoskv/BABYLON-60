import assert from "node:assert/strict";
import { test } from "node:test";
import { toHex } from "../src/crypto/bytes.ts";
import { CborEncodeError, encodeCbor } from "../src/crypto/cbor.ts";
import {
  MANIFEST_DOMAIN,
  NODE_DOMAIN,
  RECEIPT_DOMAIN,
  dagMerkleRoot,
  manifestPreimage,
  nodeLeafHash,
  nodePreimage,
  receiptEnvelope,
  signatureInput,
  sortByUtf8,
  type EnvelopeFields,
  type NodeFields,
} from "../src/crypto/canonical.ts";

const H = (b: string): string => "0x" + b.repeat(32);

const envelope = (over: Partial<EnvelopeFields> = {}): EnvelopeFields => ({
  execution_id: "e",
  causal_clock: { policy_epoch: 1, logical_tick: 1, seq_id: 1 },
  phase_one_manifest_hash: H("11"),
  phase_two_merkle_root: "b3:" + "22".repeat(32),
  larsa_commit: { trace_hash: H("55"), heuristic_weight: 5 },
  lean4_proof: { status: "VERIFIED_NO_SORRY", theorem_ident: "T", sorry_count: 0 },
  audit_metrics: { memory_bytes: 1, prev_receipt_hash: H("33"), worm_txid: H("44") },
  ...over,
});

/** Transcripción del diseño de partida: campos de texto libre unidos por "|". */
function pipeJoinedTranscript(f: EnvelopeFields): string {
  const c = f.causal_clock;
  return [
    "BABYLON60_SEAL_V5",
    f.execution_id,
    `${c.policy_epoch}:${c.logical_tick}:${c.seq_id}`,
    f.phase_one_manifest_hash,
    f.phase_two_merkle_root,
    f.lean4_proof.theorem_ident,
    f.audit_metrics.prev_receipt_hash,
  ].join("|");
}

test("regresión: dos recibos que colisionaban bajo la unión con '|' tienen sobres distintos", () => {
  const p2 = H("aa");
  const r2 = "b3:" + "bb".repeat(32);
  const a = envelope({
    execution_id: "e",
    causal_clock: { policy_epoch: 1, logical_tick: 1, seq_id: 1 },
    lean4_proof: { status: "VERIFIED_NO_SORRY", theorem_ident: `x|2:2:2|${p2}|${r2}|T2`, sorry_count: 0 },
  });
  const b = envelope({
    execution_id: `e|1:1:1|${a.phase_one_manifest_hash}|${a.phase_two_merkle_root}|x`,
    causal_clock: { policy_epoch: 2, logical_tick: 2, seq_id: 2 },
    phase_one_manifest_hash: p2,
    phase_two_merkle_root: r2,
    lean4_proof: { status: "VERIFIED_NO_SORRY", theorem_ident: "T2", sorry_count: 0 },
  });
  assert.equal(pipeJoinedTranscript(a), pipeJoinedTranscript(b), "el contraejemplo debe colisionar en el formato de partida");
  assert.notDeepEqual(a.causal_clock, b.causal_clock);
  assert.notEqual(a.phase_two_merkle_root, b.phase_two_merkle_root);
  assert.notEqual(toHex(receiptEnvelope(a)), toHex(receiptEnvelope(b)));
  assert.notEqual(toHex(signatureInput(receiptEnvelope(a))), toHex(signatureInput(receiptEnvelope(b))));
});

test("sobre: cada campo cubierto cambia los bytes", () => {
  const base = toHex(receiptEnvelope(envelope()));
  const variants: Partial<EnvelopeFields>[] = [
    { execution_id: "f" },
    { causal_clock: { policy_epoch: 2, logical_tick: 1, seq_id: 1 } },
    { causal_clock: { policy_epoch: 1, logical_tick: 2, seq_id: 1 } },
    { causal_clock: { policy_epoch: 1, logical_tick: 1, seq_id: 2 } },
    { phase_one_manifest_hash: H("12") },
    { phase_two_merkle_root: "b3:" + "23".repeat(32) },
    { larsa_commit: { trace_hash: H("56"), heuristic_weight: 5 } },
    { larsa_commit: { trace_hash: H("55"), heuristic_weight: 6 } },
    { lean4_proof: { status: "FAILED_INVARIANT", theorem_ident: "T", sorry_count: 0 } },
    { lean4_proof: { status: "VERIFIED_NO_SORRY", theorem_ident: "U", sorry_count: 0 } },
    { lean4_proof: { status: "VERIFIED_NO_SORRY", theorem_ident: "T", sorry_count: 1 } },
    { audit_metrics: { memory_bytes: 2, prev_receipt_hash: H("33"), worm_txid: H("44") } },
    { audit_metrics: { memory_bytes: 1, prev_receipt_hash: H("34"), worm_txid: H("44") } },
    { audit_metrics: { memory_bytes: 1, prev_receipt_hash: H("33"), worm_txid: H("45") } },
  ];
  const seen = new Set([base]);
  for (const v of variants) {
    const hex = toHex(receiptEnvelope(envelope(v)));
    assert.ok(!seen.has(hex), JSON.stringify(v));
    seen.add(hex);
  }
  // Campos adyacentes del mismo tipo no son intercambiables.
  const swapped = envelope({ causal_clock: { policy_epoch: 1, logical_tick: 2, seq_id: 3 } });
  const other = envelope({ causal_clock: { policy_epoch: 3, logical_tick: 2, seq_id: 1 } });
  assert.notEqual(toHex(receiptEnvelope(swapped)), toHex(receiptEnvelope(other)));
});

const node = (over: Partial<NodeFields> = {}): NodeFields => ({
  node_id: "EV_00000001_000000",
  parent_ids: [],
  state_status: "COMMITTED",
  smt_verified: true,
  reduction_steps: 1,
  violation_reason: null,
  ...over,
});

test("nodo: la preimagen no depende del orden de los padres y cada campo la cambia", () => {
  const p = ["EV_00000003_000000", "EV_00000002_000000", "EV_00000010_000000"];
  const a = toHex(nodePreimage(node({ parent_ids: p })));
  assert.equal(toHex(nodePreimage(node({ parent_ids: [...p].reverse() }))), a);
  const variants: Partial<NodeFields>[] = [
    {},
    { node_id: "EV_00000001_000001" },
    { parent_ids: ["EV_00000002_000000"] },
    { state_status: "PENDING_SEAL" },
    { smt_verified: false },
    { reduction_steps: 2 },
    { reduction_steps: 0 },
    { violation_reason: "r" },
    { violation_reason: "" },
  ];
  assert.equal(new Set(variants.map((v) => toHex(nodePreimage(node(v))))).size, variants.length);
});

test("nodo: bytes exactos de una preimagen (perfil restringido: sin booleanos ni null)", () => {
  const bytes = nodePreimage(node({ parent_ids: ["EV_00000000_000000"], violation_reason: "x", smt_verified: false, reduction_steps: 300 }));
  const text = (s: string): string => toHex(encodeCbor(s));
  assert.equal(
    toHex(bytes),
    "87" + // array de 7
      text("BABYLON60_EXEC_NODE_V1") +
      text("EV_00000001_000000") +
      "81" + text("EV_00000000_000000") +
      text("COMMITTED") +
      "00" + // smt_verified = false
      "19012c" + // 300
      "81" + text("x")
  );
  assert.ok(toHex(nodePreimage(node())).endsWith("01" + "01" + "80"), "true = 1, pasos = 1, razón ausente = array vacío");
});

test("dominios: cada preimagen empieza por su etiqueta y no puede confundirse con las del árbol", () => {
  const startsWithTag = (bytes: Uint8Array, tag: string, arity: number): boolean => {
    const expected = Uint8Array.of(0x80 + arity, ...encodeCbor(tag));
    return expected.every((b, i) => bytes[i] === b);
  };
  assert.ok(startsWithTag(nodePreimage(node()), NODE_DOMAIN, 7));
  assert.ok(
    startsWithTag(
      manifestPreimage({
        execution_id: "e",
        manifest_version: "v1.0.0",
        causal_clock: { policy_epoch: 0, logical_tick: 0, seq_id: 0 },
        ingress: { agent_id: "a", policy_profile: "BFT_DEFENSIVE", payload_raw: "" },
      }),
      MANIFEST_DOMAIN,
      9
    )
  );
  assert.ok(startsWithTag(receiptEnvelope(envelope()), RECEIPT_DOMAIN, 15));
  assert.deepEqual([NODE_DOMAIN, MANIFEST_DOMAIN, RECEIPT_DOMAIN], ["BABYLON60_EXEC_NODE_V1", "BABYLON60_EXEC_MANIFEST_V1", "BABYLON60_EXEC_RECEIPT_V1"]);
  // Ninguna empieza por 'B' (0x42), primer byte de los prefijos B60-LEAF/NODE/ROOT del árbol.
  for (const bytes of [nodePreimage(node()), receiptEnvelope(envelope())]) assert.notEqual(bytes[0], 0x42);
});

test("orden por bytes UTF-8: no coincide con el orden por unidades UTF-16 cuando hay caracteres astrales", () => {
  const astral = "\u{1F600}"; // UTF-16: D83D DE00; UTF-8: F0 9F 98 80
  const bmpHigh = "\uff5e"; //    UTF-16: FF5E;      UTF-8: EF BD 9E
  assert.deepEqual([astral, bmpHigh].sort(), [astral, bmpHigh], "orden por unidades UTF-16");
  assert.deepEqual(sortByUtf8([astral, bmpHigh]), [bmpHigh, astral], "orden por bytes UTF-8");
});

test("raíz del DAG: independiente del orden de llegada y sensible al contenido", () => {
  const nodes = [node(), node({ node_id: "EV_00000002_000000", parent_ids: ["EV_00000001_000000"] }), node({ node_id: "EV_00000003_000000" })];
  const ids = nodes.map((n) => n.node_id);
  const hashes = nodes.map(nodeLeafHash);
  const root = dagMerkleRoot(ids, hashes);
  assert.match(root, /^b3:[0-9a-f]{64}$/);
  assert.equal(dagMerkleRoot([...ids].reverse(), [...hashes].reverse()), root);
  assert.notEqual(dagMerkleRoot(ids.slice(0, 2), hashes.slice(0, 2)), root);
  assert.throws(() => dagMerkleRoot(ids, hashes.slice(0, 2)), RangeError);
});

test("valores sin forma canónica no llegan a ninguna preimagen", () => {
  assert.throws(() => nodePreimage(node({ violation_reason: "\ud800" })), CborEncodeError);
  assert.throws(() => nodePreimage(node({ reduction_steps: 1.5 })), CborEncodeError);
  assert.throws(() => nodePreimage(node({ reduction_steps: -1 })), CborEncodeError);
  assert.throws(() => nodePreimage(node({ smt_verified: "true" as unknown as boolean })), TypeError);
  assert.throws(() => receiptEnvelope(envelope({ phase_one_manifest_hash: "0x00" })), TypeError);
  assert.throws(() => receiptEnvelope(envelope({ larsa_commit: { trace_hash: H("AA"), heuristic_weight: 1 } })), TypeError);
});
