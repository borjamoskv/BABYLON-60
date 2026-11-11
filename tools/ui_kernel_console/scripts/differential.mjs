#!/usr/bin/env node
// Arnés diferencial: el sellador y el verificador TypeScript frente al crate Rust
// (CLI `b60-exec-receipt` y binding wasm). Todo se genera con semillas fijas, así que cada
// ejecución es reproducible. No escribe fuera de scratch/ y sale con código 1 ante cualquier
// discrepancia entre implementaciones.
//
// Uso, desde tools/ui_kernel_console:
//   (cd rust && cargo build --locked --release)          # CLI
//   node scripts/differential.mjs [--cases 300] [--mutants 8] [--seed 2912] [--cli RUTA] [--wasm RUTA]
//
// Qué compara, para cada recibo base y cada alteración:
//   - el veredicto TypeScript sobre los bytes UTF-8 frente a la ruta de texto JSON (coherencia interna);
//   - frente a la CLI `batch` (mismo código que `verify`);
//   - frente al binding wasm;
//   - en una muestra, frente a `verify --policy` por entrada estándar (código de salida incluido).
// Y el sellado: el recibo que emite TypeScript con la semilla de prueba frente a `seal` del crate.

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PKG = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const STDIN_EVERY = 25;

function fail(code, message) {
  process.stderr.write(`${message}\n`);
  process.exit(code);
}

function parseArgs(argv) {
  const opts = { cases: 300, mutants: 8, seed: 2912, cli: null, wasm: null };
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    const value = () => {
      const v = argv[i + 1];
      if (v === undefined) fail(2, `falta el valor de ${flag}`);
      i += 1;
      return v;
    };
    if (flag === "--cases") opts.cases = Number(value());
    else if (flag === "--mutants") opts.mutants = Number(value());
    else if (flag === "--seed") opts.seed = Number(value());
    else if (flag === "--cli") opts.cli = resolve(value());
    else if (flag === "--wasm") opts.wasm = resolve(value());
    else fail(2, `argumento desconocido: ${flag}`);
  }
  if (!Number.isInteger(opts.cases) || opts.cases < 1) fail(2, "--cases debe ser un entero positivo");
  if (!Number.isInteger(opts.mutants) || opts.mutants < 0) fail(2, "--mutants debe ser un entero no negativo");
  if (!Number.isInteger(opts.seed)) fail(2, "--seed debe ser un entero");
  return opts;
}

const opts = parseArgs(process.argv.slice(2));
const CLI = opts.cli ?? resolve(PKG, "scratch/rust-target/release/b60-exec-receipt");
const WASM = opts.wasm ?? resolve(PKG, "scratch/wasm-pkg/babylon60_exec_receipt.js");
if (!existsSync(CLI)) fail(2, `falta la CLI en ${CLI}. Compílala con: (cd rust && cargo build --locked --release)`);
if (!existsSync(WASM)) fail(2, `falta el binding wasm en ${WASM}. Ver «Rust y WebAssembly» en el README.`);

// Compilación fresca: el arnés nunca compara con una salida de TypeScript anterior a los cambios.
{
  const tsc = resolve(PKG, "node_modules/.bin/tsc");
  if (!existsSync(tsc)) fail(2, "faltan dependencias: ejecuta `npm ci --ignore-scripts` en tools/ui_kernel_console");
  const build = spawnSync(tsc, ["-p", "tsconfig.test.json"], { cwd: PKG, encoding: "utf8" });
  if (build.status !== 0) fail(2, `la compilación TypeScript falla:\n${build.stdout}${build.stderr}`);
}
const load = (rel) => import(pathToFileURL(resolve(PKG, "scratch/test-build/src", rel)).href);
const { ed25519SignerFromSeed, sealReceipt } = await load("crypto/receiptSealer.js");
const { parseAnchorText, verifyExecutionPayloadJson, verifyExecutionPayloadWithAnchorText } = await load(
  "crypto/sealVerifier.js"
);
const verifyWithAnchorText = verifyExecutionPayloadWithAnchorText;
const wasm = createRequire(import.meta.url)(WASM);

// ---------------------------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------------------------

