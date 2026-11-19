/**
 * Visor SVG del DAG de ejecución.
 *
 * Fail-closed por construcción: el componente no recibe nodos sueltos, solo un veredicto. Dibuja el
 * grafo únicamente si el veredicto es positivo y su recibo figura en el registro del verificador
 * (`isAcceptedReceipt`); en cualquier otro caso (comprobación pendiente, veredicto negativo u objeto
 * con forma de veredicto construido a mano) muestra el panel de cuarentena y ningún nodo.
 *
 * Con `interactive = false` el marcado es estático (sin controles ni manejadores) e incluye una
 * tabla con el detalle de todos los nodos: es la salida de referencia para servir sin JavaScript.
 */

import { useId, useMemo, useState, type KeyboardEvent, type ReactElement } from "react";
import { isAcceptedReceipt } from "../crypto/sealVerifier.ts";
import { NODE_HEIGHT, NODE_WIDTH, computeDagLayout, edgePath, type DagLayout, type NodeBox } from "../dag/layout.ts";
import type { ExecutionDagNode, SealFailure, VerificationVerdict } from "../types/babylon60.ts";
import { STATUS_PALETTE, SVG_COLOR, SVG_FONT } from "./theme.ts";
import { shortHash, visibleText } from "./visibleText.ts";

export interface DeterministicDagViewerProps {
  /** `null` mientras la comprobación está en curso. */
  readonly verdict: VerificationVerdict | null;
  readonly selectedNodeId?: string | null;
  readonly onSelectNode?: (nodeId: string) => void;
  /** `false` produce marcado estático con tabla de nodos. Por defecto, interactivo. */
  readonly interactive?: boolean;
}

const UNVERIFIED_INPUT: readonly SealFailure[] = Object.freeze([
  Object.freeze({
    code: "UNVERIFIED_INPUT",
    detail: "el veredicto recibido no procede del verificador; no se dibuja ningún dato",
  } as const),
]);

function QuarantinePanel({ failures }: { readonly failures: readonly SealFailure[] }): ReactElement {
  return (
    <section aria-label="DAG de ejecución en cuarentena" role="alert" className="b60-quarantine">
      <div className="b60-quarantine__title">
        <span>[FAIL-CLOSED] GRAPH RENDERING HALTED</span>
        <span>INV_SEAL_QUARANTINE</span>
      </div>
      <p className="b60-quarantine__lead">
        El cliente ha bloqueado la proyección del DAG: el recibo no superó las comprobaciones locales. No se muestra
        ningún nodo del recibo recibido.
      </p>
      <ul className="b60-failures">
        {failures.map((f, idx) => (
          <li key={idx} className="b60-failure">
            <strong className="b60-danger">{f.code}:</strong> {visibleText(f.detail, 600)}
          </li>
        ))}
      </ul>
    </section>
  );
}

function nodeAriaLabel(node: ExecutionDagNode, depth: number): string {
  const parts = [
    `Nodo ${node.node_id}`,
    `estado ${STATUS_PALETTE[node.state_status].label}`,
    `SMT ${node.smt_verified ? "sí" : "no"}`,
    `${node.reduction_steps} pasos de reducción`,
    `profundidad ${depth}`,
    `${node.parent_ids.length} padre(s)`,
  ];
  if (node.violation_reason !== null) parts.push("con violación registrada");
  return parts.join(", ");
}

function parentsText(node: ExecutionDagNode): string {
  return node.parent_ids.length === 0 ? "∅ (raíz)" : node.parent_ids.join(", ");
}

function NodeDetail({ box }: { readonly box: NodeBox }): ReactElement {
  const { node } = box;
  return (
    <footer aria-live="polite" className="b60-node-detail">
      <div>
        <strong>NODE:</strong> {node.node_id} | <strong>STATUS:</strong> {node.state_status} | <strong>DEPTH:</strong> {box.depth}
      </div>
      <div>
        <strong>PARENTS:</strong> {parentsText(node)}
      </div>
      <div>
        <strong>LEAF_HASH (recalculado = declarado):</strong> {node.state_hash}
      </div>
      {node.violation_reason !== null && (
        <div className="b60-danger">
          <strong>INVARIANT_VIOLATION:</strong> {visibleText(node.violation_reason)}
        </div>
      )}
    </footer>
  );
}

