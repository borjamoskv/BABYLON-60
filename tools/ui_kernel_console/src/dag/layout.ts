/**
 * Disposición determinista del DAG verificado: una columna por profundidad causal y, dentro de cada
 * columna, el orden topológico que entrega el verificador. Función pura: misma entrada, mismas
 * coordenadas; no mide texto, no usa reloj ni aleatoriedad.
 */

import { sortByUtf8 } from "../crypto/canonical.ts";
import type { ExecutionDagNode, LaidOutNode } from "../types/babylon60.ts";

export const NODE_WIDTH = 264;
export const NODE_HEIGHT = 68;
export const COL_GAP = 84;
export const ROW_GAP = 32;
export const PADDING = 36;

export interface NodeBox {
  readonly node: ExecutionDagNode;
  readonly depth: number;
  readonly x: number;
  readonly y: number;
}

export interface DagEdge {
  readonly key: string;
  readonly from: NodeBox;
  readonly to: NodeBox;
  /** La arista termina en un nodo detenido (rechazado o interceptado). */
  readonly halted: boolean;
}

export interface DagLayout {
  readonly boxes: readonly NodeBox[];
  readonly edges: readonly DagEdge[];
  readonly width: number;
  readonly height: number;
}

export function computeDagLayout(nodes: readonly LaidOutNode[]): DagLayout {
  const columns: LaidOutNode[][] = [];
  for (const entry of nodes) {
    (columns[entry.depth] ??= []).push(entry);
  }
  let maxRows = 1;
  for (const column of columns) {
    if (column !== undefined && column.length > maxRows) maxRows = column.length;
  }
  const columnCount = Math.max(columns.length, 1);
  const height = PADDING * 2 + maxRows * NODE_HEIGHT + (maxRows - 1) * ROW_GAP;
  const width = PADDING * 2 + columnCount * NODE_WIDTH + (columnCount - 1) * COL_GAP;

  const boxes: NodeBox[] = [];
  const byId = new Map<string, NodeBox>();
  for (let depth = 0; depth < columns.length; depth++) {
    const column = columns[depth];
    if (column === undefined) continue;
    const columnHeight = column.length * NODE_HEIGHT + (column.length - 1) * ROW_GAP;
    const startY = (height - columnHeight) / 2;
    const x = PADDING + depth * (NODE_WIDTH + COL_GAP);
    column.forEach((entry, row) => {
      const box: NodeBox = { node: entry.node, depth, x, y: startY + row * (NODE_HEIGHT + ROW_GAP) };
      boxes.push(box);
      byId.set(entry.node.node_id, box);
    });
  }

  const edges: DagEdge[] = [];
  for (const to of boxes) {
    const halted = to.node.state_status === "REJECTED_POLICY" || to.node.state_status === "INTERCEPTED_NEMESIS";
    for (const parentId of sortByUtf8(to.node.parent_ids)) {
      const from = byId.get(parentId);
      if (from === undefined) continue;
      edges.push({ key: `${parentId}->${to.node.node_id}`, from, to, halted });
    }
  }
  return { boxes, edges, width, height };
}

/** Curva de Bézier cúbica del borde derecho del padre al borde izquierdo del hijo. */
export function edgePath(edge: DagEdge): string {
  const x1 = edge.from.x + NODE_WIDTH;
  const y1 = edge.from.y + NODE_HEIGHT / 2;
  const x2 = edge.to.x;
  const y2 = edge.to.y + NODE_HEIGHT / 2;
  const cx = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`;
}