const TEXT = new TextEncoder();
const utf8 = (s) => TEXT.encode(s);
const concatBytes = (...parts) => {
  const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let offset = 0;
  for (const p of parts) {
    out.set(p, offset);
    offset += p.length;
  }
  return out;
};
const decodeStrict = (bytes) => {
  try {
    return new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
  } catch {
    return null;
  }
};

const depthOf = (v) => (v !== null && typeof v === "object" ? 1 + Math.max(0, ...Object.values(v).map(depthOf)) : 0);
const eqBytes = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);

function prng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rint = (rng, lo, hi) => lo + Math.floor(rng() * (hi - lo + 1));
const pick = (rng, xs) => xs[Math.floor(rng() * xs.length)];
const hexBytes = (rng, n) =>
  Array.from({ length: n }, () => rint(rng, 0, 255).toString(16).padStart(2, "0")).join("");
const hex32 = (rng) => `0x${hexBytes(rng, 32)}`;

const getAt = (root, path) => path.reduce((o, k) => o[k], root);
const holderOf = (root, path) => getAt(root, path.slice(0, -1));
const lastOf = (path) => path[path.length - 1];

function keyPaths(node, prefix = [], out = []) {
  if (Array.isArray(node)) {
    node.forEach((child, i) => keyPaths(child, [...prefix, i], out));
  } else if (node !== null && typeof node === "object") {
    for (const key of Object.keys(node)) {
      out.push([...prefix, key]);
      keyPaths(node[key], [...prefix, key], out);
    }
  }
  return out;
}

function collectObjects(node, out = []) {
  if (Array.isArray(node)) {
    node.forEach((child) => collectObjects(child, out));
  } else if (node !== null && typeof node === "object") {
    out.push(node);
    Object.values(node).forEach((child) => collectObjects(child, out));
  }
  return out;
}

function changeHexDigit(s, rng) {
  const digits = "0123456789abcdef";
  const positions = [];
  for (let i = Math.max(0, s.length - 16); i < s.length; i += 1) {
    if (digits.includes(s[i])) positions.push(i);
  }
  if (positions.length === 0) return `${s}0`;
  const at = pick(rng, positions);
  const next = digits[(digits.indexOf(s[at]) + rint(rng, 1, 15)) % 16];
  return s.slice(0, at) + next + s.slice(at + 1);
}

// Tokens numéricos del texto JSON que están fuera de cadenas.
function numberTokens(text) {
  const out = [];
  const numeric = /-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/y;
  let inString = false;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    if (inString) {
      if (c === "\\") i += 1;
      else if (c === '"') inString = false;
      continue;
    }
    if (c === '"') {
      inString = true;
      continue;
    }
    if (c === "-" || (c >= "0" && c <= "9")) {
      numeric.lastIndex = i;
      const m = numeric.exec(text);
      if (m) {
        if (/^-?\d+$/.test(m[0])) out.push({ start: i, end: i + m[0].length, token: m[0] });
        i += m[0].length - 1;
      }
    }
  }
  return out;
}

// Forma canónica para comparar objetos sin depender del orden de claves.
function canon(v) {
  if (Array.isArray(v)) return `[${v.map(canon).join(",")}]`;
  if (v !== null && typeof v === "object") {
    return `{${Object.keys(v)
      .sort()
      .map((k) => `${JSON.stringify(k)}:${canon(v[k])}`)
      .join(",")}}`;
  }
  return JSON.stringify(v);
}

// ---------------------------------------------------------------------------------------------
// Normalización de veredictos: TypeScript, JSON de la CLI y wasm, con la misma forma.
// ---------------------------------------------------------------------------------------------

const uniqueSorted = (xs) => [...new Set(xs)].sort();

function fromTs(v) {
  if (!v.ok) return { ok: false, codes: uniqueSorted(v.failures.map((f) => f.code)) };
  const r = v.receipt;
  return {
    ok: true,
    codes: [],
    receipt_hash: r.receipt_hash,
    signer: r.signer,
    larsa_required_weight: r.larsa_required_weight,
    chain_link: r.assurances.chain_link,
    nodes: r.nodes.map((n) => ({ node_id: n.node.node_id, depth: n.depth })),
  };
}

