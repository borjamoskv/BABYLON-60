/**
 * Atributos de presentación del SVG y clases de estado. El SVG se colorea con atributos (`fill`,
 * `stroke`), no con estilos en línea; el resto de la interfaz usa las clases de `console.css`.
 * Cada estado se expresa además con texto: el color nunca es el único portador de significado.
 */

import type { AssuranceLevel, NodeStateStatus } from "../types/babylon60.ts";

export const SVG_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace";

export const SVG_COLOR = Object.freeze({
  nodeFill: "#0F0F0F",
  nodeFillSelected: "#171717",
  text: "#F5F5F5",
  textMuted: "#A3A3A3",
  focus: "#F5F5F5",
  edge: "#737373",
  edgeHalted: "#EF4444",
});

export const STATUS_PALETTE: Readonly<Record<NodeStateStatus, { readonly stroke: string; readonly badgeFill: string; readonly label: string }>> =
  Object.freeze({
    COMMITTED: { stroke: "#34D399", badgeFill: "#0E2A20", label: "COMMITTED" },
    REJECTED_POLICY: { stroke: "#F87171", badgeFill: "#2E1416", label: "POLICY_REJECT" },
    INTERCEPTED_NEMESIS: { stroke: "#FB7185", badgeFill: "#33151B", label: "NEMESIS_TRAP" },
    PENDING_SEAL: { stroke: "#FBBF24", badgeFill: "#2E2410", label: "PENDING_SEAL" },
  });

export const STATE_CLASS: Readonly<Record<AssuranceLevel, string>> = Object.freeze({
  COINCIDE: "b60-state b60-state--coincide",
  DECLARADO: "b60-state b60-state--declarado",
  NO_VERIFICADO: "b60-state b60-state--no-verificado",
});
