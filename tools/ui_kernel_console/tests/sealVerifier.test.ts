import assert from "node:assert/strict";
import { test } from "node:test";
import { sealReceipt, signWire, unsealedOf, wireReceiptHash, type UnsealedReceipt } from "../src/crypto/receiptSealer.ts";
import { LIMITS, MAX_ADMITTED_AUTHORITIES, createReceiptVerifier, isAcceptedReceipt, verifyExecutionPayload, verifyExecutionPayloadJson } from "../src/crypto/sealVerifier.ts";
import type { TrustPolicy } from "../src/types/babylon60.ts";
import { N0, N1, N2, N3, type MutableUnsealed, expectRejected, sealed, testAuthority, testSigners, viaJson } from "./helpers.ts";

function isDeepFrozen(value: unknown): boolean {
  if (typeof value !== "object" || value === null) return true;
  if (!Object.isFrozen(value)) return false;
  return Object.values(value as Record<string, unknown>).every(isDeepFrozen);
}

test("recibo íntegro: aceptado, inmutable, con orden topológico y alcance explícito de cada comprobación", async () => {
  const demo = await testAuthority();
  const verdict = await verifyExecutionPayload(await sealed(), demo.policy);
  assert.ok(verdict.ok, JSON.stringify(verdict.failures));
  const r = verdict.receipt;
  assert.ok(isAcceptedReceipt(r));
  assert.ok(isDeepFrozen(r) && Object.isFrozen(verdict));
  assert.deepEqual(r.nodes.map((n) => [n.node.node_id, n.depth]), [[N0, 0], [N1, 1], [N2, 1], [N3, 2]]);
  assert.equal(r.signer, demo.authority.publicKey);
  assert.equal(r.larsa_required_weight, 4);
  assert.deepEqual(r.assurances, {
    structure: "COINCIDE",
    dag_acyclic: "COINCIDE",
    leaf_hashes: "COINCIDE",
    merkle_root: "COINCIDE",
    manifest_binding: "COINCIDE",
    authority_signature: "COINCIDE",
    larsa_commit: "DECLARADO",
    lean4_proof: "DECLARADO",
    worm_audit: "DECLARADO",
    chain_link: "NO_VERIFICADO",
  });
  assert.match(r.receipt_hash, /^0x[0-9a-f]{64}$/);
  assert.throws(() => {
    (r.payload.execution_dag[0] as { smt_verified: boolean }).smt_verified = false;
  }, TypeError);
  assert.throws(() => {
    (r.nodes as unknown as unknown[]).push({});
  }, TypeError);
});

test("un objeto con forma de recibo aceptado no pasa por aceptado", async () => {
  const demo = await testAuthority();
  const verdict = await verifyExecutionPayload(await sealed(), demo.policy);
  assert.ok(verdict.ok);
  assert.ok(!isAcceptedReceipt(structuredClone(verdict.receipt)));
  assert.ok(!isAcceptedReceipt({ ...verdict.receipt }));
  assert.ok(!isAcceptedReceipt(null) && !isAcceptedReceipt("x") && !isAcceptedReceipt(undefined));
});

test("determinismo: el orden de llegada de nodos y padres no altera raíz, hash ni veredicto", async () => {
  const demo = await testAuthority();
  const extra = "EV_00001049_000000";
  const base = await sealed((u) => {
    u.nodes.push({ node_id: extra, parent_ids: [N3, N1, N0], state_status: "COMMITTED", smt_verified: true, reduction_steps: 7, violation_reason: null });
  });
  const permuted = viaJson(base);
  permuted.execution_dag.reverse();
  for (const n of permuted.execution_dag) n.parent_ids.reverse();

  const a = await verifyExecutionPayload(base, demo.policy);
  const b = await verifyExecutionPayload(permuted, demo.policy);
  assert.ok(a.ok && b.ok, JSON.stringify([a.failures, b.failures]));
  assert.equal(a.receipt.receipt_hash, b.receipt.receipt_hash);
  assert.deepEqual(a.receipt.nodes.map((n) => [n.node.node_id, n.depth]), b.receipt.nodes.map((n) => [n.node.node_id, n.depth]));
  assert.deepEqual(a.receipt.nodes.map((n) => n.depth), [0, 1, 1, 2, 3]);
  // Mismo recibo sellado dos veces: mismos bytes (Ed25519 es determinista).
  assert.deepEqual(await sealed(), await sealed());
});

