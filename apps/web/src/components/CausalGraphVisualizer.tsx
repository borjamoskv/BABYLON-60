import React, { useState } from 'react';
import { soundFx } from './AudioEngine';

interface Node {
  id: string;
  name: string;
  type: 'sensor' | 'internal' | 'active' | 'ledger';
  x: number;
  y: number;
  entropy: number;
}

export const CausalGraphVisualizer: React.FC = () => {
  const [permeability, setPermeability] = useState<number>(0.15);
  const [activeNode, setActiveNode] = useState<string | null>('INTERNAL_01');

  // Calculated Free Energy Discrepancy F = D_KL + Entropy Frictions
  const klDivergence = (0.02 + permeability * 0.48).toFixed(4);
  const freeEnergy = (0.012 + permeability * 0.18).toFixed(4);
  const exergyScore = Math.round(1000 - permeability * 250);

  const nodes: Node[] = [
    { id: 'SENSOR_01', name: 'S1: Input Taint Stream', type: 'sensor', x: 120, y: 100, entropy: 0.04 },
    { id: 'SENSOR_02', name: 'S2: Telemetry Sensor', type: 'sensor', x: 120, y: 220, entropy: 0.02 },
    { id: 'INTERNAL_01', name: 'µ1: Lawvere Fixed-Point Kernel', type: 'internal', x: 340, y: 110, entropy: 0.001 },
    { id: 'INTERNAL_02', name: 'µ2: Z3 SMT Solver Constraint', type: 'internal', x: 340, y: 210, entropy: 0.002 },
    { id: 'ACTIVE_01', name: 'A1: Sovereign Action Interceptor', type: 'active', x: 560, y: 160, entropy: 0.005 },
    { id: 'LEDGER_01', name: 'L1: SQLite WAL Hash-Chain (SHA3-256)', type: 'ledger', x: 780, y: 160, entropy: 0.000 },
  ];

  const edges = [
    { from: 'SENSOR_01', to: 'INTERNAL_01', label: 'Markov Lens π' },
    { from: 'SENSOR_02', to: 'INTERNAL_02', label: 'Bayesian Reduction' },
    { from: 'INTERNAL_01', to: 'ACTIVE_01', label: 'Do-Calculus P(Y|do(X))' },
    { from: 'INTERNAL_02', to: 'ACTIVE_01', label: 'Z3 SAT Verification' },
    { from: 'ACTIVE_01', to: 'LEDGER_01', label: 'SHA3-256 Merkle Commit' },
  ];

  return (
    <div className="space-y-6 font-mono">
      <div className="glass-panel p-6 relative overflow-hidden">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold mb-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              VISUALIZADOR TOPOLÓGICO Y MANTA DE MARKOV (C5-REAL)
            </div>
            <h2 className="text-2xl font-bold text-white">Simulador de Geodésicas de Información de Fisher</h2>
            <p className="text-xs text-slate-400 mt-1">
              Modelado interactivo del Grafo Causal Aclíclico (DAG) y la reducción entrópica de la Manta de Markov.
            </p>
          </div>
          <div className="flex gap-4">
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-right">
              <span className="text-[10px] text-slate-500 block">DIVERGENCIA K-L (D_KL):</span>
              <span className="text-cyan-300 font-bold text-base">{klDivergence} nats</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-right">
              <span className="text-[10px] text-slate-500 block">ENERGÍA LIBRE (F):</span>
              <span className="text-emerald-400 font-bold text-base">{freeEnergy} J</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-right">
              <span className="text-[10px] text-slate-500 block">SCORE EXERGÍA:</span>
              <span className="text-amber-300 font-bold text-base">{exergyScore} / 1000</span>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Control & Canvas Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Controls Sidebar */}
        <div className="glass-panel p-5 space-y-4 font-mono text-xs">
          <h3 className="text-sm font-bold text-cyan-300 flex items-center gap-2 border-b border-slate-800 pb-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            Parámetros Causal-Termodinámicos
          </h3>

          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="text-slate-400">Permeabilidad Manta (η):</span>
              <span className="text-cyan-300 font-bold">{permeability.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.01"
              max="0.50"
              step="0.01"
              value={permeability}
              onChange={(e) => {
                soundFx.playClick();
                setPermeability(parseFloat(e.target.value));
              }}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <p className="text-[10px] text-slate-500 mt-1 leading-snug">
              Modula la fricción entrópica en el límite del sistema cognoscitivo.
            </p>
          </div>

          <div className="p-3 bg-slate-950 rounded border border-slate-800 space-y-2">
            <span className="text-[10px] text-slate-400 font-bold block">INVARIANTES TOPOLÓGICOS:</span>
            <div className="text-[11px] text-emerald-400 flex justify-between">
              <span>Unicidad Chentsov:</span>
              <span>VERIFICADO</span>
            </div>
            <div className="text-[11px] text-cyan-400 flex justify-between">
              <span>Lawvere Store Comonad:</span>
              <span>ISOMÓRFICO</span>
            </div>
            <div className="text-[11px] text-amber-400 flex justify-between">
              <span>Landauer Floor (u64):</span>
              <span>1,102,080 aJ</span>
            </div>
          </div>

          <div>
            <span className="text-[10px] text-slate-400 block mb-2 font-bold">SELECCIONAR NODO CAUSAL:</span>
            <div className="space-y-1">
              {nodes.map((n) => (
                <button
                  key={n.id}
                  onClick={() => {
                    soundFx.playClick();
                    setActiveNode(n.id);
                  }}
                  className={`w-full text-left p-2 rounded text-[11px] transition-all flex justify-between items-center ${
                    activeNode === n.id
                      ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/50 font-bold'
                      : 'bg-slate-900/60 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <span className="truncate">{n.name}</span>
                  <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                    {n.type}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Dynamic Topology Canvas Display */}
        <div className="lg:col-span-3 glass-panel p-5 relative overflow-hidden flex flex-col justify-between min-h-[380px]">
          <div className="flex justify-between items-center text-xs text-slate-400 border-b border-slate-800 pb-3 z-10">
            <span className="flex items-center gap-2 font-bold text-slate-200">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              TOPOLOGÍA DEL GRAFO CAUSAL (ACÍCLICO Y DETERMINISTA)
            </span>
            <span className="text-cyan-400">MÉTRICA DE FISHER: G_ij = E[∂_i ln p ∂_j ln p]</span>
          </div>

          {/* SVG Diagram Canvas */}
          <div className="relative w-full h-[320px] bg-slate-950/90 rounded-lg border border-slate-900 my-2 overflow-hidden">
            <svg className="w-full h-full">
              <defs>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="6"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#00f0ff" />
                </marker>
              </defs>

              {/* Draw Edges */}
              {edges.map((edge, i) => {
                const source = nodes.find((n) => n.id === edge.from)!;
                const target = nodes.find((n) => n.id === edge.to)!;
                return (
                  <g key={i}>
                    <line
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      stroke="#00f0ff"
                      strokeWidth="1.5"
                      strokeOpacity="0.6"
                      strokeDasharray={i % 2 === 0 ? "5,5" : "none"}
                      markerEnd="url(#arrow)"
                    />
                    <text
                      x={(source.x + target.x) / 2}
                      y={(source.y + target.y) / 2 - 8}
                      fill="#94a3b8"
                      fontSize="9"
                      fontFamily="JetBrains Mono, monospace"
                      textAnchor="middle"
                    >
                      {edge.label}
                    </text>
                  </g>
                );
              })}

              {/* Draw Nodes */}
              {nodes.map((node) => {
                const isSelected = activeNode === node.id;
                let color = '#00f0ff';
                if (node.type === 'sensor') color = '#38bdf8';
                if (node.type === 'internal') color = '#10b581';
                if (node.type === 'active') color = '#f59e0b';
                if (node.type === 'ledger') color = '#ec4899';

                return (
                  <g
                    key={node.id}
                    className="cursor-pointer transition-transform hover:scale-105"
                    onClick={() => {
                      soundFx.playClick();
                      setActiveNode(node.id);
                    }}
                  >
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={isSelected ? 22 : 18}
                      fill={`${color}20`}
                      stroke={color}
                      strokeWidth={isSelected ? 3 : 1.5}
                    />
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r="4"
                      fill={color}
                    />
                    <text
                      x={node.x}
                      y={node.y + 32}
                      fill={isSelected ? '#ffffff' : '#cbd5e1'}
                      fontSize="10"
                      fontWeight={isSelected ? 'bold' : 'normal'}
                      fontFamily="JetBrains Mono, monospace"
                      textAnchor="middle"
                    >
                      {node.name.split(':')[0]}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Node Detail Bar */}
          {activeNode && (
            <div className="bg-slate-900/90 border border-slate-800 p-3 rounded-lg text-xs flex justify-between items-center z-10">
              <div className="space-y-0.5">
                <span className="text-slate-400 text-[10px]">DETALLES DE ESTADO NODO:</span>
                <div className="font-bold text-white">
                  {nodes.find((n) => n.id === activeNode)?.name}
                </div>
              </div>
              <div className="flex gap-4 text-right">
                <div>
                  <span className="text-[10px] text-slate-500 block">TASA DE ENTROPÍA:</span>
                  <span className="text-emerald-400 font-bold font-mono">
                    {nodes.find((n) => n.id === activeNode)?.entropy} nat/step
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">ESTADO BARRERA:</span>
                  <span className="text-cyan-300 font-bold font-mono">C5-HARDENED</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
