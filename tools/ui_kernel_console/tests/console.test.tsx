import assert from "node:assert/strict";
import { test } from "node:test";
import TestRenderer, { act, type ReactTestRenderer } from "react-test-renderer";
import { BabylonKernelConsole } from "../src/components/BabylonKernelConsole.tsx";
import { INITIAL_CONSOLE_STATE, consoleReducer, verdictOf } from "../src/components/consoleState.ts";
import { rejectionVerdict, verifyExecutionPayload, type ReceiptVerifier } from "../src/crypto/sealVerifier.ts";
import { MODES } from "../src/demo/fixture.ts";
import type { VerificationVerdict } from "../src/types/babylon60.ts";
import { sealed, testAuthority } from "./helpers.ts";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const text = (r: ReactTestRenderer): string => JSON.stringify(r.toJSON());
const tick = (ms = 2): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

async function settle(r: ReactTestRenderer): Promise<void> {
  for (let i = 0; i < 2000; i++) {
    if (!text(r).includes("VERIFYING")) return;
    await act(async () => {
      await tick();
    });
  }
  assert.fail("la consola no llegó a un estado asentado");
}

function clickMode(r: ReactTestRenderer, label: string): void {
  const button = r.root.findAllByType("button").find((b) => b.children.join("") === label);
  assert.ok(button, `no existe el botón ${label}`);
  act(() => {
    (button.props as { onClick: () => void }).onClick();
  });
}

function mount(props: Parameters<typeof BabylonKernelConsole>[0] = {}): ReactTestRenderer {
  let renderer: ReactTestRenderer | undefined;
  act(() => {
    renderer = TestRenderer.create(<BabylonKernelConsole createAuthority={testAuthority} {...props} />);
  });
  assert.ok(renderer);
  return renderer;
}

test("máquina de estados: toda petición borra el veredicto anterior y los resultados obsoletos se ignoran", () => {
  const verdictA = rejectionVerdict("SCHEMA_INVALID", "a");
  const verdictB = rejectionVerdict("SCHEMA_INVALID", "b");
  let s = INITIAL_CONSOLE_STATE;
  assert.equal(verdictOf(s), null);
  s = consoleReducer(s, { type: "RESOLVE", requestId: 0, verdict: verdictA });
  assert.equal(verdictOf(s), verdictA);
  assert.equal(consoleReducer(s, { type: "RESOLVE", requestId: 0, verdict: verdictB }), s, "un estado asentado no se sobrescribe");

  s = consoleReducer(s, { type: "REQUEST", mode: "INJECT_DAG_CYCLE" });
  assert.deepEqual(s, { phase: "VERIFYING", requestId: 1, mode: "INJECT_DAG_CYCLE" });
  assert.equal(verdictOf(s), null, "el veredicto anterior desaparece en la misma transición");
  assert.equal(consoleReducer(s, { type: "RESOLVE", requestId: 0, verdict: verdictA }), s, "resultado de una petición anterior");
  assert.equal(consoleReducer(s, { type: "RESOLVE", requestId: 2, verdict: verdictA }), s, "resultado de una petición futura");
  s = consoleReducer(s, { type: "RESOLVE", requestId: 1, verdict: verdictB });
  assert.equal(verdictOf(s), verdictB);
});

test("consola: arranca sin mostrar nada verificado y cada modo acaba en los códigos que declara", async () => {
  const r = mount();
  assert.ok(text(r).includes("VERIFYING"));
  assert.ok(!text(r).includes("COINCIDEN") && !text(r).includes('"svg"'));
  await settle(r);
  assert.ok(text(r).includes("COMPROBACIONES LOCALES: COINCIDEN") && text(r).includes("COINCIDE CON LO ESPERADO") && !text(r).includes("NO COINCIDE"));
  assert.equal(r.root.findAllByType("button").length, MODES.length);

  for (const spec of MODES) {
    clickMode(r, spec.label);
    // Inmediatamente después del clic: modo nuevo resaltado y ningún veredicto anterior en pantalla.
    const pending = text(r);
    assert.ok(pending.includes("VERIFYING"), spec.mode);
    assert.ok(!pending.includes("COINCIDEN") && !pending.includes("RECHAZADO"), `${spec.mode}: veredicto obsoleto visible`);
    assert.equal(r.root.findAllByType("svg").length, 0, `${spec.mode}: grafo obsoleto visible`);
    const pressed = r.root.findAllByType("button").filter((b) => (b.props as { "aria-pressed": boolean })["aria-pressed"]);
    assert.deepEqual(pressed.map((b) => b.children.join("")), [spec.label]);

    await settle(r);
    const settled = text(r);
    assert.ok(settled.includes("COINCIDE CON LO ESPERADO") && !settled.includes("NO COINCIDE CON LO ESPERADO"), `${spec.mode}: ${settled.slice(0, 400)}`);
    if (spec.expected.length === 0) {
      assert.ok(settled.includes("COMPROBACIONES LOCALES: COINCIDEN"));
      assert.equal(r.root.findAllByType("svg").length, 1);
    } else {
      assert.ok(settled.includes("RECHAZADO") && settled.includes("[FAIL-CLOSED] GRAPH RENDERING HALTED"), spec.mode);
      assert.equal(r.root.findAllByType("svg").length, 0, spec.mode);
      for (const code of spec.expected) assert.ok(settled.includes(code), `${spec.mode}: falta ${code}`);
    }
  }
  act(() => r.unmount());
});