function fromRust(v) {
  if (v.error !== undefined) return { error: v.error };
  if (!v.ok) return { ok: false, codes: uniqueSorted(v.failures.map((f) => f.code)) };
  return {
    ok: true,
    codes: [],
    receipt_hash: v.receipt_hash,
    signer: v.signer,
    larsa_required_weight: v.larsa_required_weight,
    chain_link: v.chain_link,
    nodes: v.nodes.map((n) => ({ node_id: n.node_id, depth: n.depth })),
  };
}

// ---------------------------------------------------------------------------------------------
// Generación de recibos base (sellados por TypeScript)
// ---------------------------------------------------------------------------------------------

function randomUnsealed(rng, k) {
  const tick = rint(rng, 0, 2_000_000);
  const count = rint(rng, 1, 9);
  const nodes = [];
  for (let i = 0; i < count; i += 1) {
    const committed = rng() < 0.75;
    const parent_ids = [];
    for (let j = 0; j < i && parent_ids.length < 3; j += 1) {
      if (rng() < 0.4) parent_ids.push(nodes[j].node_id);
    }
    nodes.push({
      node_id: `EV_${String(tick).padStart(8, "0")}_${String(i).padStart(6, "0")}`,
      parent_ids,
      state_status: committed ? "COMMITTED" : pick(rng, ["REJECTED_POLICY", "INTERCEPTED_NEMESIS"]),
      smt_verified: committed ? rng() < 0.97 : rng() < 0.5,
      reduction_steps: rint(rng, 0, 500),
      violation_reason: committed
        ? null
        : `INV_C5_${pick(rng, ["FLASH_DEFENSE", "SEAL_GAP"])}: ${pick(rng, ["Side-Effect Without Pre-Seal", "rebote ñandú 😀"])}`,
    });
  }
  const status = rng() < 0.9 ? "VERIFIED_NO_SORRY" : "FAILED_INVARIANT";
  return {
    execution_id: `b60-exec-${hexBytes(rng, 6)}-${k}`,
    causal_clock: { policy_epoch: rint(rng, 0, 999), logical_tick: tick, seq_id: rint(rng, 0, 100_000) },
    manifest_version: `v${rint(rng, 0, 9)}.${rint(rng, 0, 20)}.${rint(rng, 0, 50)}`,
    ingress: {
      agent_id: `agent://cortex/rea-${rint(rng, 0, 99)}`,
      policy_profile: pick(rng, ["STRICT_DETERMINISTIC", "BFT_DEFENSIVE", "NEMESIS_ADVERSARIAL"]),
      payload_raw: pick(rng, [`{"op":"fs.write","target":"/etc/hosts","n":${rint(rng, 0, 9)}}`, '{"nota":"ñandú 😀"}', "{}"]),
    },
    nodes,
    larsa_commit: { trace_hash: hex32(rng), heuristic_weight: rint(rng, 1, 9) },
    lean4_proof: {
      status,
      theorem_ident: `Babylon.Exec.t${rint(rng, 0, 99)}`,
      sorry_count: status === "VERIFIED_NO_SORRY" && rng() < 0.05 ? 1 : 0,
    },
    audit_metrics: { memory_bytes: rint(rng, 0, 2 ** 31), prev_receipt_hash: hex32(rng), worm_txid: hex32(rng) },
  };
}

// Semillas de prueba (no secretas): la 0x11 es la raíz admitida y la 0x22 una autoridad ajena.
const SEED_ADMITTED = "11".repeat(32);
const SEED_OTHER = "22".repeat(32);
const signerAdmitted = await ed25519SignerFromSeed(SEED_ADMITTED);
const signerOther = await ed25519SignerFromSeed(SEED_OTHER);

