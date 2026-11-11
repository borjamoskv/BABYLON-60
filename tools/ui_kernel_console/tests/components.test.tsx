import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import ReactDOMServer from "react-dom/server";
import { DeterministicDagViewer } from "../src/components/DeterministicDagViewer.tsx";
import { StaticReceiptReport } from "../src/components/StaticReceiptReport.tsx";
import { TwoPhaseSealInspector } from "../src/components/TwoPhaseSealInspector.tsx";
import { shortHash, visibleText } from "../src/components/visibleText.ts";
import { wireReceiptHash } from "../src/crypto/receiptSealer.ts";
import { verifyExecutionPayload } from "../src/crypto/sealVerifier.ts";
import { NODE_HEIGHT, NODE_WIDTH, computeDagLayout, edgePath } from "../src/dag/layout.ts";
import { MODES, buildFixture } from "../src/demo/fixture.ts";
import type { VerificationVerdict } from "../src/types/babylon60.ts";
import { N0, N1, N2, N3, sealed, testAuthority } from "./helpers.ts";

const noop = (): void => {};
const html = (element: React.ReactElement): string => ReactDOMServer.renderToStaticMarkup(element);
const count = (text: string, needle: string): number => text.split(needle).length - 1;

async function cleanVerdict(): Promise<Extract<VerificationVerdict, { ok: true }>> {
  const authority = await testAuthority();
  const verdict = await verifyExecutionPayload(await sealed(), authority.policy);
  assert.ok(verdict.ok, JSON.stringify(verdict.failures));
  return verdict;
}

/** Ejecuta `fn` y devuelve lo que React haya escrito por console.error (avisos de claves, props, etc.). */
function capturingReactWarnings<T>(fn: () => T): { result: T; warnings: string[] } {
  const original = console.error;
  const warnings: string[] = [];
  console.error = (...args: unknown[]): void => void warnings.push(args.map(String).join(" "));
  try {
    return { result: fn(), warnings };
  } finally {
    console.error = original;
  }
}

test("visor: un recibo verificado se dibuja con todos sus nodos y aristas, accesible por teclado", async () => {
  const verdict = await cleanVerdict();
  const { result: markup, warnings } = capturingReactWarnings(() =>
    html(<DeterministicDagViewer verdict={verdict} selectedNodeId={N2} onSelectNode={noop} />)
  );
  assert.deepEqual(warnings, []);
  assert.equal(count(markup, "<svg"), 1);
  assert.ok(markup.includes("ACÍCLICO (Kahn) · HOJAS RECALCULADAS: COINCIDEN"));
  assert.ok(markup.includes("(4 NODES, 3 EDGES)"));
  for (const id of [N0, N1, N2, N3]) assert.ok(markup.includes(`>${id}</text>`), id);
  assert.equal(count(markup, 'role="button"'), 4);
  assert.equal(count(markup, 'tabindex="0"'), 4);
  assert.equal(count(markup, 'aria-pressed="true"'), 1);
  assert.equal(count(markup, 'aria-pressed="false"'), 3);
  assert.equal(count(markup, "marker-end="), 3);
  assert.equal(count(markup, 'stroke-dasharray="5 4"'), 1, "solo la arista hacia el nodo interceptado va punteada");
  assert.ok(markup.includes("INV_C5_FLASH_DEFENSE: Side-Effect Without Pre-Seal"));
  assert.ok(markup.includes("NEMESIS_TRAP") && markup.includes("COMMITTED"));
  assert.ok(!markup.includes("FAIL-CLOSED"));
});

test("visor: con cualquier veredicto negativo no se emite ni un nodo del recibo", async () => {
  const demo = await testAuthority();
  for (const spec of MODES) {
    if (spec.expected.length === 0) continue;
    const verdict = await verifyExecutionPayload(await buildFixture(spec.mode, demo), demo.policy);
    assert.equal(verdict.ok, false, spec.mode);
    const markup = html(<DeterministicDagViewer verdict={verdict} selectedNodeId={N2} onSelectNode={noop} />);
    assert.ok(!markup.includes("<svg"), spec.mode);
    assert.ok(!markup.includes('role="button"'), spec.mode);
    assert.ok(markup.includes("[FAIL-CLOSED] GRAPH RENDERING HALTED"), spec.mode);
    assert.ok(markup.includes('role="alert"'), spec.mode);
    for (const code of spec.expected) assert.ok(markup.includes(`${code}:`), `${spec.mode}: falta ${code}`);
    assert.ok(!markup.includes("COINCIDEN") && !markup.includes("[COINCIDE]"), spec.mode);
  }
});