test("regresión: si la verificación lanza, la consola muestra un rechazo y nunca el veredicto anterior", async () => {
  let fail = false;
  const verify: ReceiptVerifier = async (input, policy) => {
    if (fail) throw new Error("fallo inyectado <b>x</b>");
    return verifyExecutionPayload(input, policy);
  };
  const r = mount({ verify });
  await settle(r);
  assert.ok(text(r).includes("COMPROBACIONES LOCALES: COINCIDEN"));

  fail = true;
  clickMode(r, "Inject Causal Cycle");
  assert.ok(!text(r).includes("COINCIDEN"));
  await settle(r);
  const after = text(r);
  assert.ok(after.includes("RECHAZADO") && after.includes("VERIFIER_INTERNAL_ERROR"));
  assert.ok(after.includes("NO COINCIDE CON LO ESPERADO"), "el resultado no es el que el escenario declara, y la consola lo dice");
  assert.ok(!after.includes("COINCIDEN"));
  assert.equal(r.root.findAllByType("svg").length, 0);

  fail = false;
  clickMode(r, "Valid Trace");
  await settle(r);
  assert.ok(text(r).includes("COMPROBACIONES LOCALES: COINCIDEN"));
  act(() => r.unmount());
});

test("regresión: un resultado tardío de una petición anterior no sustituye al de la petición vigente", async () => {
  const authority = await testAuthority();
  const okVerdict = await verifyExecutionPayload(await sealed(), authority.policy);
  assert.ok(okVerdict.ok);
  const pending: ((v: VerificationVerdict) => void)[] = [];
  const verify: ReceiptVerifier = () => new Promise<VerificationVerdict>((resolve) => void pending.push(resolve));

  const r = mount({ verify });
  for (let i = 0; i < 200 && pending.length < 1; i++) await act(async () => void (await tick()));
  assert.equal(pending.length, 1);

  clickMode(r, "Drop BFT Quorum");
  for (let i = 0; i < 200 && pending.length < 2; i++) await act(async () => void (await tick()));
  assert.equal(pending.length, 2);

  await act(async () => {
    pending[1]!(rejectionVerdict("VERIFIER_INTERNAL_ERROR", "veredicto de la petición vigente"));
    await tick();
  });
  assert.ok(text(r).includes("RECHAZADO"));
  await act(async () => {
    pending[0]!(okVerdict);
    await tick();
  });
  assert.ok(text(r).includes("RECHAZADO") && !text(r).includes("COINCIDEN"), "el resultado obsoleto no debe aparecer");
  assert.equal(r.root.findAllByType("svg").length, 0);
  act(() => r.unmount());
});

test("consola: sin ancla de confianza (runtime sin Ed25519) el resultado es un rechazo, y se reintenta al cambiar de modo", async () => {
  let attempts = 0;
  const createAuthority = async (): ReturnType<typeof testAuthority> => {
    attempts++;
    if (attempts === 1) throw new Error("Ed25519 no disponible");
    return testAuthority();
  };
  const r = mount({ createAuthority });
  await settle(r);
  assert.ok(text(r).includes("RECHAZADO") && text(r).includes("VERIFIER_INTERNAL_ERROR") && text(r).includes("Ed25519 no disponible"));
  assert.equal(r.root.findAllByType("svg").length, 0);
  clickMode(r, "Valid Trace");
  await settle(r);
  assert.ok(text(r).includes("COMPROBACIONES LOCALES: COINCIDEN"));
  assert.equal(attempts, 2);
  act(() => r.unmount());
});

test("consola: seleccionar un nodo con teclado muestra su detalle", async () => {
  const r = mount();
  await settle(r);
  const nodes = r.root.findAll((n) => n.type === "g" && (n.props as { role?: string }).role === "button");
  assert.equal(nodes.length, 4);
  const first = nodes[0]!;
  let prevented = false;
  act(() => {
    (first.props as { onKeyDown: (e: unknown) => void }).onKeyDown({ key: "Enter", preventDefault: () => void (prevented = true) });
  });
  assert.ok(prevented);
  assert.ok(text(r).includes("∅ (raíz)"), "el detalle del nodo raíz debe mostrarse");
  act(() => {
    (first.props as { onKeyDown: (e: unknown) => void }).onKeyDown({ key: "a", preventDefault: () => assert.fail("tecla ajena") });
  });
  act(() => r.unmount());
});