async function makeBase(k) {
  const rng = prng((opts.seed * 1_000_003 + k) >>> 0);
  const u = randomUnsealed(rng, k);
  const other = rng() < 0.1;
  const wire = await sealReceipt(u, other ? signerOther : signerAdmitted);
  const policy = {
    admitted_authorities: [signerAdmitted.publicKey],
    larsa_required_weight: rng() < 0.7 ? rint(rng, 1, u.larsa_commit.heuristic_weight) : rint(rng, 1, 12),
  };
  const chain = rng();
  if (chain < 0.2) {
    policy.previous_receipt = {
      receipt_hash: u.audit_metrics.prev_receipt_hash,
      seq_id: Math.max(0, u.causal_clock.seq_id - 1),
    };
  } else if (chain < 0.25) {
    policy.previous_receipt = { receipt_hash: hex32(rng), seq_id: rint(rng, 0, 100_000) };
  }
  return { k, rng, u, wire, text: JSON.stringify(wire), policy, seedHex: other ? SEED_OTHER : SEED_ADMITTED };
}

// ---------------------------------------------------------------------------------------------
// Alteraciones. Cada una devuelve null si no es aplicable, o { text | bytes, policy? }.
// ---------------------------------------------------------------------------------------------

// Ancla de la base con otro valor de peso (texto, para probar escrituras numéricas distintas).
const withWeight = (b, token) =>
  JSON.stringify(b.policy).replace(/"larsa_required_weight":\d+/, `"larsa_required_weight":${token}`);

const HEX_FIELDS = [
  ["cryptographic_seal", "phase_one_manifest_hash"],
  ["cryptographic_seal", "phase_two_merkle_root"],
  ["cryptographic_seal", "ed25519_public_key"],
  ["cryptographic_seal", "ed25519_signature"],
  ["cryptographic_seal", "larsa_commit", "trace_hash"],
  ["audit_metrics", "prev_receipt_hash"],
  ["audit_metrics", "worm_txid"],
];
const INT_FIELDS = [
  ["causal_clock", "policy_epoch"],
  ["causal_clock", "logical_tick"],
  ["causal_clock", "seq_id"],
  ["audit_metrics", "memory_bytes"],
  ["cryptographic_seal", "larsa_commit", "heuristic_weight"],
  ["cryptographic_seal", "lean4_proof", "sorry_count"],
];
const STRING_FIELDS = [
  ["execution_id"],
  ["manifest_version"],
  ["ingress", "agent_id"],
  ["ingress", "policy_profile"],
  ["cryptographic_seal", "lean4_proof", "theorem_ident"],
];