test("regresión: un veredicto positivo fabricado a mano no dibuja nada", async () => {
  const real = await cleanVerdict();
  const tamperedCopy = structuredClone(real.receipt) as unknown as { payload: { execution_dag: { state_status: string; violation_reason: string | null }[] } };
  tamperedCopy.payload.execution_dag[2]!.state_status = "COMMITTED";
  tamperedCopy.payload.execution_dag[2]!.violation_reason = null;
  const forgeries: unknown[] = [
    { ok: true, receipt: tamperedCopy, failures: [] },
    { ok: true, receipt: structuredClone(real.receipt), failures: [] },
    { ok: true, receipt: { ...real.receipt }, failures: [] },
    { ok: true, receipt: null, failures: [] },
    { ok: true, receipt: { payload: real.receipt.payload, nodes: real.receipt.nodes }, failures: [] },
  ];
  for (const forged of forgeries) {
    const viewer = html(<DeterministicDagViewer verdict={forged as VerificationVerdict} selectedNodeId={null} onSelectNode={noop} />);
    assert.ok(!viewer.includes("<svg") && !viewer.includes('role="button"'));
    assert.ok(viewer.includes("UNVERIFIED_INPUT:"));
    const inspector = html(<TwoPhaseSealInspector verdict={forged as VerificationVerdict} />);
    assert.ok(inspector.includes("RECHAZADO") && inspector.includes("UNVERIFIED_INPUT"));
    assert.ok(!inspector.includes("COINCIDEN") && !inspector.includes("[COINCIDE]"));
  }
});

test("regresión: el visor no admite nodos sueltos junto a un veredicto (no hay forma de desparejarlos)", async () => {
  const verdict = await cleanVerdict();
  const props = { verdict, selectedNodeId: null, onSelectNode: noop, nodes: [] };
  // @ts-expect-error — `nodes` no forma parte de las props: los nodos solo llegan dentro del recibo verificado.
  const element = <DeterministicDagViewer verdict={verdict} selectedNodeId={null} onSelectNode={noop} nodes={[]} />;
  assert.ok(html(element).includes("<svg"));
  assert.equal(Object.keys(props).length, 4);
});

test("verificación pendiente: ni grafo ni sello verificado", () => {
  const viewer = html(<DeterministicDagViewer verdict={null} selectedNodeId={N2} onSelectNode={noop} />);
  assert.ok(viewer.includes("VERIFYING") && viewer.includes('aria-busy="true"'));
  assert.ok(!viewer.includes("<svg") && !viewer.includes("FAIL-CLOSED"));
  const inspector = html(<TwoPhaseSealInspector verdict={null} />);
  assert.ok(inspector.includes("VERIFYING") && !inspector.includes("COINCIDE") && !inspector.includes("RECHAZADO"));
});

test("inspector: cada fila dice qué se comparó y con qué resultado; no hay sello global de verificado", async () => {
  const demo = await testAuthority();
  const verdict = await cleanVerdict();
  const markup = html(<TwoPhaseSealInspector verdict={verdict} />);
  assert.ok(markup.includes("COMPROBACIONES LOCALES: COINCIDEN"));
  assert.ok(markup.includes(verdict.receipt.payload.cryptographic_seal.phase_two_merkle_root));
  assert.ok(markup.includes(verdict.receipt.receipt_hash));
  assert.ok(markup.includes("peso heurístico declarado 5 ≥ exigido por el ancla 4"));
  assert.ok(markup.includes(`comprobada contra la autoridad admitida ${shortHash(demo.authority.publicKey, 10, 6)}`));
  assert.equal(count(markup, "[DECLARADO]"), 3, "LARSA, Lean 4 y auditoría WORM son declaraciones del emisor");
  assert.equal(count(markup, "[NO_VERIFICADO]"), 1, "sin punto de control, el encadenamiento no se comprueba");
  assert.equal(count(markup, "[COINCIDE]"), 8);
  // La fila de Lean 4 nunca aparece como comprobada por el cliente.
  const leanRow = markup.slice(markup.indexOf("LEAN4_PROOF"), markup.indexOf("L0_PREV_RECEIPT_HASH"));
  assert.ok(leanRow.includes("estado declarado VERIFIED_NO_SORRY") && leanRow.includes("[DECLARADO]") && !leanRow.includes("[COINCIDE]"));
  // Límite explícito junto a la firma, y ningún sello global.
  assert.ok(markup.includes("Una firma válida no establece quién controla la clave"));
  for (const seal of ["SEAL_VERIFIED", "VERIFICADO FORMALMENTE", ">VERIFIED<", ">VERIFICADO<"]) assert.ok(!markup.includes(seal), seal);

  const first = await sealed();
  const second = await sealed((u) => {
    u.causal_clock.seq_id = 4097;
    u.audit_metrics.prev_receipt_hash = wireReceiptHash(first);
  });
  const linked = await verifyExecutionPayload(second, { ...demo.policy, previous_receipt: { receipt_hash: wireReceiptHash(first), seq_id: 4096 } });
  assert.ok(linked.ok);
  assert.equal(count(html(<TwoPhaseSealInspector verdict={linked} />), "[NO_VERIFICADO]"), 0);
});

