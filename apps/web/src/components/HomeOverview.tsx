import { TerminalHero } from './TerminalHero';
import { HeroCodeSnippet } from './HeroCodeSnippet';
import { EcosystemGrid } from './EcosystemGrid';
import { RoadmapMatrix } from './RoadmapMatrix';

interface HomeOverviewProps {
  handleCTA: (tab: string) => void;
}

export function HomeOverview({ handleCTA }: HomeOverviewProps) {
  return (
    <div className="space-y-16 pb-16">
      {/* Hero Banner - Minimalist */}
      <div className="border border-slate-800 p-8 lg:p-12">
        <div className="max-w-4xl space-y-6">
          <div className="inline-flex items-center gap-3 text-cyan-500 font-mono text-xs uppercase tracking-[0.2em]">
            <span className="w-1 h-1 bg-cyan-500 block" />
            Sovereign Causal Engine — BABYLON60.COM v4.0.0
          </div>
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-light text-slate-100 tracking-tight leading-tight">
            Verifiable Causal Infrastructure for <span className="font-medium text-cyan-400">AI Agents</span>.
          </h2>
          <p className="text-sm text-slate-400 font-mono max-w-2xl leading-relaxed">
            BABYLON-60 replaces opaque vector databases with a local hash-chained ledger (SHA3-256) 
            and provides a self-evaluation exporter for the EU AI Act (Articles 9–14). 
            Zero anergy architecture.
          </p>
          <div className="flex flex-wrap gap-4 pt-6">
            <button 
              onClick={() => handleCTA('blog')} 
              className="px-6 py-3 bg-transparent border border-slate-700 hover:border-slate-400 hover:text-white text-xs font-mono text-slate-300 transition-colors"
            >
              [ BLOG EXÉRGICO ]
            </button>
            <button 
              onClick={() => handleCTA('compliance')} 
              className="px-6 py-3 bg-emerald-950/30 border border-emerald-900 hover:border-emerald-700 text-xs font-mono text-emerald-400 transition-colors"
            >
              [ AUTOEVALUADOR EU AI ACT ]
            </button>
            <button 
              onClick={() => handleCTA('license')} 
              className="px-6 py-3 bg-transparent border border-slate-700 hover:border-slate-400 hover:text-white text-xs font-mono text-slate-300 transition-colors"
            >
              [ GESTOR DE LICENCIAS ]
            </button>
            <button 
              onClick={() => handleCTA('swarm')} 
              className="px-6 py-3 bg-transparent border border-slate-700 hover:border-slate-400 hover:text-white text-xs font-mono text-slate-300 transition-colors"
            >
              [ ENJAMBRE 21 AGENTES ]
            </button>
          </div>
        </div>
      </div>

      {/* Quick Metrics Cards - Minimalist */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'AUTO-EVALUACIÓN', value: '100% PASS', title: 'EU AI Act Art. 9–14', desc: 'Evidencia en JSON/Markdown/HTML.', color: 'text-emerald-400' },
          { label: 'ORQUESTACIÓN', value: '2.47s PASS', title: '21 Agentes P×S', desc: 'Auditoría paralela Python/Rust.', color: 'text-cyan-400' },
          { label: 'DISTRIBUCIÓN', value: 'PyPI & SRC', title: 'babylon60', desc: 'Paquete PyPI y código fuente local.', color: 'text-slate-200' },
          { label: 'LICENCIAMIENTO', value: 'TOKEN VERIFY', title: 'Enterprise Ready', desc: 'Verificación offline soberana.', color: 'text-amber-400' },
        ].map((metric, i) => (
          <div key={i} className="border border-slate-800 p-6 space-y-4 hover:border-slate-600 transition-colors">
            <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 uppercase tracking-widest">
              <span>{metric.label}</span>
              <span className={`${metric.color}`}>{metric.value}</span>
            </div>
            <div className="text-lg font-mono text-slate-200">{metric.title}</div>
            <p className="text-xs text-slate-400 font-mono">{metric.desc}</p>
          </div>
        ))}
      </div>

      <TerminalHero />
      <HeroCodeSnippet />
      <EcosystemGrid />
      <RoadmapMatrix />

      {/* Pricing Tiers Grid - Minimalist */}
      <div className="space-y-8 pt-12 border-t border-slate-800">
        <h3 className="text-xs font-mono text-slate-400 uppercase tracking-[0.2em]">
          // Planes y Licenciamiento Comercial
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Developer */}
          <div className="border border-slate-800 p-8 space-y-6">
            <div className="text-[10px] text-cyan-500 font-mono tracking-[0.2em]">DEVELOPER / COMMUNITY</div>
            <div className="text-3xl font-mono text-white">$0 <span className="text-xs text-slate-500">/ gratis</span></div>
            <p className="text-xs text-slate-400 font-mono leading-relaxed h-12">Proyectos Open Source bajo licencia Apache-2.0 / MIT.</p>
            <ul className="text-xs text-slate-500 font-mono space-y-4 border-t border-slate-800 pt-6">
              <li>+ Kernel Rust & Python API</li>
              <li>+ 25 Axiomas Z3 & Pruebas Lean 4</li>
              <li>+ SQLite Tamper-Evident Ledger</li>
              <li className="text-slate-700 opacity-50">- Soporte SLAs Enterprise</li>
            </ul>
          </div>

          {/* Professional */}
          <div className="border border-cyan-900 bg-cyan-950/10 p-8 space-y-6 relative">
            <div className="absolute top-0 right-0 bg-cyan-900 text-cyan-100 text-[10px] px-3 py-1 font-mono uppercase tracking-widest">
              Popular
            </div>
            <div className="text-[10px] text-cyan-400 font-mono tracking-[0.2em]">STARTUP PRO</div>
            <div className="text-3xl font-mono text-white">$499 <span className="text-xs text-slate-500">/ mes</span></div>
            <p className="text-xs text-slate-400 font-mono leading-relaxed h-12">Para startups desplegando agentes autónomos en producción.</p>
            <ul className="text-xs text-cyan-100/70 font-mono space-y-4 border-t border-cyan-900/50 pt-6">
              <li>+ Todo lo de Developer</li>
              <li>+ Generador Auto-Evaluación AI Act</li>
              <li>+ Servidor MCP babylon60-mcp</li>
              <li>+ Firma Criptográfica Comercial</li>
            </ul>
            <div className="pt-4">
              <a href="https://buy.stripe.com/aFaeVe2nq9G666v9hx3ks00" target="_blank" rel="noopener noreferrer" className="block text-center w-full py-3 bg-cyan-900 hover:bg-cyan-800 text-cyan-50 text-xs font-mono uppercase tracking-widest transition-colors">
                Obtener Licencia Pro
              </a>
            </div>
          </div>

          {/* Sovereign Enterprise */}
          <div className="border border-slate-800 p-8 space-y-6">
            <div className="text-[10px] text-emerald-500 font-mono tracking-[0.2em]">SOVEREIGN ENTERPRISE</div>
            <div className="text-3xl font-mono text-white">CUSTOM <span className="text-xs text-slate-500">/ on-premise</span></div>
            <p className="text-xs text-slate-400 font-mono leading-relaxed h-12">Aislamiento total para corporaciones y gobiernos.</p>
            <ul className="text-xs text-slate-500 font-mono space-y-4 border-t border-slate-800 pt-6">
              <li>+ Despliegue Soberano Air-Gapped</li>
              <li>+ Auditoría de Seguridad OPSEC-Ω</li>
              <li>+ Orquestación Legion 100k Tenantes</li>
              <li>+ SLA 99.999% & Soporte 24/7</li>
            </ul>
            <div className="pt-4">
              <a href="mailto:sales@babylon60.com?subject=BABYLON-60%20Sovereign%20Enterprise" className="block text-center w-full py-3 border border-slate-700 hover:border-slate-500 text-slate-300 text-xs font-mono uppercase tracking-widest transition-colors">
                Contactar Enterprise
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