const MUTATIONS = {
  hex_digit: (rng, b) => {
    const w = structuredClone(b.wire);
    const nodeHash = ["execution_dag", rint(rng, 0, w.execution_dag.length - 1), "state_hash"];
    const path = pick(rng, [...HEX_FIELDS, nodeHash]);
    holderOf(w, path)[lastOf(path)] = changeHexDigit(getAt(w, path), rng);
    return { text: JSON.stringify(w) };
  },
  int_step: (rng, b) => {
    const w = structuredClone(b.wire);
    const reduction = ["execution_dag", rint(rng, 0, w.execution_dag.length - 1), "reduction_steps"];
    const path = pick(rng, [...INT_FIELDS, reduction]);
    holderOf(w, path)[lastOf(path)] += rng() < 0.5 ? 1 : -1;
    return { text: JSON.stringify(w) };
  },
  int_limit: (rng, b) => {
    const w = structuredClone(b.wire);
    const path = pick(rng, INT_FIELDS);
    holderOf(w, path)[lastOf(path)] = pick(rng, [2 ** 53, 2 ** 53 - 1]);
    return { text: JSON.stringify(w) };
  },
  string_field: (rng, b) => {
    const w = structuredClone(b.wire);
    const path = pick(rng, STRING_FIELDS);
    holderOf(w, path)[lastOf(path)] += pick(rng, ["x", "!", " ", "é"]);
    return { text: JSON.stringify(w) };
  },
  enum_field: (rng, b) => {
    const w = structuredClone(b.wire);
    const edits = [
      () => {
        w.cryptographic_seal.lean4_proof.status = pick(rng, ["VERIFIED_WITH_SORRY", "verified_no_sorry", "PENDING_SEAL"]);
      },
      () => {
        w.ingress.policy_profile = pick(rng, ["UNKNOWN_PROFILE", "strict_deterministic"]);
      },
      () => {
        pick(rng, w.execution_dag).state_status = pick(rng, ["UNKNOWN_STATUS", "committed"]);
      },
    ];
    pick(rng, edits)();
    return { text: JSON.stringify(w) };
  },
  drop_key: (rng, b) => {
    const w = structuredClone(b.wire);
    const path = pick(rng, keyPaths(w));
    delete holderOf(w, path)[lastOf(path)];
    return { text: JSON.stringify(w) };
  },
  extra_key: (rng, b) => {
    const w = structuredClone(b.wire);
    pick(rng, collectObjects(w)).x_extra = rint(rng, 0, 9);
    return { text: JSON.stringify(w) };
  },
  type_swap: (rng, b) => {
    const w = structuredClone(b.wire);
    const path = pick(rng, keyPaths(w));
    const holder = holderOf(w, path);
    const key = lastOf(path);
    const v = holder[key];
    holder[key] =
      typeof v === "number" ? String(v) : typeof v === "string" ? 0 : typeof v === "boolean" ? "true" : null;
    return { text: JSON.stringify(w) };
  },
  swap_nodes: (rng, b) => {
    const w = structuredClone(b.wire);
    const dag = w.execution_dag;
    if (dag.length < 2) return null;
    const i = rint(rng, 0, dag.length - 2);
    [dag[i], dag[i + 1]] = [dag[i + 1], dag[i]];
    return { text: JSON.stringify(w) };
  },
  parent_edit: (rng, b) => {
    const w = structuredClone(b.wire);
    const node = pick(rng, w.execution_dag);
    node.parent_ids = pick(rng, [
      ["EV_00000000_000000"],
      [node.node_id],
      [...node.parent_ids, ...node.parent_ids],
    ]);
    return { text: JSON.stringify(w) };
  },
  dup_node: (rng, b) => {
    const w = structuredClone(b.wire);
    w.execution_dag.push(structuredClone(pick(rng, w.execution_dag)));
    return { text: JSON.stringify(w) };
  },
  empty_dag: (_rng, b) => {
    const w = structuredClone(b.wire);
    w.execution_dag = [];
    return { text: JSON.stringify(w) };
  },
  signer_swap: (_rng, b) => {
    const w = structuredClone(b.wire);
    w.cryptographic_seal.ed25519_public_key = signerOther.publicKey;
    return { text: JSON.stringify(w) };
  },
  signature_zero: (_rng, b) => {
    const w = structuredClone(b.wire);
    w.cryptographic_seal.ed25519_signature = `0x${"00".repeat(64)}`;
    return { text: JSON.stringify(w) };
  },
  signature_digit: (rng, b) => {
    const w = structuredClone(b.wire);
    w.cryptographic_seal.ed25519_signature = changeHexDigit(w.cryptographic_seal.ed25519_signature, rng);
    return { text: JSON.stringify(w) };
  },
  small_order_key: (rng, b) => {
    const identity = `0x01${"00".repeat(31)}`;
    const w = structuredClone(b.wire);
    w.cryptographic_seal.ed25519_public_key = identity;
    const admit = rng() < 0.5;
    return {
      text: JSON.stringify(w),
      policy: admit ? { ...b.policy, admitted_authorities: [identity] } : b.policy,
    };
  },
  policy_weight: (rng, b) => ({
    text: b.text,
    policy: {
      ...b.policy,
      larsa_required_weight: pick(rng, [0, 4_294_967_296, b.wire.cryptographic_seal.larsa_commit.heuristic_weight + 1]),
    },
  }),
  policy_authorities: (rng, b) => ({
    text: b.text,
    policy: {
      ...b.policy,
      admitted_authorities: pick(rng, [
        [signerAdmitted.publicKey.toUpperCase()],
        [signerAdmitted.publicKey.slice(0, -2)],
        [],
        [signerAdmitted.publicKey, signerAdmitted.publicKey],
      ]),
    },
  }),
  policy_extra: (_rng, b) => ({ text: b.text, policy: { ...b.policy, comment: "auditoría" } }),
  policy_chain: (_rng, b) => ({
    text: b.text,
    policy: {
      ...b.policy,
      previous_receipt: { receipt_hash: `0x${"ab".repeat(32)}`, seq_id: b.wire.causal_clock.seq_id },
    },
  }),
  text_float: (rng, b) => numericEdit(rng, b, (t) => `${t}.0`),
  text_exponent: (rng, b) => numericEdit(rng, b, (t) => `${t}e0`),
  text_negzero: (rng, b) => numericEdit(rng, b, () => "-0"),
  text_bigint: (rng, b) => numericEdit(rng, b, () => "9007199254740993"),
  text_bom: (_rng, b) => ({ bytes: concatBytes(Uint8Array.of(0xef, 0xbb, 0xbf), utf8(b.text)) }),
  text_control: (_rng, b) => ({ text: b.text.replace('"execution_id":"', '"execution_id":"\u0001') }),
  text_lone_high: (_rng, b) => ({ text: b.text.replace('"execution_id":"', '"execution_id":"\\ud800') }),
  text_lone_low: (_rng, b) => ({ text: b.text.replace('"execution_id":"', '"execution_id":"\\udc00') }),
  text_pair: (_rng, b) => ({ text: b.text.replace('"payload_raw":"', '"payload_raw":"\\ud83d\\ude00') }),
  text_deep: (_rng, b) => ({ text: b.text.replace(/^\{/, `{"deep":${"[".repeat(126)}${"]".repeat(126)},`) }),
  text_dup_key: (_rng, b) => ({ text: b.text.replace(/\}$/, ',"execution_id":"b60-exec-dup"}') }),
  text_escape_key: (_rng, b) => ({ text: b.text.replace('"execution_id"', '"\\u0065xecution_id"') }),
  text_whitespace: (_rng, b) => ({ text: JSON.stringify(JSON.parse(b.text), null, 2) }),
  text_truncate: (rng, b) => ({
    text: b.text.slice(0, rint(rng, Math.floor(b.text.length / 2), b.text.length - 1)),
  }),
  text_trailing: (rng, b) => ({ text: b.text + pick(rng, [" x", "\n1", "}"]) }),
  bytes_invalid_utf8: (rng, b) => {
    const bytes = utf8(b.text);
    const at = rint(rng, 0, bytes.length - 1);
    return { bytes: concatBytes(bytes.slice(0, at), Uint8Array.of(0xff), bytes.slice(at)) };
  },
  bytes_overlong: (_rng, b) => ({ bytes: concatBytes(Uint8Array.of(0xc0, 0x80), utf8(b.text)) }),
  // Ancla como texto: escrituras numéricas, claves, sustitutos, BOM, profundidad y truncamientos.
  anchor_weight_forms: (rng, b) => {
    const w = b.policy.larsa_required_weight;
    return { anchor: withWeight(b, pick(rng, [`${w}.0`, `${w}e0`, `${w}E+0`, `${w}.000`])) };
  },
  anchor_weight_bad: (rng, b) => {
    const w = b.policy.larsa_required_weight;
    return { anchor: withWeight(b, pick(rng, [`${w}.5`, "0", "0.0", `-${w}`, "4294967296", "9007199254740993", "1e400", `${w}e400`])) };
  },
  anchor_seq_forms: (rng, b) => {
    const seq = pick(rng, ["0.0", "0e0", "-0.0", "0.5", "-1", "1e400", "1"]);
    const text = JSON.stringify({
      admitted_authorities: b.policy.admitted_authorities,
      larsa_required_weight: b.policy.larsa_required_weight,
      previous_receipt: { receipt_hash: `0x${"ab".repeat(32)}`, seq_id: 0 },
    });
    return { anchor: text.replace('"seq_id":0', `"seq_id":${seq}`) };
  },
  anchor_dup_key: (_rng, b) => ({ anchor: JSON.stringify(b.policy).replace(/}$/, ',"larsa_required_weight":1}') }),
  anchor_lone_surrogate: (_rng, b) => ({
    anchor: JSON.stringify(b.policy).replace('"admitted_authorities":["', '"admitted_authorities":["\\ud800'),
  }),
  anchor_bom: (_rng, b) => ({ anchor: `\uFEFF${JSON.stringify(b.policy)}` }),
  anchor_truncate: (rng, b) => {
    const text = JSON.stringify(b.policy);
    return { anchor: text.slice(0, rint(rng, 1, text.length - 1)) };
  },
  anchor_deep: (_rng, b) => ({
    anchor: JSON.stringify(b.policy).replace(/}$/, `,"x":${"[".repeat(126)}${"]".repeat(126)}}`),
  }),
  anchor_pretty: (_rng, b) => ({ anchor: JSON.stringify(b.policy, null, 2) }),
  anchor_escape_key: (_rng, b) => ({ anchor: JSON.stringify(b.policy).replace('"larsa_required_weight"', '"\\u006carsa_required_weight"') }),
};