test("inspector: un rechazo muestra códigos y cotejo forense rotulado como no confiable", async () => {
  const demo = await testAuthority();
  const verdict = await verifyExecutionPayload(await buildFixture("TAMPER_NODE_FIELD", demo), demo.policy);
  assert.equal(verdict.ok, false);
  const markup = html(<TwoPhaseSealInspector verdict={verdict} />);
  assert.ok(markup.includes("RECHAZADO"));
  assert.ok(markup.includes("LEAF_HASH_MISMATCH, MERKLE_ROOT_MISMATCH"));
  assert.ok(markup.includes("DECLARED_MERKLE_ROOT") && markup.includes("CLIENT_RECOMPUTED_ROOT") && markup.includes("— NO COINCIDE"));
  assert.ok(markup.includes("entrada no confiable"));
  assert.ok(!markup.includes("[COINCIDE]") && !markup.includes("COINCIDEN"));
});

test("texto no confiable firmado: se escapa como HTML y los caracteres invisibles se hacen visibles", async () => {
  const authority = await testAuthority();
  const hostile = '<script>alert(1)</script>\u202egnp.exe\u200b"><img src=x onerror=alert(2)>';
  const input = await sealed((u) => {
    u.nodes[2]!.violation_reason = hostile;
    u.ingress.payload_raw = `</code><script>x</script>\u0000\u202e`;
  });
  const verdict = await verifyExecutionPayload(input, authority.policy);
  assert.ok(verdict.ok, JSON.stringify(verdict.failures));
  const markup = html(<DeterministicDagViewer verdict={verdict} selectedNodeId={N2} onSelectNode={noop} />) + html(<TwoPhaseSealInspector verdict={verdict} />);
  assert.ok(!markup.includes("<script>") && !markup.includes("<img"));
  assert.ok(markup.includes("&lt;script&gt;alert(1)&lt;/script&gt;\\u{202E}gnp.exe\\u{200B}"));
  assert.ok(markup.includes("\\u{0}\\u{202E}"));
  assert.ok(!/[\u0000\u200b\u202e]/.test(markup));
});

test("dos visores en la misma página no comparten identificadores SVG", async () => {
  const verdict = await cleanVerdict();
  const { result: markup, warnings } = capturingReactWarnings(() =>
    html(
      <div>
        <DeterministicDagViewer verdict={verdict} selectedNodeId={null} onSelectNode={noop} />
        <DeterministicDagViewer verdict={verdict} selectedNodeId={null} onSelectNode={noop} />
      </div>
    )
  );
  assert.deepEqual(warnings, []);
  const ids = [...markup.matchAll(/ id="([^"]+)"/g)].map((m) => m[1]!);
  assert.equal(ids.length, 6);
  assert.equal(new Set(ids).size, 6);
  for (const id of ids) assert.match(id, /^dag-[A-Za-z0-9_-]+-(ok|halt|clip)$/);
});

test("disposición: coordenadas deterministas por profundidad y orden topológico", async () => {
  const verdict = await cleanVerdict();
  const layout = computeDagLayout(verdict.receipt.nodes);
  assert.equal(layout.width, 36 * 2 + 3 * NODE_WIDTH + 2 * 84);
  assert.equal(layout.height, 36 * 2 + 2 * NODE_HEIGHT + 32);
  assert.deepEqual(
    layout.boxes.map((b) => [b.node.node_id, b.depth, b.x, b.y]),
    [
      [N0, 0, 36, 86],
      [N1, 1, 384, 36],
      [N2, 1, 384, 136],
      [N3, 2, 732, 86],
    ]
  );
  assert.deepEqual(layout.edges.map((e) => [e.key, e.halted]), [[`${N0}->${N1}`, false], [`${N0}->${N2}`, true], [`${N1}->${N3}`, false]]);
  assert.equal(edgePath(layout.edges[0]!), "M 300 120 C 342 120, 342 70, 384 70");
  assert.deepEqual(computeDagLayout(verdict.receipt.nodes), layout);
});