// ---- Ancla de confianza -------------------------------------------------------------------

const commitIntercepted = (u: MutableUnsealed): void => {
  u.nodes[2]!.state_status = "COMMITTED";
  u.nodes[2]!.violation_reason = null;
};

test("regresión: un resellado coherente con clave propia del atacante se rechaza", async () => {
  const demo = await testAuthority();
  const forged = await sealed(commitIntercepted, demo.rogue);
  expectRejected(await verifyExecutionPayload(forged, demo.policy), ["AUTHORITY_NOT_ADMITTED"]);
  // Nombrar la clave admitida sin poder firmar con ella tampoco sirve.
  forged.cryptographic_seal.ed25519_public_key = demo.authority.publicKey;
  expectRejected(await verifyExecutionPayload(forged, demo.policy), ["ED25519_SIGNATURE_INVALID"]);
});

test("regresión: no existe verificación sin ancla de confianza válida", async () => {
  const demo = await testAuthority();
  const input = await sealed();
  const key = demo.authority.publicKey;
  const bad: unknown[] = [
    undefined,
    null,
    {},
    [],
    "policy",
    { admitted_authorities: [], larsa_required_weight: 1 },
    { admitted_authorities: key, larsa_required_weight: 1 },
    { admitted_authorities: [key] },
    { admitted_authorities: [key], larsa_required_weight: 0 },
    { admitted_authorities: [key], larsa_required_weight: -1 },
    { admitted_authorities: [key], larsa_required_weight: Number.NaN },
    { admitted_authorities: [key], larsa_required_weight: 1.5 },
    { admitted_authorities: [key], larsa_required_weight: "1" },
    { admitted_authorities: [key], larsa_required_weight: 2 ** 32 },
    { admitted_authorities: [key, key], larsa_required_weight: 1 },
    { admitted_authorities: [key.toUpperCase()], larsa_required_weight: 1 },
    { admitted_authorities: [key.slice(2)], larsa_required_weight: 1 },
    { admitted_authorities: [{ ed25519_public_key: key }], larsa_required_weight: 1 },
    { admitted_authorities: [null], larsa_required_weight: 1 },
    { admitted_authorities: Array.from({ length: MAX_ADMITTED_AUTHORITIES + 1 }, () => key), larsa_required_weight: 1 },
    { admitted_authorities: [key], larsa_required_weight: 1, enforceEd25519: false },
    { admitted_authorities: [key], larsa_required_weight: 1, previous_receipt: { receipt_hash: "0x00", seq_id: 1 } },
    { admitted_authorities: [key], larsa_required_weight: 1, previous_receipt: { receipt_hash: "0x" + "0".repeat(64), seq_id: -1 } },
    { admitted_authorities: [key], larsa_required_weight: 1, previous_receipt: null },
  ];
  for (const policy of bad) {
    const verdict = await verifyExecutionPayload(input, policy as TrustPolicy);
    expectRejected(verdict, ["TRUST_POLICY_INVALID"], JSON.stringify(policy)?.slice(0, 90));
  }
});

test("regresión: claves degeneradas y firmas triviales se rechazan aunque el runtime las acepte", async () => {
  const demo = await testAuthority();
  const identityKey = "0x01" + "00".repeat(31);
  const trivialSignature = "0x01" + "00".repeat(63);
  const degenerate = await sealed();
  degenerate.cryptographic_seal.ed25519_public_key = identityKey;
  degenerate.cryptographic_seal.ed25519_signature = trivialSignature;

  // 1. El runtime, por sí solo, da por buena esa pareja para cualquier mensaje.
  const key = await crypto.subtle.importKey("raw", new Uint8Array(32).fill(0, 1).fill(1, 0, 1), { name: "Ed25519" }, false, ["verify"]);
  const sig = new Uint8Array(64);
  sig[0] = 1;
  assert.equal(await crypto.subtle.verify({ name: "Ed25519" }, key, sig, new TextEncoder().encode("cualquier mensaje")), true);

  // 2. El verificador la rechaza por tres caminos independientes.
  expectRejected(await verifyExecutionPayload(degenerate, demo.policy), ["AUTHORITY_NOT_ADMITTED"]);
  expectRejected(await verifyExecutionPayload(degenerate, { admitted_authorities: [identityKey], larsa_required_weight: 4 }), ["TRUST_POLICY_INVALID"]);
  const trivialUnderAdmittedKey = await sealed();
  trivialUnderAdmittedKey.cryptographic_seal.ed25519_signature = trivialSignature;
  expectRejected(await verifyExecutionPayload(trivialUnderAdmittedKey, demo.policy), ["ED25519_SIGNATURE_INVALID"]);
});

