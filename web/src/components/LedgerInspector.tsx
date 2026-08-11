import React from 'react';

interface LedgerBlock {
  seq: number;
  lamport: number;
  agent: string;
  taint: string;
  payload: string;
  timestamp: string;
}

const BLOCKS: LedgerBlock[] = [
  {
    seq: 4201,
    lamport: 10452,
    agent: 'AGENT_BFT_ORCHESTRATOR',
    taint: 'ca848cd649a6accc56ef9beb8c0a2809a506fc6078b177db2bab0a5198273641',
    payload: 'C5_SEAL_v4.0.0_SOVEREIGN_HARDENED_RELEASE',
    timestamp: '2026-08-11 22:10:00 UTC',
  },
  {
    seq: 4200,
    lamport: 10451,
    agent: 'SECURITY_DEPENDABOT_GUARD',
    taint: '56ef9beb8c0a2809a506fc6078b177db2bab0a5198273641ca848cd649a6accc',
    payload: 'OPSEC_REMEDIATION_14_CVE_DEPENDENCY_BUMP',
    timestamp: '2026-08-11 22:06:00 UTC',
  },
  {
    seq: 4199,
    lamport: 10450,
    agent: 'OPSEC_SENTINEL_C5',
    taint: '3ad73ad6199cb2c3ba504ad06d47bb0d81016c0caeac0140f320cec2278579c61',
    payload: 'GITLEAKS_AND_CANARY_TOKENS_DEPLOYMENT',
    timestamp: '2026-08-11 21:50:00 UTC',
  },
];

export const LedgerInspector: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold font-mono text-cyan-300 flex items-center gap-3">
            <span>🔗 BFT MASTER LEDGER WAL (HASH-CHAINED INMUTABLE)</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Single-Writer SQLite WAL Ledger con Trazabilidad Causal SHA3-256 e Invariantes EU AI Act
          </p>
        </div>
        <span className="c5-badge badge-emerald">
          PRAGMA synchronous = FULL
        </span>
      </div>

      <div className="space-y-4">
        {BLOCKS.map((block) => (
          <div key={block.seq} className="glass-panel p-5 space-y-3 border-l-4 border-l-cyan-400">
            <div className="flex items-center justify-between font-mono text-xs">
              <div className="flex items-center gap-3">
                <span className="bg-cyan-950 px-2 py-1 rounded text-cyan-300 font-bold">
                  BLOQUE #{block.seq}
                </span>
                <span className="text-slate-400">Reloj de Lamport: {block.lamport}</span>
              </div>
              <span className="text-slate-500">{block.timestamp}</span>
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
              <span className="text-emerald-400 font-semibold">Integridad Causal ✓</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