test("identificadores de longitud máxima: el contenido del nodo queda recortado al rectángulo", async () => {
  const authority = await testAuthority();
  const longest = "EV_18446744073709551615_4294967295";
  const input = await sealed((u) => {
    u.nodes.push({ node_id: longest, parent_ids: [N3], state_status: "COMMITTED", smt_verified: true, reduction_steps: Number.MAX_SAFE_INTEGER, violation_reason: null });
  });
  const verdict = await verifyExecutionPayload(input, authority.policy);
  assert.ok(verdict.ok, JSON.stringify(verdict.failures));
  const markup = html(<DeterministicDagViewer verdict={verdict} selectedNodeId={null} onSelectNode={noop} />);
  assert.ok(markup.includes(longest));
  assert.equal(count(markup, 'clip-path="url(#dag-'), 5);
});

test("visibleText y shortHash", () => {
  assert.equal(visibleText("abc"), "abc");
  assert.equal(visibleText("a\u0000b\u202ec\u200bd\ufeffe\u00adf"), "a\\u{0}b\\u{202E}c\\u{200B}d\\u{FEFF}e\\u{AD}f");
  assert.equal(visibleText("ñ€😀"), "ñ€😀");
  assert.equal(visibleText("\ud800x"), "\\u{D800}x");
  assert.equal(visibleText("😀😀😀😀", 2), "😀😀… (+4)");
  assert.equal(visibleText("abcdef", 3), "abc… (+3)");
  assert.equal(shortHash("0x" + "ab".repeat(32), 10, 6), "0xabababab…ababab");
  assert.equal(shortHash("0x1234"), "0x1234");
});

/** Clases definidas en la hoja de estilos del paquete. */
function definedClasses(): Set<string> {
  const css = readFileSync(path.join(process.cwd(), "src", "components", "console.css"), "utf8");
  return new Set([...css.matchAll(/\.(b60-[A-Za-z0-9_-]+)/g)].map((m) => m[1]!));
}

function usedClasses(markup: string): Set<string> {
  const out = new Set<string>();
  for (const m of markup.matchAll(/ class="([^"]*)"/g)) for (const c of m[1]!.split(/\s+/)) if (c !== "") out.add(c);
  return out;
}

test("marcado servible sin JavaScript y bajo CSP estricta: sin estilos en línea, sin scripts, sin manejadores, sin recursos externos", async () => {
  const demo = await testAuthority();
  const accepted = await cleanVerdict();
  const rejected = await verifyExecutionPayload(await buildFixture("INJECT_DAG_CYCLE", demo), demo.policy);
  const css = definedClasses();
  const pages = [
    html(<StaticReceiptReport verdict={accepted} sourceLabel="fixture de pruebas" />),
    html(<StaticReceiptReport verdict={rejected} sourceLabel="fixture de pruebas" />),
    html(<DeterministicDagViewer verdict={accepted} selectedNodeId={N2} onSelectNode={noop} />),
    html(<DeterministicDagViewer verdict={null} />),
    html(<TwoPhaseSealInspector verdict={null} />),
  ];
  for (const markup of pages) {
    assert.ok(!/ style=/.test(markup), "atributo style en línea");
    assert.ok(!/<script|<style|<link|<iframe|<img|<object/i.test(markup), "elemento activo o recurso");
    assert.ok(!/ on[a-z]+=/i.test(markup), "manejador de eventos en línea");
    assert.ok(!/(?:href|src)=|url\((?!#)/i.test(markup), "referencia externa");
    for (const c of usedClasses(markup)) assert.ok(css.has(c), `clase sin definir en console.css: ${c}`);
  }
});

test("informe estático: sin controles; cada nodo aparece en la tabla con su detalle completo", async () => {
  const accepted = await cleanVerdict();
  const markup = html(<StaticReceiptReport verdict={accepted} sourceLabel="fixture <b>de</b> pruebas" />);
  assert.ok(!markup.includes('role="button"') && !markup.includes("tabindex") && !markup.includes("<button"));
  assert.equal(count(markup, 'role="img"'), 4);
  assert.equal(count(markup, "<tr>"), 5, "cabecera + 4 nodos");
  for (const entry of accepted.receipt.nodes) {
    assert.ok(markup.includes(`<th scope="row">${entry.node.node_id}</th>`));
    assert.ok(markup.includes(`<td>${entry.node.state_hash}</td>`));
  }
  assert.ok(markup.includes("Origen del recibo: fixture &lt;b&gt;de&lt;/b&gt; pruebas"));
  assert.ok(markup.includes("INV_C5_FLASH_DEFENSE: Side-Effect Without Pre-Seal"));
});

test("la hoja de estilos no carga nada externo y usa solo fuentes del sistema", () => {
  const css = readFileSync(path.join(process.cwd(), "src", "components", "console.css"), "utf8");
  assert.ok(!/@import|@font-face|url\(|https?:/i.test(css));
  assert.ok(css.includes("ui-monospace"));
});