test("regresión: el peso LARSA exigido lo fija el ancla; el recibo no puede rebajarlo", async () => {
  const demo = await testAuthority();
  const atThreshold = await sealed((u) => void (u.larsa_commit.heuristic_weight = 4));
  assert.equal((await verifyExecutionPayload(atThreshold, demo.policy)).ok, true);

  const below = await sealed((u) => void (u.larsa_commit.heuristic_weight = 3));
  expectRejected(await verifyExecutionPayload(below, demo.policy), ["QUORUM_INSUFFICIENT"]);
  expectRejected(await verifyExecutionPayload(await sealed(), { ...demo.policy, larsa_required_weight: 6 }), ["QUORUM_INSUFFICIENT"]);
  expectRejected(await verifyExecutionPayload(await sealed((u) => void (u.larsa_commit.heuristic_weight = 0)), demo.policy), ["QUORUM_INSUFFICIENT"]);

  // Un umbral declarado en el propio recibo ya no existe como campo.
  const selfDeclared = viaJson(below) as unknown as { cryptographic_seal: Record<string, unknown> };
  selfDeclared.cryptographic_seal["larsa_quorum_threshold"] = 1;
  expectRejected(await verifyExecutionPayload(selfDeclared, demo.policy), ["SCHEMA_INVALID"]);

  const overflow = await sealed();
  overflow.cryptographic_seal.larsa_commit.heuristic_weight = 2 ** 32;
  expectRejected(await verifyExecutionPayload(overflow, demo.policy), ["SCHEMA_INVALID"]);
});

test("varias autoridades admitidas: basta una firma válida de la que el recibo nombra", async () => {
  const demo = await testAuthority();
  const { authorities } = await testSigners();
  const [a, b, c] = authorities as [typeof demo.rogue, typeof demo.rogue, typeof demo.rogue];
  const policy: TrustPolicy = { admitted_authorities: [a.publicKey, b.publicKey], larsa_required_weight: 4 };

  const byB = await sealed(undefined, b);
  const ok = await verifyExecutionPayload(byB, policy);
  assert.ok(ok.ok, JSON.stringify(ok.failures));
  assert.equal(ok.receipt.signer, b.publicKey);

  expectRejected(await verifyExecutionPayload(await sealed(undefined, c), policy), ["AUTHORITY_NOT_ADMITTED"]);

  const misattributed = viaJson(byB);
  misattributed.cryptographic_seal.ed25519_public_key = a.publicKey;
  expectRejected(await verifyExecutionPayload(misattributed, policy), ["ED25519_SIGNATURE_INVALID"]);
});

test("regresión: la firma de un recibo no valida otro recibo", async () => {
  const demo = await testAuthority();
  const first = await sealed();
  const second = await sealed((u) => void (u.causal_clock.seq_id += 1));
  second.cryptographic_seal.ed25519_signature = first.cryptographic_seal.ed25519_signature;
  expectRejected(await verifyExecutionPayload(second, demo.policy), ["ED25519_SIGNATURE_INVALID"]);
});

test("refirmar tras alterar el sobre exige la clave de una autoridad admitida", async () => {
  const demo = await testAuthority();
  const tampered = await sealed();
  tampered.audit_metrics.memory_bytes += 1;
  expectRejected(await verifyExecutionPayload(tampered, demo.policy), ["ED25519_SIGNATURE_INVALID"]);
  assert.equal((await verifyExecutionPayload(viaJson(await signWire(tampered, demo.authority)), demo.policy)).ok, true);
  expectRejected(await verifyExecutionPayload(viaJson(await signWire(tampered, demo.rogue)), demo.policy), ["AUTHORITY_NOT_ADMITTED"]);
});

// ---- Forma del DAG y reglas de estado -----------------------------------------------------

