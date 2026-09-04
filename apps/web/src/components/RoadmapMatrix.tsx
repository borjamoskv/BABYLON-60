import React from 'react';

export const RoadmapMatrix: React.FC = () => {
  const steps = [
    {
      step: '01',
      title: 'Native Rust Kernel & Seqlock',
      status: 'PRODUCTION / 100% PASS',
      desc: 'Lock-free memory engine in Rust (PyO3 FFI), SharedManifest, and 377 verified unit tests.'
    },
    {
      step: '02',
      title: 'EU AI Act Self-Assessment Exporter',
      status: 'PRODUCTION / 100% PASS',
      desc: 'Automated evidence exporter for Articles 9–14 in JSON, HTML, and Markdown.'
    },
    {
      step: '03',
      title: 'Local Causal Hash-Chained Ledger',
      status: 'PRODUCTION / CURRENT',
      desc: 'Single-Writer SQLite WAL with SHA3-256 causal traceability and a posteriori Git witnesses.'
    },
    {
      step: '04',
      title: 'Global P2P BFT Consensus Cluster',
      status: 'ROADMAP / RESEARCH',
      desc: 'Multi-model P2P distributed consensus and Byzantine fault tolerance in a sovereign network.'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-[#27272a] pb-4">
        <div>
          <h3 className="text-sm font-medium text-slate-200 tracking-tight flex items-center gap-2">
            Evolution Roadmap
            <span className="px-1.5 py-0.5 rounded-sm bg-[#18181b] border border-[#27272a] text-[9px] text-cyan-500 font-mono tracking-widest uppercase">
              C5-REAL Audited
            </span>
          </h3>
          <p className="text-xs text-slate-500 mt-1 font-mono tracking-wide">
            Strict separation between production capabilities and future network R&D.
          </p>
        </div>
      </div>

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {steps.map((st, idx) => (
          <div 
            key={idx} 
            className="group flex flex-col p-5 bg-[#111111] border border-[#27272a] rounded-2xl hover:bg-[#18181b] hover:border-[#3f3f46] transition-all duration-300"
          >
            <div className="flex justify-between items-start mb-4">
              <span className="text-[10px] font-mono text-cyan-500/50 group-hover:text-cyan-400 transition-colors">
                {st.step}
              </span>
              <span className={`text-[9px] font-mono tracking-widest uppercase ${
                st.status.includes('PRODUCTION') ? 'text-emerald-500/70' : 'text-amber-500/70'
              }`}>
                {st.status}
              </span>
            </div>
            
            <div className="mt-auto space-y-2">
              <h4 className="text-sm font-medium text-slate-200 tracking-tight leading-snug">
                {st.title}
              </h4>
              <p className="text-[11px] text-slate-500 font-mono leading-relaxed">
                {st.desc}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