function NodeTable({ layout }: { readonly layout: DagLayout }): ReactElement {
  return (
    <div className="b60-node-table">
      <table>
        <caption className="b60-muted">Nodos en orden topológico (cada state_hash recalculado coincide con el declarado)</caption>
        <thead>
          <tr>
            <th scope="col">node_id</th>
            <th scope="col">estado</th>
            <th scope="col">SMT</th>
            <th scope="col">pasos</th>
            <th scope="col">padres</th>
            <th scope="col">state_hash</th>
            <th scope="col">violation_reason</th>
          </tr>
        </thead>
        <tbody>
          {layout.boxes.map(({ node }) => (
            <tr key={node.node_id}>
              <th scope="row">{node.node_id}</th>
              <td>{node.state_status}</td>
              <td>{node.smt_verified ? "sí" : "no"}</td>
              <td>{node.reduction_steps}</td>
              <td>{parentsText(node)}</td>
              <td>{node.state_hash}</td>
              <td>{node.violation_reason === null ? "—" : visibleText(node.violation_reason)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DeterministicDagViewer({
  verdict,
  selectedNodeId = null,
  onSelectNode,
  interactive = true,
}: DeterministicDagViewerProps): ReactElement {
  const markerPrefix = `dag-${useId().replace(/[^A-Za-z0-9_-]/g, "")}`;
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);

  const receipt = verdict !== null && verdict.ok && isAcceptedReceipt(verdict.receipt) ? verdict.receipt : null;
  const layout = useMemo(() => (receipt === null ? null : computeDagLayout(receipt.nodes)), [receipt]);

  if (verdict === null) {
    return (
      <section aria-label="DAG de ejecución pendiente de comprobación" aria-busy="true" className="b60-pending">
        <strong className="b60-strong">VERIFYING…</strong>
        <p className="b60-pending__lead">No se muestra ningún dato del recibo hasta que terminen las comprobaciones locales.</p>
      </section>
    );
  }
  if (receipt === null || layout === null) {
    return <QuarantinePanel failures={verdict.ok ? UNVERIFIED_INPUT : verdict.failures} />;
  }

  const selected: NodeBox | null = interactive ? (layout.boxes.find((b) => b.node.node_id === selectedNodeId) ?? null) : null;
  const clipId = `${markerPrefix}-clip`;
  const select = (nodeId: string): void => onSelectNode?.(nodeId);
  const onNodeKeyDown = (event: KeyboardEvent<SVGGElement>, nodeId: string): void => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      select(nodeId);
    }
  };

  return (
    <section aria-label="DAG de ejecución comprobado" className="b60-panel">
      <header className="b60-panel__header">
        <span>
          2. DETERMINISTIC EXECUTION DAG ({layout.boxes.length} NODES, {layout.edges.length} EDGES)
        </span>
        <span className="b60-ok">ACÍCLICO (Kahn) · HOJAS RECALCULADAS: COINCIDEN</span>
      </header>

      <div className="b60-svg-scroll">
        <svg
          role="group"
          aria-label={
            interactive
              ? `Grafo causal de ${layout.boxes.length} nodos; use Tab para recorrerlos y Enter para ver el detalle`
              : `Grafo causal de ${layout.boxes.length} nodos; el detalle de cada nodo está en la tabla siguiente`
          }
          width={layout.width}
          height={layout.height}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          fontFamily={SVG_FONT}
          className="b60-svg"
        >
          <defs>
            <marker id={`${markerPrefix}-ok`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 1 L 10 5 L 0 9 z" fill={SVG_COLOR.edge} />
            </marker>
            <marker id={`${markerPrefix}-halt`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 1 L 10 5 L 0 9 z" fill={SVG_COLOR.edgeHalted} />
            </marker>
            <clipPath id={clipId}>
              <rect width={NODE_WIDTH} height={NODE_HEIGHT} rx={3} />
            </clipPath>
          </defs>

          <g aria-hidden="true">
            {layout.edges.map((edge) => (
              <path
                key={edge.key}
                d={edgePath(edge)}
                fill="none"
                stroke={edge.halted ? SVG_COLOR.edgeHalted : SVG_COLOR.edge}
                strokeWidth={edge.halted ? 1.8 : 1.4}
                strokeDasharray={edge.halted ? "5 4" : undefined}
                markerEnd={`url(#${markerPrefix}-${edge.halted ? "halt" : "ok"})`}
              />
            ))}
          </g>

          {layout.boxes.map(({ node, x, y, depth }) => {
            const palette = STATUS_PALETTE[node.state_status];
            const isSelected = interactive && node.node_id === selectedNodeId;
            const isFocused = interactive && node.node_id === focusedNodeId;
            const body = (
              <>
                <rect
                  width={NODE_WIDTH}
                  height={NODE_HEIGHT}
                  rx={3}
                  fill={isSelected ? SVG_COLOR.nodeFillSelected : SVG_COLOR.nodeFill}
                  stroke={isFocused ? SVG_COLOR.focus : palette.stroke}
                  strokeWidth={isFocused ? 3 : isSelected ? 2 : 1}
                />
                <g clipPath={`url(#${clipId})`}>
                  <rect x={8} y={8} width={NODE_WIDTH - 16} height={18} rx={2} fill={palette.badgeFill} />
                  <text x={14} y={20} fill={palette.stroke} fontSize="10" fontWeight="700">
                    {palette.label}
                  </text>
                  <text x={NODE_WIDTH - 14} y={20} fill={SVG_COLOR.textMuted} fontSize="10" textAnchor="end">
                    {shortHash(node.state_hash, 10, 0)}
                  </text>
                  <text x={12} y={42} fill={SVG_COLOR.text} fontSize="11" fontWeight="600">
                    {node.node_id}
                  </text>
                  <text x={12} y={58} fill={SVG_COLOR.textMuted} fontSize="10">
                    SMT:{node.smt_verified ? "OK" : "NO"} · steps {node.reduction_steps}
                    {node.violation_reason !== null ? " · VIOLATION" : ""}
                  </text>
                </g>
              </>
            );
            if (!interactive) {
              return (
                <g key={node.node_id} role="img" aria-label={nodeAriaLabel(node, depth)} transform={`translate(${x}, ${y})`}>
                  {body}
                </g>
              );
            }
            return (
              <g
                key={node.node_id}
                role="button"
                tabIndex={0}
                aria-pressed={isSelected}
                aria-label={nodeAriaLabel(node, depth)}
                transform={`translate(${x}, ${y})`}
                className="b60-node"
                onClick={() => select(node.node_id)}
                onKeyDown={(event) => onNodeKeyDown(event, node.node_id)}
                onFocus={() => setFocusedNodeId(node.node_id)}
                onBlur={() => setFocusedNodeId((current) => (current === node.node_id ? null : current))}
              >
                {body}
              </g>
            );
          })}
        </svg>
      </div>

      {interactive ? selected !== null && <NodeDetail box={selected} /> : <NodeTable layout={layout} />}
    </section>
  );
}