test("DAG: duplicados, padres inexistentes o repetidos, autorreferencia y ciclos se rechazan con su código", async () => {
  const demo = await testAuthority();
  const cases: [string, (u: MutableUnsealed) => void, string[]][] = [
    ["id duplicado", (u) => void u.nodes.push({ ...u.nodes[3]! }), ["DAG_DUPLICATE_NODE_ID"]],
    ["padre inexistente", (u) => void (u.nodes[3]!.parent_ids = ["EV_00009999_000000"]), ["DAG_DANGLING_PARENT_REF"]],
    ["padre repetido", (u) => void (u.nodes[3]!.parent_ids = [N1, N1]), ["DAG_DUPLICATE_PARENT_REF"]],
    ["autorreferencia", (u) => void (u.nodes[3]!.parent_ids = [N3]), ["DAG_CYCLE_DETECTED"]],
    ["ciclo de dos", (u) => void (u.nodes[1]!.parent_ids = [N3]), ["DAG_CYCLE_DETECTED"]],
    ["ciclo sin raíz", (u) => void ((u.nodes[0]!.parent_ids = [N3]), (u.nodes[2]!.parent_ids = [N3])), ["DAG_CYCLE_DETECTED"]],
  ];
  for (const [label, mutate, expected] of cases) {
    expectRejected(await verifyExecutionPayload(await sealed(mutate), demo.policy), expected, label);
  }
});

test("reglas de estado: COMMITTED exige smt_verified; no se impone ninguna regla de cascada que el kernel no define", async () => {
  const demo = await testAuthority();
  expectRejected(await verifyExecutionPayload(await sealed((u) => void (u.nodes[1]!.smt_verified = false)), demo.policy), ["COMMITTED_WITHOUT_SMT"]);
  for (const status of ["REJECTED_POLICY", "INTERCEPTED_NEMESIS", "PENDING_SEAL"]) {
    const input = await sealed((u) => {
      u.nodes[1]!.state_status = status;
      u.nodes[1]!.smt_verified = false;
    });
    assert.equal((await verifyExecutionPayload(input, demo.policy)).ok, true, `${status} sin SMT es un estado declarable`);
  }
  // Un hijo COMMITTED bajo un nodo interceptado, firmado por una autoridad admitida, se muestra tal
  // como se atestó: el kernel no define propagación de resultados entre predecesores y sucesores.
  const childUnderIntercepted = await sealed((u) => {
    u.nodes.push({ node_id: "EV_00001049_000000", parent_ids: [N2], state_status: "COMMITTED", smt_verified: true, reduction_steps: 1, violation_reason: null });
  });
  assert.equal((await verifyExecutionPayload(childUnderIntercepted, demo.policy)).ok, true);
});

test("constancia Lean 4 declarada: solo VERIFIED_NO_SORRY con sorry_count 0", async () => {
  const demo = await testAuthority();
  expectRejected(await verifyExecutionPayload(await sealed((u) => void (u.lean4_proof.status = "FAILED_INVARIANT")), demo.policy), ["LEAN4_PROOF_INVALID"]);
  expectRejected(await verifyExecutionPayload(await sealed((u) => void (u.lean4_proof.sorry_count = 1)), demo.policy), ["LEAN4_PROOF_INVALID"]);
  expectRejected(await verifyExecutionPayload(await sealed((u) => void (u.lean4_proof.status = "UNVERIFIED")), demo.policy), ["SCHEMA_INVALID"]);
  for (const ident of ["", " ", "Thm with space", "Thm|x", "1abc", "a..b", "a.", "ñ"]) {
    expectRejected(await verifyExecutionPayload(await sealed((u) => void (u.lean4_proof.theorem_ident = ident)), demo.policy), ["SCHEMA_INVALID"], ident);
  }
});

// ---- Encadenamiento -----------------------------------------------------------------------

