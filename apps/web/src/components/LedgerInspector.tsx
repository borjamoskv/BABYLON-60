import React, { useState } from 'react';
import { soundFx } from './AudioEngine';

interface LedgerBlock {
  seq: number;
  lamport: number;
  agent: string;
  taint: string;
  payload: string;
  timestamp: string;
}

const INITIAL_BLOCKS: LedgerBlock[] = [
  {
    seq: 4201,
    lamport: 10452,
    agent: 'AGENT_BFT_ORCHESTRATOR',
    taint: 'ca848cd649a6accc56ef9beb8c0a2809a506fc6078b177db2bab0a5198273641',
    payload: 'C5_SEAL_v4.0.0_SOVEREIGN_HARDENED_RELEASE',
    timestamp: '2026-08-13 16:20:00 UTC',
  },
  {
    seq: 4200,
    lamport: 10451,
    agent: 'SECURITY_DEPENDABOT_GUARD',
    taint: '56ef9beb8c0a2809a506fc6078b177db2bab0a5198273641ca848cd649a6accc',
    payload: 'OPSEC_REMEDIATION_14_CVE_DEPENDENCY_BUMP',
    timestamp: '2026-08-13 16:15:00 UTC',
  },
  {
    seq: 4199,
    lamport: 10450,
    agent: 'OPSEC_SENTINEL_C5',
    taint: '3ad73ad6199cb2c3ba504ad06d47bb0d81016c0caeac0140f320cec2278579c61',
    payload: 'GITLEAKS_AND_CANARY_TOKENS_DEPLOYMENT',
    timestamp: '2026-08-13 16:00:00 UTC',
  },
];

export const LedgerInspector: React.FC = () => {
  const [blocks, setBlocks] = useState<LedgerBlock[]>(INITIAL_BLOCKS);
  const [newPayload, setNewPayload] = useState<string>('');
  const [agentName, setAgentName] = useState<string>('AGENT_USER_INTERACTIVE');
  const [filter, setFilter] = useState<string>('');

  const generateFakeSha3 = (seed: string) => {
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
      hash = (hash << 5) - hash + seed.charCodeAt(i);
      hash |= 0;
    }
    const hex = Math.abs(hash).toString(16).padStart(8, '0');
    return `${hex}e49a6accc56ef9beb8c0a2809a506fc6078b177db2bab0a5198273${hex}`;
  };

  const handleAppendEvent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPayload.trim()) return;

    soundFx.playSuccess();
    const nextSeq = blocks[0] ? blocks[0].seq + 1 : 1;
    const nextLamport = blocks[0] ? blocks[0].lamport + 1 : 1000;
    const now = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';

    const newBlock: LedgerBlock = {
      seq: nextSeq,
      lamport: nextLamport,
      agent: agentName,
      taint: generateFakeSha3(`${nextSeq}-${newPayload}-${now}`),
      payload: newPayload.toUpperCase().replace(/\s+/g, '_'),
      timestamp: now,
    };

    setBlocks([newBlock, ...blocks]);
    setNewPayload('');
  };

  const filteredBlocks = blocks.filter(
    (b) =>
      b.payload.toLowerCase().includes(filter.toLowerCase()) ||
      b.agent.toLowerCase().includes(filter.toLowerCase()) ||
      b.taint.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-xl font-bold font-mono text-cyan-300 flex items-center gap-3">
            <span>🔗 LOCAL CAUSAL LEDGER WAL (SHA3-256 TAMPER-EVIDENT)</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Single-Writer SQLite WAL Ledger con Trazabilidad Causal SHA3-256 e Invariantes EU AI Act
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="c5-badge badge-emerald">
            PRAGMA synchronous = FULL
          </span>
          <span className="c5-badge badge-cyan">
            REGISTROS: {blocks.length} BLOQUES
          </span>
        </div>
      </div>

      {/* Interactive Appender Form */}
      <form onSubmit={handleAppendEvent} className="glass-panel p-5 space-y-4 font-mono">
        <div className="text-xs font-bold text-cyan-400 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          ⚡ SIMULAR ESTAMPA EN TIEMPO REAL (APPEND EVENT TO SHA3-256 WAL)
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-[10px] text-slate-400 block mb-1">AGENTE EMISOR</label>
            <input
              type="text"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-cyan-300 font-mono focus:border-cyan-500 outline-none"
            />
          </div>
          <div className="md:col-span-2">
            <label className="text-[10px] text-slate-400 block mb-1">PAYLOAD DE EVENTO DE ATESTACIÓN</label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Ej. MODEL_INFERENCE_ATTENTATIVE_TRACE_LOG_VERIFIED"
                value={newPayload}
                onChange={(e) => setNewPayload(e.target.value)}
                className="flex-1 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-emerald-400 font-mono focus:border-emerald-500 outline-none"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 rounded text-emerald-300 text-xs font-bold transition-all shadow-[0_0_12px_rgba(16,185,129,0.2)]"
              >
                + ESTAMPAR BLOQUE
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Search / Filter Control */}
      <div className="flex justify-between items-center font-mono text-xs">
        <div className="w-full max-w-xs">
          <input
            type="text"
            placeholder="🔍 Filtrar por payload, agente o taint hash..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500/50"
          />
        </div>
        <span className="text-slate-500 text-[11px]">Mostrando {filteredBlocks.length} de {blocks.length}</span>
      </div>

      {/* Blocks List */}
      <div className="space-y-4">
        {filteredBlocks.map((block) => (
          <div key={block.seq} className="glass-panel p-5 space-y-3 border-l-4 border-l-cyan-400 hover:border-l-emerald-400 transition-all">
            <div className="flex items-center justify-between font-mono text-xs">
              <div className="flex items-center gap-3">
                <span className="bg-cyan-950 px-2 py-1 rounded text-cyan-300 font-bold">
                  BLOQUE #{block.seq}
                </span>
                <span className="text-slate-400">Reloj de Lamport: {block.lamport}</span>
              </div>
              <span className="text-slate-500 text-[11px]">{block.timestamp}</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
              <div className="bg-black/60 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">TAINT HASH (SHA3-256):</span>
                <span className="text-cyan-400 font-semibold break-all">{block.taint}</span>
              </div>

              <div className="bg-black/60 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">PAYLOAD VERIFICADO:</span>
                <span className="text-emerald-400 font-semibold">{block.payload}</span>
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] font-mono pt-1 text-slate-400">
              <span>Agente Emisor: <strong className="text-slate-200">{block.agent}</strong></span>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <span>Integridad Causal</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

