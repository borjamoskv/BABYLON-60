/**
 * Consola de demostración: construye la traza sintética en el escenario elegido, la pasa por el
 * verificador real y muestra el resultado junto a los códigos de fallo que el escenario debía
 * producir.
 *
 * No hay camino sin firma: el ancla de confianza es una clave efímera generada en este runtime y
 * toda traza se comprueba contra ella. Si el runtime no ofrece Ed25519, la consola lo muestra como
 * rechazo, no como traza válida. Los botones solo eligen escenario; la consola no ofrece ningún
 * control de aprobación.
 */

import { useEffect, useReducer, useRef, useState, type ReactElement } from "react";
import { rejectionVerdict, verifyExecutionPayload, type ReceiptVerifier } from "../crypto/sealVerifier.ts";
import { MODES, buildFixture, createDemoAuthority, type AdversarialMode, type DemoAuthority, type ModeSpec } from "../demo/fixture.ts";
import type { VerificationVerdict } from "../types/babylon60.ts";
import { DeterministicDagViewer } from "./DeterministicDagViewer.tsx";
import { TwoPhaseSealInspector } from "./TwoPhaseSealInspector.tsx";
import { INITIAL_CONSOLE_STATE, consoleReducer, verdictOf } from "./consoleState.ts";

export interface BabylonKernelConsoleProps {
  /** Fábrica del ancla de confianza de la demostración (por defecto, claves efímeras). */
  readonly createAuthority?: () => Promise<DemoAuthority>;
  /** Verificador a usar (por defecto, el del módulo). Existe para pruebas de la propia consola. */
  readonly verify?: ReceiptVerifier;
}

const DEFAULT_SELECTED_NODE = "EV_00001048_000002";
const ALL_MATCH = "∅ (todas las comprobaciones locales coinciden)";

function specOf(mode: AdversarialMode): ModeSpec {
  const spec = MODES.find((m) => m.mode === mode);
  if (spec === undefined) throw new Error(`escenario desconocido: ${mode}`);
  return spec;
}

function observedCodes(verdict: VerificationVerdict): string[] {
  return [...new Set(verdict.failures.map((f) => f.code))].sort();
}

function sameCodes(a: readonly string[], b: readonly string[]): boolean {
  return a.length === b.length && a.every((code, i) => code === b[i]);
}

export function BabylonKernelConsole({ createAuthority = createDemoAuthority, verify = verifyExecutionPayload }: BabylonKernelConsoleProps): ReactElement {
  const [state, dispatch] = useReducer(consoleReducer, INITIAL_CONSOLE_STATE);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(DEFAULT_SELECTED_NODE);
  const authorityRef = useRef<Promise<DemoAuthority> | null>(null);

  const { requestId, mode } = state;
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      let verdict: VerificationVerdict;
      try {
        authorityRef.current ??= createAuthority();
        const authority = await authorityRef.current;
        const input = await buildFixture(mode, authority);
        verdict = await verify(input, authority.policy);
      } catch (error) {
        authorityRef.current = null;
        verdict = rejectionVerdict(
          "VERIFIER_INTERNAL_ERROR",
          `la consola no pudo preparar o comprobar la traza: ${error instanceof Error ? error.message : "error desconocido"}`
        );
      }
      if (!cancelled) dispatch({ type: "RESOLVE", requestId, verdict });
    })();
    return () => {
      cancelled = true;
    };
  }, [requestId, mode, createAuthority, verify]);

  const verdict = verdictOf(state);
  const spec = specOf(mode);
  const expected = [...spec.expected].sort();
  const observed = verdict === null ? null : observedCodes(verdict);
  const matches = observed !== null && sameCodes(observed, expected);

  return (
    <div className="b60-console">
      <header className="b60-console__header">
        <div>
          <h1 className="b60-title">BABYLON-60 // KERNEL EXECUTION CONSOLE</h1>
          <div className="b60-subtitle">
            Client-side BLAKE3 Merkle v1 + Kahn topological gate + COSE_Sign1 Ed25519 against a pinned authority
          </div>
        </div>
        <div role="note" className="b60-note">
          DEMO · traza sintética (no procede de una ejecución del kernel) · ancla de confianza efímera generada en este
          runtime: muestra el mecanismo de comprobación, no la autenticidad de un emisor real.
        </div>
        <div role="group" aria-label="Escenario adversarial" className="b60-modes">
          {MODES.map((m) => (
            <button
              key={m.mode}
              type="button"
              aria-pressed={m.mode === mode}
              className="b60-mode"
              onClick={() => dispatch({ type: "REQUEST", mode: m.mode })}
            >
              {m.label}
            </button>
          ))}
        </div>
      </header>

      <section aria-label="Escenario y resultado" aria-live="polite" className="b60-scenario">
        <div>
          <strong>1. SCENARIO:</strong> {spec.label} · <strong>ADVERSARY:</strong> {spec.adversary}
        </div>
        <div className="b60-muted">{spec.description}</div>
        <div>
          <strong>EXPECTED:</strong> {expected.length === 0 ? ALL_MATCH : expected.join(", ")}
        </div>
        <div>
          <strong>OBSERVED:</strong>{" "}
          {observed === null ? (
            <span className="b60-muted">comprobando…</span>
          ) : (
            <span className={matches ? "b60-ok" : "b60-danger"}>
              {observed.length === 0 ? ALL_MATCH : observed.join(", ")} · {matches ? "COINCIDE CON LO ESPERADO" : "NO COINCIDE CON LO ESPERADO"}
            </span>
          )}
        </div>
      </section>

      <DeterministicDagViewer verdict={verdict} selectedNodeId={selectedNodeId} onSelectNode={setSelectedNodeId} />
      <TwoPhaseSealInspector verdict={verdict} />
    </div>
  );
}
