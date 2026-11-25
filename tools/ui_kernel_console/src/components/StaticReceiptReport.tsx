/**
 * Informe estático de un veredicto: el mismo visor e inspector, sin controles ni manejadores.
 * Pensado para `renderToStaticMarkup` en un servidor: el HTML resultante no necesita JavaScript y,
 * al no llevar estilos ni scripts en línea, sirve bajo `script-src 'self'; style-src 'self'`
 * enlazando `console.css`.
 */

import type { ReactElement } from "react";
import type { VerificationVerdict } from "../types/babylon60.ts";
import { DeterministicDagViewer } from "./DeterministicDagViewer.tsx";
import { TwoPhaseSealInspector } from "./TwoPhaseSealInspector.tsx";

export interface StaticReceiptReportProps {
  readonly verdict: VerificationVerdict;
  /** Texto que identifica el origen del recibo ante quien lee el informe. */
  readonly sourceLabel: string;
}

export function StaticReceiptReport({ verdict, sourceLabel }: StaticReceiptReportProps): ReactElement {
  return (
    <div className="b60-console">
      <header className="b60-console__header">
        <div>
          <h1 className="b60-title">BABYLON-60 // EXECUTION RECEIPT REPORT</h1>
          <div className="b60-subtitle">Origen del recibo: {sourceLabel}</div>
        </div>
      </header>
      <DeterministicDagViewer verdict={verdict} interactive={false} />
      <TwoPhaseSealInspector verdict={verdict} />
    </div>
  );
}