function numericEdit(rng, b, replace) {
  const tokens = numberTokens(b.text);
  if (tokens.length === 0) return null;
  const t = pick(rng, tokens);
  return { text: b.text.slice(0, t.start) + replace(t.token) + b.text.slice(t.end) };
}

const MUTATION_NAMES = Object.keys(MUTATIONS);

function mutate(rng, b) {
  for (let attempt = 0; attempt < 8; attempt += 1) {
    const cls = pick(rng, MUTATION_NAMES);
    const r = MUTATIONS[cls](rng, b);
    if (r) return { cls, ...r };
  }
  return null;
}

function casesOf(b) {
  const baseAnchor = JSON.stringify(b.policy);
  const baseBytes = utf8(b.text);
  const out = [{ cls: "base", bytes: baseBytes, anchorText: baseAnchor }];
  for (let m = 0; m < opts.mutants; m += 1) {
    const r = mutate(b.rng, b);
    if (!r) continue;
    const bytes = r.bytes ?? utf8(r.text ?? b.text);
    const anchorText = r.anchor ?? (r.policy !== undefined ? JSON.stringify(r.policy) : baseAnchor);
    // Una alteración que no cambia nada no cuenta como alteración aceptada: se descarta.
    if (eqBytes(bytes, baseBytes) && anchorText === baseAnchor) continue;
    out.push({ cls: r.cls, bytes, anchorText });
  }
  return out.map((c, index) => ({ ...c, base: b.k, index }));
}

