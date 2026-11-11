/**
 * Máquina de estados de la consola. Dos reglas la hacen fail-closed frente a carreras:
 *  - toda petición nueva borra el veredicto anterior en la misma transición, de modo que nunca se
 *    pinta un veredicto viejo bajo un modo nuevo;
 *  - un resultado solo se acepta si corresponde a la petición vigente.
 */

import type { AdversarialMode } from "../demo/fixture.ts";
import type { VerificationVerdict } from "../types/babylon60.ts";

export type ConsoleState =
  | { readonly phase: "VERIFYING"; readonly requestId: number; readonly mode: AdversarialMode }
  | { readonly phase: "SETTLED"; readonly requestId: number; readonly mode: AdversarialMode; readonly verdict: VerificationVerdict };

export type ConsoleAction =
  | { readonly type: "REQUEST"; readonly mode: AdversarialMode }
  | { readonly type: "RESOLVE"; readonly requestId: number; readonly verdict: VerificationVerdict };

export const INITIAL_CONSOLE_STATE: ConsoleState = Object.freeze({ phase: "VERIFYING", requestId: 0, mode: "CLEAN_TRACE" });

export function consoleReducer(state: ConsoleState, action: ConsoleAction): ConsoleState {
  switch (action.type) {
    case "REQUEST":
      return { phase: "VERIFYING", requestId: state.requestId + 1, mode: action.mode };
    case "RESOLVE":
      if (state.phase !== "VERIFYING" || action.requestId !== state.requestId) return state;
      return { phase: "SETTLED", requestId: state.requestId, mode: state.mode, verdict: action.verdict };
  }
}

/** Veredicto a mostrar: `null` (pendiente) salvo que el estado esté asentado. */
export function verdictOf(state: ConsoleState): VerificationVerdict | null {
  return state.phase === "SETTLED" ? state.verdict : null;
}