test("encadenamiento: con punto de control se verifica; sin él queda NO_VERIFICADO", async () => {
  const demo = await testAuthority();
  const first = await sealed();
  const firstHash = wireReceiptHash(first);
  const second = await sealed((u) => {
    u.causal_clock.seq_id = 4097;
    u.causal_clock.logical_tick = 1049;
    u.audit_metrics.prev_receipt_hash = firstHash;
  });
  const checkpoint = { receipt_hash: firstHash, seq_id: 4096 };

  const linked = await verifyExecutionPayload(second, { ...demo.policy, previous_receipt: checkpoint });
  assert.ok(linked.ok, JSON.stringify(linked.failures));
  assert.equal(linked.receipt.assurances.chain_link, "COINCIDE");

  const firstVerdict = await verifyExecutionPayload(first, demo.policy);
  assert.ok(firstVerdict.ok);
  assert.equal(firstVerdict.receipt.receipt_hash, firstHash);

  expectRejected(
    await verifyExecutionPayload(second, { ...demo.policy, previous_receipt: { receipt_hash: "0x" + "ab".repeat(32), seq_id: 4096 } }),
    ["CHAIN_LINK_MISMATCH"]
  );
  expectRejected(await verifyExecutionPayload(second, { ...demo.policy, previous_receipt: { receipt_hash: firstHash, seq_id: 4097 } }), ["CHAIN_LINK_MISMATCH"]);
  expectRejected(await verifyExecutionPayload(first, { ...demo.policy, previous_receipt: checkpoint }), ["CHAIN_LINK_MISMATCH"]);
});

// ---- Robustez -----------------------------------------------------------------------------

test("la promesa nunca se rechaza: cualquier entrada produce un veredicto negativo", async () => {
  const demo = await testAuthority();
  const cyclic: Record<string, unknown> = {};
  cyclic["self"] = cyclic;
  const throwingGetter = Object.defineProperty({}, "execution_id", {
    enumerable: true,
    get() {
      throw new Error("getter hostil");
    },
  });
  const hostileProxy = new Proxy(
    {},
    {
      ownKeys() {
        throw new Error("proxy hostil");
      },
    }
  );
  const inputs: unknown[] = [undefined, null, 0, 42, "texto", true, [], [[]], {}, () => 1, Symbol("s"), 10n, new Date(0), new Map(), cyclic, throwingGetter, hostileProxy, new Array(10_000_000)];
  for (const input of inputs) {
    const verdict = await verifyExecutionPayload(input, demo.policy);
    assert.equal(verdict.ok, false);
    assert.equal(verdict.receipt, null);
    assert.ok(verdict.failures.length >= 1 && verdict.failures.length <= LIMITS.MAX_REPORTED_FAILURES);
  }
});

test("una entrada con propiedades cambiantes se lee una sola vez", async () => {
  const demo = await testAuthority();
  const clean = await sealed();
  let reads = 0;
  const shifty = { ...clean } as Record<string, unknown>;
  Object.defineProperty(shifty, "execution_id", {
    enumerable: true,
    get() {
      reads++;
      return reads === 1 ? clean.execution_id : "otro-id";
    },
  });
  const verdict = await verifyExecutionPayload(shifty, demo.policy);
  assert.equal(reads, 1);
  assert.ok(verdict.ok, JSON.stringify(verdict.failures));
  assert.equal(verdict.receipt.payload.execution_id, clean.execution_id);
});

test("entrada como texto JSON: ilegible, enorme o con claves trampa produce rechazo, no excepción", async () => {
  const demo = await testAuthority();
  const good = JSON.stringify(await sealed());
  assert.equal((await verifyExecutionPayloadJson(good, demo.policy)).ok, true);
  expectRejected(await verifyExecutionPayloadJson("{", demo.policy), ["SCHEMA_INVALID"]);
  expectRejected(await verifyExecutionPayloadJson("", demo.policy), ["SCHEMA_INVALID"]);
  expectRejected(await verifyExecutionPayloadJson(" ".repeat(4 * 1024 * 1024 + 1), demo.policy), ["SCHEMA_INVALID"]);
  expectRejected(await verifyExecutionPayloadJson(undefined as unknown as string, demo.policy), ["SCHEMA_INVALID"]);
  expectRejected(await verifyExecutionPayloadJson(good.replace("{", '{"__proto__":{"ok":true},'), demo.policy), ["SCHEMA_INVALID"]);
  // Clave duplicada: JSON.parse conserva la última aparición; aquí es la alterada y rompe el manifiesto.
  const dup = good.replace('"execution_id":', '"execution_id":"primero","execution_id":"otro-id","ignored_before":');
  assert.ok(dup !== good);
  assert.equal((await verifyExecutionPayloadJson(dup, demo.policy)).ok, false);
});