// ---------------------------------------------------------------------------------------------
// Ejecución
// ---------------------------------------------------------------------------------------------

function runBatch(lines) {
  const r = spawnSync(CLI, ["batch"], { input: `${lines.join("\n")}\n`, encoding: "utf8", maxBuffer: 1 << 30 });
  if (r.status !== 0) fail(2, `la CLI batch termina con ${r.status}:\n${r.stderr}`);
  return r.stdout
    .split("\n")
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line));
}

const seals = [];
const cases = [];
for (let k = 0; k < opts.cases; k += 1) {
  const b = await makeBase(k);
  seals.push(b);
  cases.push(...casesOf(b));
}
cases.forEach((c, id) => {
  c.id = id;
});

cases.push({
  id: cases.length,
  base: -1,
  index: 0,
  cls: "oversize_anchor",
  bytes: utf8(JSON.stringify(seals[0].u)),
  anchorText: "x".repeat(1024 * 1024 + 1),
});
cases.push({
  id: cases.length,
  base: -1,
  index: 0,
  cls: "oversize_bytes",
  bytes: new Uint8Array(13 * 1024 * 1024).fill(0x20),
  anchorText: JSON.stringify(seals[0].policy),
});
for (const c of cases) {
  c.ts = fromTs(await verifyWithAnchorText(c.bytes, c.anchorText));
  const anchor = parseAnchorText(c.anchorText);
  const text = decodeStrict(c.bytes);
  c.tsObj = anchor.ok && text !== null ? fromTs(await verifyExecutionPayloadJson(text, anchor.policy)) : null;
}

const verifyReplies = runBatch(
  cases.map((c, i) => {
    const anchor = parseAnchorText(c.anchorText);
    // Un tercio de las peticiones lleva el ancla como objeto; el resto, como texto.
    // El sobre de batch añade un nivel de anidamiento: un ancla de 127 niveles solo va como texto.
    const fits = anchor.ok && depthOf(anchor.policy) <= 126;
    const policy = i % 3 === 0 && fits ? anchor.policy : c.anchorText;
    return JSON.stringify({ op: "verify", receipt_hex: Buffer.from(c.bytes).toString("hex"), policy });
  })
);
if (verifyReplies.length !== cases.length) {
  fail(2, `la CLI devolvió ${verifyReplies.length} respuestas para ${cases.length} peticiones`);
}
cases.forEach((c, i) => {
  c.rust = fromRust(verifyReplies[i]);
});

