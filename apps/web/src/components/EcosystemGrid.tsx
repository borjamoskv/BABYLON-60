import React from 'react';

export const EcosystemGrid: React.FC = () => {
  const frameworks = [
    { name: 'LangChain / LangGraph', desc: 'Middleware de trazabilidad causal en grafos de estado.', icon: '🦜' },
    { name: 'CrewAI / Agno', desc: 'Auditoría de ejecuciones multi-agente en paralelo.', icon: '🐝' },
    { name: 'Microsoft AutoGen', desc: 'Atrapado de excepciones y guardraíles de interacción.', icon: '🤖' },
    { name: 'LlamaIndex', desc: 'Verificación hash-chained de chunks y vectores.', icon: '🦙' },
    { name: 'Model Context Protocol', desc: 'Servidor MCP nativo (`babylon60-mcp`) para Claude.', icon: '🔌' },
    { name: 'OpenAI / Anthropic APIs', desc: 'Intercepción Zero-Trust de payloads de modelos.', icon: '⚡' },
  ];

  return (
    <div className="space-y-6 pt-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-[#27272a] pb-4">
        <div>
          <h3 className="text-sm font-medium text-slate-200 tracking-tight flex items-center gap-2">
            Ecosystem Interoperability
            <span className="px-1.5 py-0.5 rounded-sm bg-[#18181b] border border-[#27272a] text-[9px] text-emerald-500 font-mono tracking-widest uppercase">
              Universal Wrapper
            </span>
          </h3>
          <p className="text-xs text-slate-500 mt-1 font-mono tracking-wide">
            Plug-and-play causal traceability middleware compatible with any AI stack.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {frameworks.map((fw, idx) => (
          <div 
            key={idx} 
            className="group flex flex-col p-5 bg-[#111111] border border-[#27272a] rounded-2xl hover:bg-[#18181b] hover:border-[#3f3f46] transition-all duration-300"
          >
            <div className="flex items-center gap-3 mb-3">
              <span className="flex items-center justify-center w-8 h-8 rounded bg-[#18181b] border border-[#27272a] text-sm group-hover:scale-110 transition-transform">
                {fw.icon}
              </span>
              <span className="text-xs font-mono text-slate-200 tracking-tight">
                {fw.name}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-mono leading-relaxed mt-auto">
              {fw.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
