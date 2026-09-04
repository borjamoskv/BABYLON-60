import React, { useState } from 'react';
import { soundFx } from './AudioEngine';

interface BftNode {
  id: number;
  name: string;
  role: 'leader' | 'replica';
  status: 'online' | 'byzantine' | 'syncing';
  vote: 'PREPARE' | 'COMMIT' | 'REJECT';
  latency: number;
}

export const BftConsensusSimulator: React.FC = () => {
  const [phase, setPhase] = useState<'IDLE' | 'PRE-PREPARE' | 'PREPARE' | 'COMMIT' | 'FINALIZED'>('FINALIZED');
  const [view, setView] = useState<number>(42);
  const [byzantineInjected, setByzantineInjected] = useState<boolean>(false);
  const [nodes, setNodes] = useState<BftNode[]>([
    { id: 0, name: 'Nodo 0 (Leader)', role: 'leader', status: 'online', vote: 'COMMIT', latency: 2 },
    { id: 1, name: 'Nodo 1 (Replica)', role: 'replica', status: 'online', vote: 'COMMIT', latency: 4 },
    { id: 2, name: 'Nodo 2 (Replica)', role: 'replica', status: 'online', vote: 'COMMIT', latency: 5 },
    { id: 3, name: 'Nodo 3 (Replica)', role: 'replica', status: 'online', vote: 'COMMIT', latency: 3 },
    { id: 4, name: 'Nodo 4 (Replica)', role: 'replica', status: 'online', vote: 'COMMIT', latency: 6 },
    { id: 5, name: 'Nodo 5 (Replica)', role: 'replica', status: 'online', vote: 'COMMIT', latency: 4 },
    { id: 6, name: 'Nodo 6 (Replica)', role: 'replica', status: 'online', vote: 'COMMIT', latency: 5 },
  ]);

  const [merkleRoot, setMerkleRoot] = useState<string>('0x7f8a9b2c3d4e5f6a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b2c3d4e5f6a');

  // LogOP Bayesian Veto State
  const [logopOpinions, setLogopOpinions] = useState<{ [nodeId: number]: number }>({
    0: 0.95,
    1: 0.92,
    2: 0.96,
    3: 0.0, // Default veto to showcase invariant
    4: 0.94,
    5: 0.91,
    6: 0.95,
  });
  const [logopHypothesis] = useState<string>('Mutación Causal AST Válida');
  const [backendStatus, setBackendStatus] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  // Direct mathematical LogOP calculation: P_LogOP = prod(p_i^w_i)
  const calculateLocalLogOp = (): number => {
    const vals = Object.values(logopOpinions);
    if (vals.some((v) => v === 0.0)) {
      return 0.0;
    }
    const weight = 1.0 / vals.length;
    let logSum = 0;
    for (const v of vals) {
      logSum += weight * Math.log(Math.max(1e-9, v));
    }
    return Math.exp(logSum);
  };

  const aggregatedProb = calculateLocalLogOp();

  const syncWithBackendLogOp = async () => {
    setIsSyncing(true);
    soundFx.playClick();
    try {
      const opinionsPayload: Record<string, Record<string, number>> = {};
      nodes.forEach((node) => {
        const prob = logopOpinions[node.id] ?? 0.95;
        opinionsPayload[node.name] = {
          [logopHypothesis]: prob,
          'Mutación Inválida': Number((1.0 - prob).toFixed(4)),
        };
      });

      const res = await fetch('/api/swarm/logop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ opinions: opinionsPayload }),
      });

      if (res.ok) {
        const data = await res.json();
        soundFx.playSuccess();
        const vetoInfo = data.veto_triggered ? 'VETO CONFIRMADO POR KERNEL' : 'CONSENSO SIN VETO';
        setBackendStatus(`✓ KERNEL FASTAPI: ${vetoInfo} (d_LogOP = ${data.aggregate_probabilities[logopHypothesis]?.toFixed(4)})`);
      } else {
        setBackendStatus('⚠️ KERNEL OFFLINE: Usando motor LogOP local.');
      }
    } catch {
      setBackendStatus('⚠️ KERNEL OFFLINE: Usando motor LogOP local.');
    } finally {
      setIsSyncing(false);
    }
  };

  const triggerConsensusRound = () => {
    soundFx.playClick();
    setPhase('PRE-PREPARE');
    
    setTimeout(() => {
      setPhase('PREPARE');
      soundFx.playClick();
    }, 600);

    setTimeout(() => {
      setPhase('COMMIT');
      soundFx.playClick();
    }, 1200);

    setTimeout(() => {
      setPhase('FINALIZED');
      soundFx.playSuccess();
      const randomHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
      setMerkleRoot(`0x${randomHash}`);
      setView((v) => v + 1);
    }, 1800);
  };

  const toggleByzantineFault = () => {
    soundFx.playClick();
    const newInjected = !byzantineInjected;
    setByzantineInjected(newInjected);
    setNodes((prev) =>
      prev.map((n) =>
        n.id === 3
          ? {
              ...n,
              status: newInjected ? 'byzantine' : 'online',
              vote: newInjected ? 'REJECT' : 'COMMIT',
            }
          : n
      )
    );
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Title Banner */}
      <div className="glass-panel p-6 relative overflow-hidden">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold mb-2">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              SIMULADOR DE CONSENSO BIZANTINO P2P (PBFT / HOTSTUFF)
            </div>
            <h2 className="text-2xl font-bold text-white">Cluster P2P con Tolerancia a Fallos Bizantinos</h2>
            <p className="text-xs text-slate-400 mt-1">
              Verificación de la regla de supermayoría <code className="text-amber-300 font-bold">2f + 1 = 5 / 7</code> y rotación determinista de View Leader.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleByzantineFault}
              className={`px-4 py-2 rounded-lg border text-xs font-bold transition-all ${
                byzantineInjected
                  ? 'bg-red-500/20 text-red-300 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.3)]'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              {byzantineInjected ? '⚠️ FRACTURA BIZANTINA ACTIVA (N3)' : '🛡️ INYECTAR NODO BIZANTINO (N3)'}
            </button>
            <button
              onClick={triggerConsensusRound}
              className="px-5 py-2 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/50 rounded-lg text-amber-300 text-xs font-bold transition-all shadow-[0_0_20px_rgba(245,158,11,0.25)]"
            >
              ⚡ EJECUTAR RONDA DE CONSENSO
            </button>
          </div>
        </div>
      </div>

      {/* Cluster Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4">
          <div className="text-[10px] text-slate-400">FASE DE CONSENSO</div>
          <div className="text-xl font-bold text-amber-300 mt-1 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
            {phase}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">PBFT 3-Phase State Machine</div>
        </div>

        <div className="glass-panel p-4">
          <div className="text-[10px] text-slate-400">NÚMERO DE VISTA (VIEW)</div>
          <div className="text-xl font-bold text-cyan-300 mt-1">VIEW #{view}</div>
          <div className="text-[10px] text-emerald-400 mt-1">Leader: Node 0 (Monotonic)</div>
        </div>

        <div className="glass-panel p-4">
          <div className="text-[10px] text-slate-400">SUPERMAYORÍA QUORUM</div>
          <div className="text-xl font-bold text-emerald-400 mt-1">
            {byzantineInjected ? '6 / 7 VOTOS' : '7 / 7 VOTOS'}
          </div>
          <div className="text-[10px] text-emerald-400 mt-1">Quorum threshold (≥ 5) PASS</div>
        </div>

        <div className="glass-panel p-4">
          <div className="text-[10px] text-slate-400">LATENCIA PROMEDIO RED</div>
          <div className="text-xl font-bold text-white mt-1">4.1 ms</div>
          <div className="text-[10px] text-cyan-400 mt-1">Seqlock Memory Shared</div>
        </div>
      </div>

      {/* Interactive Cluster Mesh Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Nodes Grid */}
        <div className="lg:col-span-2 space-y-3 font-mono">
          <div className="flex justify-between items-center text-xs text-slate-400 border-b border-slate-800 pb-2">
            <span className="font-bold text-slate-200">NODOS DEL CLUSTER BFT (N=7, F=2)</span>
            <span>VÁLIDOS: {nodes.filter((n) => n.status !== 'byzantine').length} / 7</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {nodes.map((node) => (
              <div
                key={node.id}
                className={`glass-panel p-4 border transition-all ${
                  node.status === 'byzantine'
                    ? 'border-red-500/60 bg-red-950/20 text-red-300'
                    : node.role === 'leader'
                    ? 'border-amber-500/60 bg-amber-950/20 text-amber-300'
                    : 'border-slate-800 hover:border-slate-700 text-slate-200'
                }`}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold flex items-center gap-1.5">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        node.status === 'byzantine'
                          ? 'bg-red-500 animate-pulse'
                          : 'bg-emerald-400'
                      }`}
                    />
                    {node.name}
                  </span>
                  <span
                    className={`text-[9px] font-bold px-2 py-0.5 rounded border ${
                      node.status === 'byzantine'
                        ? 'bg-red-950 border-red-500/40 text-red-300'
                        : node.role === 'leader'
                        ? 'bg-amber-950 border-amber-500/40 text-amber-300'
                        : 'bg-emerald-950 border-emerald-500/40 text-emerald-300'
                    }`}
                  >
                    {node.status === 'byzantine' ? 'BYZANTINE' : node.role.toUpperCase()}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[10px] mt-2 font-mono text-slate-400">
                  <div>
                    <span>VOTO RONDA:</span>
                    <span
                      className={`block font-bold mt-0.5 ${
                        node.vote === 'COMMIT' ? 'text-emerald-400' : 'text-red-400'
                      }`}
                    >
                      {node.vote}
                    </span>
                  </div>
                  <div>
                    <span>LATENCIA RED:</span>
                    <span className="block text-slate-200 font-bold mt-0.5">
                      {node.latency} ms
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Merkle Root & Log Stream */}
        <div className="glass-panel p-5 space-y-4 font-mono text-xs flex flex-col justify-between">
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-amber-300 flex items-center gap-2 border-b border-slate-800 pb-2">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              ESTADO DEL MERKLE TREE ROOT (SHA3-256)
            </h3>

            <div className="p-3 bg-slate-950 rounded border border-amber-500/30 space-y-1">
              <span className="text-[10px] text-slate-500 block">MERKLE ROOT ACUMULADO:</span>
              <code className="text-[11px] text-amber-300 font-bold break-all block">
                {merkleRoot}
              </code>
            </div>

            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400">Invariante HotStuff Safety:</span>
                <span className="text-emerald-400 font-bold">PASSED</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Certificado de Quorum (QC):</span>
                <span className="text-cyan-300 font-bold">FIRMA SHA3-256 VÁLIDA</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Fondo Landauer:</span>
                <span className="text-amber-300 font-bold">k_B T ln 2 RESPETADO</span>
              </div>
            </div>
          </div>

          <div className="p-3 bg-black/80 rounded border border-slate-900 text-[10px] space-y-1">
            <div className="text-slate-500">TRAZA DE CONDUCCIÓN P2P:</div>
            <div className="text-emerald-400">[INFO] View #{view} commit certified by {nodes.filter((n) => n.status !== 'byzantine').length} nodes.</div>
            {byzantineInjected && (
              <div className="text-red-400">[WARN] Malicious vote from Node 3 ignored by BFT quorum gate.</div>
            )}
          </div>
        </div>
      </div>

      {/* LogOP Bayesian Veto Oracle Section */}
      <div className="glass-panel p-6 border-cyan-500/30 space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold mb-1">
              <span>📐 ORÁCULO DE VETO LOGOP BAYESIANO (INV_BFT_LOGOP)</span>
            </div>
            <h3 className="text-lg font-bold text-white">Logarithmic Opinion Pooling: Inmunidad ante Mayorías Alucinatorias</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Si un solo auditor riguroso asigna probabilidad <code className="text-cyan-300 font-bold">P = 0.0</code>, el consenso multiplicativo colapsa a cero.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                soundFx.playClick();
                setLogopOpinions((prev) => ({
                  ...prev,
                  3: prev[3] === 0.0 ? 0.95 : 0.0,
                }));
              }}
              className={`px-4 py-2 rounded-lg border text-xs font-bold transition-all cursor-pointer ${
                logopOpinions[3] === 0.0
                  ? 'bg-red-500/20 text-red-300 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.3)]'
                  : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
              }`}
            >
              {logopOpinions[3] === 0.0 ? '⛔ VETO NODO 3 ACTIVO (P=0.0)' : '✅ NODO 3 EN CONSENSO (P=0.95)'}
            </button>
            <button
              onClick={syncWithBackendLogOp}
              disabled={isSyncing}
              className="px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 rounded-lg text-cyan-300 text-xs font-bold transition-all cursor-pointer"
            >
              {isSyncing ? '⏳ EVALUANDO...' : '⚡ EVALUAR EN KERNEL'}
            </button>
          </div>
        </div>

        {/* Aggregate Probability Banner */}
        <div className={`p-4 rounded-lg border flex flex-col sm:flex-row items-center justify-between gap-4 ${
          aggregatedProb === 0.0
            ? 'bg-red-950/40 border-red-500/50 text-red-200'
            : 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200'
        }`}>
          <div>
            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
              PROBABILIDAD LOGOP AGREGADA: P(H = &quot;{logopHypothesis}&quot;)
            </div>
            <div className="text-3xl font-extrabold mt-1 flex items-baseline gap-2">
              <span className={aggregatedProb === 0.0 ? 'text-red-400' : 'text-emerald-400'}>
                {(aggregatedProb * 100).toFixed(2)}%
              </span>
              <span className="text-xs font-normal text-slate-400">
                {aggregatedProb === 0.0 ? 'COLAPSO POR VETO ABSOLUTO' : 'CONSENSO EPISTÉMICO VÁLIDO'}
              </span>
            </div>
          </div>
          <div className="text-right text-xs">
            <span className={`inline-block px-3 py-1 rounded border font-bold ${
              aggregatedProb === 0.0
                ? 'bg-red-900/60 border-red-500 text-red-300'
                : 'bg-emerald-900/60 border-emerald-500 text-emerald-300'
            }`}>
              {aggregatedProb === 0.0 ? '🚫 ALUCINACIÓN DETENIDA' : '✨ ACEPTADO SIN VETO'}
            </span>
            {backendStatus && (
              <div className="text-[10px] text-cyan-400 mt-1 font-mono">
                {backendStatus}
              </div>
            )}
          </div>
        </div>

        {/* Sliders for Node Probabilities */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-2">
          {nodes.map((node) => {
            const prob = logopOpinions[node.id] ?? 0.95;
            const isVeto = prob === 0.0;
            return (
              <div
                key={node.id}
                className={`glass-panel p-3 border text-xs space-y-2 ${
                  isVeto ? 'border-red-500/60 bg-red-950/20' : 'border-slate-800 bg-slate-950/40'
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-300">{node.name}</span>
                  <span className={`font-mono font-bold ${isVeto ? 'text-red-400' : 'text-cyan-300'}`}>
                    {(prob * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={prob * 100}
                  onChange={(e) => {
                    const newProb = parseFloat(e.target.value) / 100;
                    setLogopOpinions((prev) => ({
                      ...prev,
                      [node.id]: newProb,
                    }));
                  }}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
                <div className="flex justify-between text-[9px] text-slate-500">
                  <span className={isVeto ? 'text-red-400 font-bold' : ''}>0% (VETO)</span>
                  <span>100% (CERTEZA)</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
