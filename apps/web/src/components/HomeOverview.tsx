import { TerminalHero } from './TerminalHero';
import { HeroCodeSnippet } from './HeroCodeSnippet';
import { EcosystemGrid } from './EcosystemGrid';
import { RoadmapMatrix } from './RoadmapMatrix';
import { SexagesimalExploit } from './SexagesimalExploit';
import { BabylonHistory } from './BabylonHistory';

interface HomeOverviewProps {
  handleCTA: (tab: string) => void;
}

export function HomeOverview({ handleCTA }: HomeOverviewProps) {
  return (
    <div className="space-y-16 pb-20">
      {/* Cold Open Hero - High-Exergy Epistemic Manifesto */}
      <div className="border border-slate-800 bg-[#05070c] p-8 lg:p-14 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-6 opacity-10 text-[80px] lg:text-[120px] font-mono select-none pointer-events-none text-slate-400">
           ৬০
        </div>
        
        <div className="max-w-4xl space-y-6 relative z-10">
          <div className="inline-flex items-center gap-3 text-amber-500 font-mono text-xs uppercase tracking-[0.25em]">
            <span className="w-2 h-2 bg-amber-500 block animate-pulse" />
            EL PECADO DEL SISTEMA DECIMAL // 4.000 AÑOS DESPUÉS
          </div>

          <h2 className="text-3xl md:text-5xl lg:text-6xl font-light text-slate-100 tracking-tight leading-tight">
            Contamos en base 10 por <span className="font-normal text-amber-400">pereza anatómica</span>.<br />
            Los ordenadores pagan el precio.
          </h2>

          <p className="text-sm md:text-base text-slate-300 font-mono max-w-3xl leading-relaxed">
            El sistema decimal es un accidente biológico de 10 dedos. Al forzar la computación 
            moderna a modelar el tiempo en fracciones flotantes (<span className="text-red-400">IEEE 754</span>), 
            los agentes autónomos de IA acumulan deriva matemática invisible, rompiendo la causalidad 
            y la auditoría legal.
          </p>

          <p className="text-xs md:text-sm text-cyan-400 font-mono max-w-3xl">
            <strong>BABYLON-60</strong> es el retorno al sistema sexagesimal mesopotámico: 
            aritmética exacta <strong>F60</strong>, ledger BFT inmutable y verificación formal en Lean 4. 
            Cero aproximación. Cero deriva.
          </p>

          <div className="flex flex-wrap gap-4 pt-4">
            <button 
              onClick={() => handleCTA('causal')} 
              className="px-6 py-3 bg-cyan-950/40 border border-cyan-700 hover:border-cyan-400 hover:text-white text-xs font-mono text-cyan-300 transition-all cursor-pointer shadow-[0_0_15px_rgba(6,182,212,0.2)]"
            >
              [ GRAFO CAUSAL DETERMINISTA ]
            </button>
            <button 
              onClick={() => handleCTA('compliance')} 
              className="px-6 py-3 bg-emerald-950/30 border border-emerald-900 hover:border-emerald-700 text-xs font-mono text-emerald-400 transition-all cursor-pointer"
            >
              [ AUDITORÍA EU AI ACT ART. 9–14 ]
            </button>
            <button 
              onClick={() => handleCTA('thermo')} 
              className="px-6 py-3 bg-transparent border border-slate-700 hover:border-slate-400 hover:text-white text-xs font-mono text-slate-300 transition-all cursor-pointer"
            >
              [ FÍSICA TERMODINÁMICA ]
            </button>
            <button 
              onClick={() => handleCTA('blog')} 
              className="px-6 py-3 bg-transparent border border-slate-700 hover:border-slate-400 hover:text-white text-xs font-mono text-slate-300 transition-all cursor-pointer"
            >
              [ MANIFIESTO C5-REAL ]
            </button>
          </div>
        </div>
      </div>

      {/* 1. Live Interactive Exploit: Demonstrating the Flaw of Float Arithmetic */}
      <SexagesimalExploit />

      {/* 2. Mesopotamian Archaeology: The 12 Phalanges Story */}
      <BabylonHistory />

      {/* Quick Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'DIVISIBILIDAD F60', value: '12 FACTORES', title: 'Aritmética Exacta', desc: 'Sin decimales periódicos en cuotas de tiempo.', color: 'text-amber-400' },
          { label: 'AUTO-EVALUACIÓN', value: '100% PASS', title: 'EU AI Act Art. 9–14', desc: 'Evidencia criptográfica inmutable WORM.', color: 'text-emerald-400' },
          { label: 'ORQUESTACIÓN', value: '2.47s PASS', title: 'Enjambre 21 Agentes', desc: 'Auditoría paralela de exergía en Rust/Python.', color: 'text-cyan-400' },
          { label: 'DISTRIBUCIÓN', value: 'CRATE & PYPI', title: 'Soberanía Técnica', desc: 'Kernel local-first con proofs en Lean 4.', color: 'text-slate-200' },
        ].map((metric, i) => (
          <div key={i} className="border border-slate-800 p-6 space-y-4 hover:border-slate-600 transition-colors bg-[#05070a]">
            <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 uppercase tracking-widest">
              <span>{metric.label}</span>
              <span className={`${metric.color} font-bold`}>{metric.value}</span>
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

      {/* Sovereign Architecture & Deployment Models (No fake pricing cards) */}
      <div className="space-y-8 pt-12 border-t border-slate-800">
        <div className="flex flex-wrap justify-between items-end gap-4">
          <div>
            <h3 className="text-xs font-mono text-slate-400 uppercase tracking-[0.2em]">
              // Arquitectura y Modelos de Despliegue Soberano
            </h3>
            <p className="text-xs text-slate-500 font-mono mt-1">
              Sin telemetría en la nube. Sin dependencias externas de Silicon Valley. Local-First.
            </p>
          </div>
          <span className="text-[10px] font-mono text-cyan-400 border border-cyan-900 bg-cyan-950/40 px-3 py-1">
            VERIFICACIÓN FORMAL LEAN 4
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Open Source / Developer */}
          <div className="border border-slate-800 bg-[#06080d] p-8 space-y-6">
            <div className="text-[10px] text-cyan-400 font-mono tracking-[0.2em]">DESARROLLADOR / RESEARCH</div>
            <div className="text-2xl font-mono text-white">OPEN SOURCE</div>
            <p className="text-xs text-slate-400 font-mono leading-relaxed h-12">
              Para investigadores matemáticos y desarrolladores de agentes deterministas.
            </p>
            <ul className="text-xs text-slate-400 font-mono space-y-3 border-t border-slate-800 pt-6">
              <li className="flex items-center gap-2 text-slate-300">
                <span className="text-cyan-400">✔</span> Kernel Rust `#![no_std]` & Python SDK
              </li>
              <li className="flex items-center gap-2 text-slate-300">
                <span className="text-cyan-400">✔</span> Aritmética Sexagesimal F60
              </li>
              <li className="flex items-center gap-2 text-slate-300">
                <span className="text-cyan-400">✔</span> 25 Axiomas C5 formalizados en Z3
              </li>
              <li className="flex items-center gap-2 text-slate-300">
                <span className="text-cyan-400">✔</span> Ledger DAG Tamper-Evident SQLite
              </li>
            </ul>
            <div className="pt-2 font-mono text-xs text-cyan-300 bg-slate-900 p-2.5 border border-slate-800 rounded">
              <code>cargo add babylon60-kernel</code>
            </div>
          </div>

          {/* EU AI Act Compliance */}
          <div className="border border-emerald-900 bg-emerald-950/10 p-8 space-y-6 relative">
            <div className="text-[10px] text-emerald-400 font-mono tracking-[0.2em]">LEGALTECH & COMPLIANCE</div>
            <div className="text-2xl font-mono text-white">AUTO-EVALUADOR</div>
            <p className="text-xs text-slate-400 font-mono leading-relaxed h-12">
              Exportador de auto-evaluación verificable para el Reglamento UE 2024/1689.
            </p>
            <ul className="text-xs text-emerald-100/70 font-mono space-y-3 border-t border-emerald-900/50 pt-6">
              <li className="flex items-center gap-2 text-emerald-300">
                <span className="text-emerald-400">✔</span> Auditoría Artículos 9, 10, 11, 12, 14
              </li>
              <li className="flex items-center gap-2 text-emerald-300">
                <span className="text-emerald-400">✔</span> Exportación en JSON / Markdown / HTML
              </li>
              <li className="flex items-center gap-2 text-emerald-300">
                <span className="text-emerald-400">✔</span> Servidor MCP para integración con IDEs
              </li>
              <li className="flex items-center gap-2 text-emerald-300">
                <span className="text-emerald-400">✔</span> Firma Criptográfica de Linaje de Datos
              </li>
            </ul>
            <div className="pt-2 font-mono text-xs text-emerald-300 bg-slate-900 p-2.5 border border-slate-800 rounded">
              <code>babylon60-compliance --format html</code>
            </div>
          </div>

          {/* Air-Gapped Sovereign Enterprise */}
          <div className="border border-slate-800 bg-[#06080d] p-8 space-y-6">
            <div className="text-[10px] text-amber-400 font-mono tracking-[0.2em]">DEFENSA & CRITICAL INFRA</div>
            <div className="text-2xl font-mono text-white">AIR-GAPPED SOVEREIGN</div>
            <p className="text-xs text-slate-400 font-mono leading-relaxed h-12">
              Aislamiento total y gobernanza determinista en hardware soberano dedicado.
            </p>
            <ul className="text-xs text-slate-400 font-mono space-y-3 border-t border-slate-800 pt-6">
              <li className="flex items-center gap-2 text-slate-300">
                <span className="text-amber-400">✔</span> Despliegue en red aislada sin acceso a internet
              </li>
              <li className="flex items-center gap-2 text-slate-300">
                <span className="text-amber-400">✔</span> Enjambre P×S de alta concurrencia
              </li>
              <li className="flex items-center gap-2 text-slate-300">
                <span className="text-amber-400">✔</span> Atestación Criptográfica L5 en Bitcoin
              </li>
              <li className="flex items-center gap-2 text-slate-300">
                <span className="text-amber-400">✔</span> Consultoría de Arquitectura de Sistemas
              </li>
            </ul>
            <div className="pt-2">
              <button 
                onClick={() => handleCTA('license')}
                className="block text-center w-full py-2.5 border border-amber-800 hover:border-amber-500 bg-amber-950/20 text-amber-300 text-xs font-mono uppercase tracking-wider transition-colors cursor-pointer"
              >
                [ GESTIÓN DE LICENCIAS & CLAVES ]
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