for (const c of cases) {
  c.wasm = fromRust(JSON.parse(wasm.verifyReceiptBytes(c.bytes, c.anchorText)));
}

for (let i = 0; i < cases.length; i += 1) {
  const c = cases[i];
  if (i % STDIN_EVERY !== 0 && c.cls !== "oversize_bytes") continue;
  // El SO no admite un argumento de más de 128 KiB: el ancla sobredimensionada no pasa por la CLI.
  if (c.cls === "oversize_anchor") continue;
  const r = spawnSync(CLI, ["verify", "--policy", c.anchorText], {
    input: c.bytes,
    maxBuffer: 1 << 26,
  });
  c.cli = r.status === (c.ts.ok ? 0 : 1) ? fromRust(JSON.parse(r.stdout.toString("utf8"))) : { exit: r.status };
}

const sealReplies = runBatch(
  seals.map((b) => JSON.stringify({ op: "seal", unsealed: b.u, test_seed_hex: b.seedHex }))
);
const sealMismatches = [];
seals.forEach((b, i) => {
  const reply = sealReplies[i];
  if (reply.receipt === undefined || canon(reply.receipt) !== canon(b.wire)) {
    sealMismatches.push({ base: b.k, reply: reply.error ?? "recibo distinto" });
  }
});

// ---------------------------------------------------------------------------------------------
// Resultados
// ---------------------------------------------------------------------------------------------

const same = (a, b) => canon(a) === canon(b);
function diffsOf(c) {
  const d = [];
  if (c.tsObj !== null && !same(c.tsObj, c.ts)) d.push("ts-objeto≠ts-texto-del-ancla");
  if (!same(c.rust, c.ts)) d.push("rust-batch≠ts");
  if (!same(c.wasm, c.ts)) d.push("wasm≠ts");
  if (c.cli !== undefined && !same(c.cli, c.ts)) d.push("rust-cli-stdin≠ts");
  return d;
}

const byClass = new Map();
const codes = new Map();
const examples = [];
let verifyMismatches = 0;
for (const c of cases) {
  const d = diffsOf(c);
  const s = byClass.get(c.cls) ?? { n: 0, accepted: 0, rejected: 0, mismatches: 0 };
  s.n += 1;
  if (c.ts.ok) s.accepted += 1;
  else s.rejected += 1;
  if (d.length > 0) {
    s.mismatches += 1;
    verifyMismatches += 1;
    if (examples.length < 5) {
      examples.push({ case: c.id, base: c.base, cls: c.cls, diffs: d, ts: c.ts, rust: c.rust, wasm: c.wasm });
    }
  }
  byClass.set(c.cls, s);
  for (const code of c.ts.codes ?? []) codes.set(code, (codes.get(code) ?? 0) + 1);
}

const accepted = cases.filter((c) => c.ts.ok).length;
const stdinSample = cases.filter((c) => c.cli !== undefined).length;
const total = sealMismatches.length + verifyMismatches;

console.log(`RESULT seal cases=${seals.length} mismatches=${sealMismatches.length}`);
console.log(
  `RESULT verify cases=${cases.length} accepted=${accepted} rejected=${cases.length - accepted} ` +
    `mismatches=${verifyMismatches} (ts-json, rust-batch, wasm; cli-stdin sample=${stdinSample})`
);
for (const [cls, s] of [...byClass].sort()) {
  console.log(`CLASS ${cls} n=${s.n} accepted=${s.accepted} rejected=${s.rejected} mismatches=${s.mismatches}`);
}
console.log(`CODES ${[...codes].sort().map(([k, v]) => `${k}=${v}`).join(" ")}`);
for (const ex of examples) console.log(`MISMATCH ${JSON.stringify(ex)}`);
for (const m of sealMismatches.slice(0, 5)) console.log(`SEAL-MISMATCH ${JSON.stringify(m)}`);
console.log(`RESULT overall ${total === 0 ? "PASS" : `FAIL mismatches=${total}`}`);
process.exit(total === 0 ? 0 : 1);
