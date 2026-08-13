import React from 'react';

export const EcosystemGrid: React.FC = () => {
  const frameworks = [
    { name: 'LangChain / LangGraph', desc: 'Middleware de trazabilidad causal en grafos de estado', icon: '🦜' },
    { name: 'CrewAI / Agno', desc: 'Auditoría de ejecuciones multi-agente en paralelo', icon: '🐝' },
    { name: 'Microsoft AutoGen', desc: 'Atrapado de excepciones y guardraíles de interacción', icon: '🤖' },
    { name: 'LlamaIndex', desc: 'Verificación hash-chained de chunks y vectores recuperados', icon: '🦙' },
    { name: 'Model Context Protocol (MCP)', desc: 'Servidor MCP nativo (`babylon60-mcp`) para Claude / Antigravity', icon: '🔌' },
    { name: 'OpenAI / Anthropic APIs', desc: 'Intercepción Zero-Trust de payloads de modelos LLM', icon: '⚡' },
  ];

  return (
    <div className="glass-panel p-6 space-y-4 font-mono">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-bold text-cyan-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            INTEROPERABILIDAD Y ECOSISTEMA ABIERTO
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Middleware de trazabilidad causal plug-and-play compatible con cualquier stack de IA
          </p>
        </div>
        <span className="c5-badge badge-cyan text-[10px]">
          UNIVERSAL WRAPPER
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
        {frameworks.map((fw, idx) => (
          <div key={idx} className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg hover:border-cyan-500/40 transition-all space-y-1">
            <div className="flex items-center gap-2 font-bold text-slate-200">
              <span className="text-base">{fw.icon}</span>
              <span>{fw.name}</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">{fw.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