test("runtime sin Ed25519 fiable: todo recibo se rechaza", async () => {
  const demo = await testAuthority();
  const input = await sealed();
  const real = crypto.subtle;
  const shims: [string, unknown][] = [
    ["sin WebCrypto", undefined],
    ["verify siempre true", { importKey: real.importKey.bind(real), verify: async () => true }],
    ["verify siempre false", { importKey: real.importKey.bind(real), verify: async () => false }],
    ["importKey falla", { importKey: async () => Promise.reject(new Error("NotSupportedError")), verify: real.verify.bind(real) }],
    ["verify lanza", { importKey: real.importKey.bind(real), verify: async () => Promise.reject(new Error("boom")) }],
    ["objeto vacío", {}],
  ];
  for (const [label, subtle] of shims) {
    const verify = createReceiptVerifier({ subtle: subtle as never });
    expectRejected(await verify(input, demo.policy), ["ED25519_UNSUPPORTED_RUNTIME"], label);
  }
  assert.equal((await createReceiptVerifier({ subtle: real as never })(input, demo.policy)).ok, true);
});

test("cotas: el trabajo por recibo está acotado y los excesos se rechazan antes de recorrerse", async () => {
  const demo = await testAuthority();
  const chain = (n: number, base: UnsealedReceipt): UnsealedReceipt => ({
    ...base,
    nodes: Array.from({ length: n }, (_, i) => ({
      node_id: `EV_00002000_${String(i).padStart(6, "0")}`,
      parent_ids: i === 0 ? [] : [`EV_00002000_${String(i - 1).padStart(6, "0")}`],
      state_status: "COMMITTED",
      smt_verified: true,
      reduction_steps: i,
      violation_reason: null,
    })),
  });
  const atLimit = viaJson(await sealReceipt(chain(LIMITS.MAX_DAG_NODES, unsealedOf(await sealed())), demo.authority));
  const started = performance.now();
  const ok = await verifyExecutionPayload(atLimit, demo.policy);
  const elapsed = performance.now() - started;
  assert.ok(ok.ok, JSON.stringify(ok.failures));
  assert.equal(ok.receipt.nodes.at(-1)!.depth, LIMITS.MAX_DAG_NODES - 1);
  assert.ok(elapsed < 20_000, `verificar ${LIMITS.MAX_DAG_NODES} nodos tardó ${elapsed.toFixed(0)} ms`);

  const over = viaJson(atLimit);
  over.execution_dag.push({ ...over.execution_dag[0]!, node_id: "EV_00003000_000000" });
  expectRejected(await verifyExecutionPayload(over, demo.policy), ["LIMIT_EXCEEDED"]);

  const manyParents = await sealed();
  manyParents.execution_dag[3]!.parent_ids = Array.from({ length: LIMITS.MAX_PARENTS_PER_NODE + 1 }, () => N0);
  expectRejected(await verifyExecutionPayload(manyParents, demo.policy), ["LIMIT_EXCEEDED"]);

  const longPayload = await sealed();
  longPayload.ingress.payload_raw = "x".repeat(LIMITS.MAX_PAYLOAD_RAW_LENGTH + 1);
  expectRejected(await verifyExecutionPayload(longPayload, demo.policy), ["LIMIT_EXCEEDED"]);

  const longReason = await sealed();
  longReason.execution_dag[2]!.violation_reason = "x".repeat(LIMITS.MAX_VIOLATION_REASON_LENGTH + 1);
  expectRejected(await verifyExecutionPayload(longReason, demo.policy), ["LIMIT_EXCEEDED"]);

  // Una avalancha de nodos inválidos no produce una lista de fallos sin tope, y el recorte se declara.
  const flood = await sealed();
  flood.execution_dag = Array.from({ length: LIMITS.MAX_DAG_NODES }, () => ({ bogus: true })) as never;
  const flooded = await verifyExecutionPayload(flood, demo.policy);
  assert.equal(flooded.ok, false);
  assert.equal(flooded.failures.length, LIMITS.MAX_REPORTED_FAILURES);
  assert.match(flooded.failures.at(-1)!.detail, /lista truncada en el tope de 64 fallos/);
});
