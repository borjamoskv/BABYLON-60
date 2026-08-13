import React from 'react';

export const RoadmapMatrix: React.FC = () => {
  const steps = [
    {
      step: 'Escalón 1',
      title: 'Kernel Nativo Rust & Seqlock',
      status: 'PRODUCCIÓN (100% PASS)',
      statusColor: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10',
      desc: 'Motor de memoria lock-free en Rust (PyO3 FFI), SharedManifest y 377 tests unitarios.'
    },
    {
      step: 'Escalón 2',
      title: 'EU AI Act Self-Assessment Exporter',
      status: 'PRODUCCIÓN (100% PASS)',
      statusColor: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10',
      desc: 'Exportador de evidencias de autoevaluación (Artículos 9–14) en JSON, HTML y Markdown.'
    },
    {
      step: 'Escalón 3',
      title: 'Local Causal Hash-Chained Ledger',
      status: 'PRODUCCIÓN (ACTUAL)',
      statusColor: 'text-cyan-400 border-cyan-500/40 bg-cyan-500/10',
      desc: 'Single-Writer SQLite WAL con trazabilidad causal SHA3-256 y testigos Git a posteriori.'
    },
    {
      step: 'Escalón 4',
      title: 'Global P2P BFT Consensus Cluster',
      status: 'HOJA DE RUTA (EN DESARROLLO)',
      statusColor: 'text-amber-400 border-amber-500/40 bg-amber-500/10',
      desc: 'Consenso distribuido P2P multimodelo y tolerancia a fallos bizantinos en red soberana.'
    }
  ];

  return (
    <div className="glass-panel p-6 space-y-4 font-mono">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            HOJA DE RUTA & MATRIZ DE EVOLUCIÓN (TRANSPARENCIA TOTAL)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Diferenciación estricta entre capacidades actuales de producción y desarrollos de red futuros
          </p>
        </div>
        <span className="c5-badge badge-cyan text-[10px]">
          C5-REAL AUDITED
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {steps.map((st, idx) => (
          <div key={idx} className="p-4 bg-slate-950/80 border border-slate-800 rounded-lg space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-cyan-400">{st.step}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${st.statusColor}`}>
                {st.status}
              </span>
            </div>
            <div className="font-bold text-white text-sm">{st.title}</div>
            <p className="text-slate-400 text-[11px] leading-snug">{st.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
