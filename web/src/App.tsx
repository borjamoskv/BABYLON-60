import { useState } from 'react';
import { Header } from './components/Header';
import { ParticleCanvas } from './components/ParticleCanvas';
import { AxiomMatrix } from './components/AxiomMatrix';
import { SwarmMonitor } from './components/SwarmMonitor';
import { LedgerInspector } from './components/LedgerInspector';

function App() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="relative w-screen h-screen bg-[#05070a] text-slate-100 flex flex-col overflow-hidden c5-grid-bg">
      {/* Background Topological Particle Mesh */}
      <ParticleCanvas />

      {/* Header Navigation */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content View Container */}
      <main className="flex-1 p-6 overflow-y-auto relative z-10 max-w-7xl mx-auto w-full">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Hero Banner */}
            <div className="glass-panel p-8 relative overflow-hidden">
              <div className="max-w-3xl relative z-10 space-y-3">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono text-xs font-semibold">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  SUBSTRATO DE GOBERNANZA & ATESTACIÓN C5-REAL
                </div>
                <h2 className="text-3xl font-extrabold text-white tracking-tight font-display">
                  BABYLON-60 <span className="text-cyan-400">v4.0.0</span> Sovereign Hardened
                </h2>
                <p className="text-sm text-slate-300 leading-relaxed font-sans">
                  Infraestructura Capa 0 para Agentes IA Verificables y Cumplimiento Regulatorio EU AI Act (Artículos 9–14). Sustituto de alta integridad para bases de datos vectoriales sin linaje causal.
                </p>
                <div className="flex gap-3 pt-2">
                  <button 
                    onClick={() => setActiveTab('axiomas')} 
                    className="px-5 py-2.5 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 rounded-lg text-xs font-mono font-bold text-cyan-300 transition-all shadow-[0_0_15px_rgba(0,240,255,0.2)]"
                  >
                    EXPLORAR 25 AXIOMAS Z3
                  </button>
                  <button 
                    onClick={() => setActiveTab('ledger')} 
                    className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg text-xs font-mono font-semibold text-slate-300 transition-all"
                  >
                    INSPECCIONAR LEDGER WAL
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>VERIFICACIÓN FORMAL</span>
                  <span className="text-emerald-400 font-bold">100% OK</span>
                </div>
                <div className="text-2xl font-bold font-mono text-white">25 / 25 Axiomas Z3</div>
                <p className="text-xs text-slate-400 font-mono">Pruebas en Lean 4 & Z3 SMT Solver satisfechas sin excepciones.</p>
              </div>

              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>SEGURIDAD OPSEC-Ω</span>
                  <span className="text-emerald-400 font-bold">VERDE 🟢</span>
                </div>
                <div className="text-2xl font-bold font-mono text-cyan-300">0 Secretos / 0 CVEs</div>
                <p className="text-xs text-slate-400 font-mono">Gitleaks CI/CD + 14 CVEs de Dependabot remediadas en main.</p>
              </div>

              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>ORQUESTACIÓN ENJAMBRE</span>
                  <span className="text-amber-400 font-bold">LEGION P×S</span>
                </div>
                <div className="text-2xl font-bold font-mono text-amber-300">100,000 Tenantes</div>
                <p className="text-xs text-slate-400 font-mono">Válvula termodinámica de concurrencia a 5,000 req/sec.</p>
              </div>
            </div>

            {/* Axioms Preview Section */}
            <AxiomMatrix />
          </div>
        )}

        {activeTab === 'axioms' && <AxiomMatrix />}
        {activeTab === 'ledger' && <LedgerInspector />}
        {activeTab === 'swarm' && <SwarmMonitor />}
      </main>

      {/* Subtle Status Footer */}
      <footer className="h-7 px-6 bg-[#030507] border-t border-[var(--border-cyan)] flex items-center justify-between text-[11px] font-mono text-slate-500 z-50">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            C5-REAL ACTIVE
          </span>
          <span>BRANCH: main</span>
          <span>COMMIT: db2bab0a51</span>
        </div>
        <div>
          <span>ISO/IEC EU AI Act Article 9–14 Compliant</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
