import { useState } from 'react';
import { Header } from './components/Header';
import { ParticleCanvas } from './components/ParticleCanvas';
import { TerminalHero } from './components/TerminalHero';
import { AxiomMatrix } from './components/AxiomMatrix';
import { SwarmMonitor } from './components/SwarmMonitor';
import { LedgerInspector } from './components/LedgerInspector';
import { LicensePortal } from './components/LicensePortal';
import { ComplianceInspector } from './components/ComplianceInspector';
import { soundFx } from './components/AudioEngine';

function App() {
  const [activeTab, setActiveTab] = useState('overview');

  const handleCTA = (tab: string) => {
    soundFx.playClick();
    setActiveTab(tab);
  };

  return (
    <div className="relative w-screen h-screen bg-[#030508] text-slate-100 flex flex-col overflow-hidden c5-grid-bg">
      {/* Background Topological Particle Canvas */}
      <ParticleCanvas />

      {/* Header Navigation */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content View Container */}
      <main className="flex-1 p-6 overflow-y-auto relative z-10 max-w-7xl mx-auto w-full space-y-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Hero Banner */}
            <div className="glass-panel p-8 relative overflow-hidden">
              <div className="max-w-4xl relative z-10 space-y-4">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono text-xs font-semibold">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  MOTOR CAUSAL SOBERANO — BABYLON60.COM v4.0.0
                </div>
                <h2 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight font-display leading-tight">
                  Infraestructura Causal Verificable para <span className="text-cyan-400">Agentes de IA</span>
                </h2>
                <p className="text-base text-slate-300 leading-relaxed font-sans max-w-3xl">
                  BABYLON-60 es el motor de atestación criptográfica y gobernanza de cero anergía para sistemas cognitivos autónomos.
                  Sustituye bases de datos vectoriales opacas por un ledger local hash-chained (SHA3-256) con exportador de autoevaluación para el <strong className="text-emerald-400">EU AI Act (Artículos 9–14)</strong>.
                </p>
                <div className="flex flex-wrap gap-3 pt-2">
                  <button 
                    onClick={() => handleCTA('compliance')} 
                    className="px-6 py-3 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/50 rounded-xl text-xs font-mono font-bold text-emerald-300 transition-all shadow-[0_0_20px_rgba(16,185,129,0.25)]"
                  >
                    🛡️ AUTOEVALUADOR EU AI ACT
                  </button>
                  <button 
                    onClick={() => handleCTA('license')} 
                    className="px-6 py-3 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 rounded-xl text-xs font-mono font-bold text-cyan-300 transition-all shadow-[0_0_20px_rgba(0,240,255,0.25)]"
                  >
                    🔑 GESTOR DE LICENCIAS
                  </button>
                  <button 
                    onClick={() => handleCTA('swarm')} 
                    className="px-6 py-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-xl text-xs font-mono font-semibold text-slate-300 transition-all"
                  >
                    🐝 ENJAMBRE 21 AGENTES
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>CUMPLIMIENTO REGULATORIO</span>
                  <span className="text-emerald-400 font-bold">100% PASS</span>
                </div>
                <div className="text-xl font-bold font-mono text-white">EU AI Act Art. 9–14</div>
                <p className="text-xs text-slate-400 font-mono">Exportador de evidencia en JSON, Markdown y HTML.</p>
              </div>

              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>ORQUESTACIÓN ENJAMBRE</span>
                  <span className="text-cyan-400 font-bold">2.47s PASS</span>
                </div>
                <div className="text-xl font-bold font-mono text-cyan-300">21 Agentes P×S</div>
                <p className="text-xs text-slate-400 font-mono">Auditoría paralela de distribuciones Python, Rust y Docker.</p>
              </div>

              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>DISTRIBUCIÓN FIRMADA</span>
                  <span className="text-emerald-400 font-bold font-mono">OIDC & COSIGN</span>
                </div>
                <div className="text-xl font-bold font-mono text-white">PyPI + Crates + GHCR</div>
                <p className="text-xs text-slate-400 font-mono">Firmas Sigstore/SLSA y contenedores multi-arch Cosign.</p>
              </div>

              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>LICENCIAMIENTO</span>
                  <span className="text-amber-400 font-bold font-mono">HMAC-SHA256</span>
                </div>
                <div className="text-xl font-bold font-mono text-amber-300">Enterprise Ready</div>
                <p className="text-xs text-slate-400 font-mono">Verificación soberana offline en $BABYLON60_LICENSE_KEY.</p>
              </div>
            </div>

            {/* CLI Playground Terminal Hero */}
            <TerminalHero />

            {/* Pricing Tiers Grid */}
            <div className="space-y-4 pt-2">
              <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                Planes y Licenciamiento Comercial (babylon60.com)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono">
                {/* Developer */}
                <div className="glass-panel p-6 space-y-4 border-slate-800 hover:border-slate-700">
                  <div className="text-xs text-cyan-400 font-bold">DEVELOPER / COMMUNITY</div>
                  <div className="text-3xl font-extrabold text-white">$0 <span className="text-xs font-normal text-slate-400">/ gratis</span></div>
                  <p className="text-xs text-slate-400">Para investigadores y proyectos Open Source bajo licencia Apache-2.0 / MIT.</p>
                  <ul className="text-xs text-slate-300 space-y-2">
                    <li>✅ Acceso al Kernel Rust & Python API</li>
                    <li>✅ 25 Axiomas Z3 & Pruebas Lean 4</li>
                    <li>✅ SQLite Tamper-Evident Ledger local (SHA3-256)</li>
                    <li>❌ Soporte SLAs Enterprise</li>
                  </ul>
                </div>

                {/* Professional */}
                <div className="glass-panel p-6 space-y-4 border-cyan-500/50 shadow-[0_0_20px_rgba(0,240,255,0.15)] relative overflow-hidden">
                  <div className="absolute top-3 right-3 px-2 py-0.5 bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 rounded text-[10px] font-bold">
                    MÁS POPULAR
                  </div>
                  <div className="text-xs text-cyan-300 font-bold">STARTUP PRO</div>
                  <div className="text-3xl font-extrabold text-white">$499 <span className="text-xs font-normal text-slate-400">/ mes</span></div>
                  <p className="text-xs text-slate-400">Para startups desplegando agentes autónomos en producción.</p>
                  <ul className="text-xs text-slate-300 space-y-2">
                    <li>✅ Todo lo de Developer</li>
                    <li>✅ Certificador EU AI Act (HTML/JSON)</li>
                    <li>✅ Servidor MCP `babylon60-mcp`</li>
                    <li>✅ Firma HMAC Comercial</li>
                  </ul>
                  <button onClick={() => handleCTA('license')} className="w-full py-2.5 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 rounded-lg text-cyan-300 text-xs font-bold transition-all">
                    OBTENER LICENCIA PRO
                  </button>
                </div>

                {/* Sovereign Enterprise */}
                <div className="glass-panel p-6 space-y-4 border-emerald-500/40">
                  <div className="text-xs text-emerald-400 font-bold">SOVEREIGN ENTERPRISE</div>
                  <div className="text-3xl font-extrabold text-white">CUSTOM <span className="text-xs font-normal text-slate-400">/ On-Premise</span></div>
                  <p className="text-xs text-slate-400">Para corporaciones y entidades gubernamentales que requieren aislamiento total.</p>
                  <ul className="text-xs text-slate-300 space-y-2">
                    <li>✅ Despliegue Soberano Air-Gapped</li>
                    <li>✅ Auditoría de Seguridad OPSEC-Ω</li>
                    <li>✅ Orquestación Legion 100k Tenantes</li>
                    <li>✅ SLA 99.999% & Soporte 24/7</li>
                  </ul>
                  <button onClick={() => handleCTA('license')} className="w-full py-2.5 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 rounded-lg text-emerald-300 text-xs font-bold transition-all">
                    CONTACTAR ENTERPRISE
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'compliance' && <ComplianceInspector />}
        {activeTab === 'license' && <LicensePortal />}
        {activeTab === 'swarm' && <SwarmMonitor />}
        {activeTab === 'axioms' && <AxiomMatrix />}
        {activeTab === 'ledger' && <LedgerInspector />}
      </main>

      {/* Status Footer */}
      <footer className="h-7 px-6 bg-[#030507] border-t border-[var(--border-cyan)] flex items-center justify-between text-[11px] font-mono text-slate-500 z-50">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            BABYLON60.COM ONLINE
          </span>
          <span>RELEASE: v4.0.0</span>
          <span>21 AGENTS: PASS</span>
        </div>
        <div>
          <span>ISO/IEC EU AI Act Article 9–14 Certified</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
