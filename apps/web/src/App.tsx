import { useState } from 'react';
import { Header } from './components/Header';
import { ParticleCanvas } from './components/ParticleCanvas';
import { AxiomMatrix } from './components/AxiomMatrix';
import { SwarmMonitor } from './components/SwarmMonitor';
import { LedgerInspector } from './components/LedgerInspector';
import { LicensePortal } from './components/LicensePortal';
import { ComplianceInspector } from './components/ComplianceInspector';

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
            {/* Hero Commercial Banner */}
            <div className="glass-panel p-8 relative overflow-hidden">
              <div className="max-w-3xl relative z-10 space-y-4">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono text-xs font-semibold">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  INFRAESTRUCTURA CAPA 0 PARA AGENTES IA VERIFICABLES — BABYLON60.COM
                </div>
                <h2 className="text-4xl font-extrabold text-white tracking-tight font-display">
                  BABYLON-60 <span className="text-cyan-400">v4.0.0</span> Sovereign Hardened
                </h2>
                <p className="text-sm text-slate-300 leading-relaxed font-sans">
                  El substrato criptográfico determinista de ultra-alta exergía para agentes de IA autónomos.
                  Gobernanza C5-REAL, prueba Z3 SMT, auditoría BFT append-only y cumplimiento automático del <strong className="text-emerald-400">EU AI Act (Artículos 9–14)</strong>.
                </p>
                <div className="flex flex-wrap gap-3 pt-2">
                  <button 
                    onClick={() => setActiveTab('compliance')} 
                    className="px-5 py-2.5 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/50 rounded-lg text-xs font-mono font-bold text-emerald-300 transition-all shadow-[0_0_15px_rgba(16,185,129,0.2)]"
                  >
                    🛡️ CERTIFICADO EU AI ACT
                  </button>
                  <button 
                    onClick={() => setActiveTab('license')} 
                    className="px-5 py-2.5 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 rounded-lg text-xs font-mono font-bold text-cyan-300 transition-all shadow-[0_0_15px_rgba(0,240,255,0.2)]"
                  >
                    🔑 PORTAL DE LICENCIAS
                  </button>
                  <button 
                    onClick={() => setActiveTab('swarm')} 
                    className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg text-xs font-mono font-semibold text-slate-300 transition-all"
                  >
                    🐝 ENJAMBRE DE 21 AGENTES
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>CUMPLIMIENTO REGULATORIO</span>
                  <span className="text-emerald-400 font-bold">100% PASS</span>
                </div>
                <div className="text-xl font-bold font-mono text-white">EU AI Act Art. 9–14</div>
                <p className="text-xs text-slate-400 font-mono">Certificado de auditoría automatizado en JSON, Markdown y HTML.</p>
              </div>

              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>ENJAMBRE 21 AGENTES</span>
                  <span className="text-cyan-400 font-bold">2.47s PASS</span>
                </div>
                <div className="text-xl font-bold font-mono text-cyan-300">7 Escuadrones P×S</div>
                <p className="text-xs text-slate-400 font-mono">Auditoría paralela de distribuciones Python, Rust, Docker y MCP.</p>
              </div>

              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>DISTRIBUCIÓN SOTA</span>
                  <span className="text-emerald-400 font-bold">SIGNED</span>
                </div>
                <div className="text-xl font-bold font-mono text-white">PyPI + Crates + GHCR</div>
                <p className="text-xs text-slate-400 font-mono">Firmas Sigstore/SLSA y contenedores multi-arch Cosign.</p>
              </div>

              <div className="glass-panel p-6 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span>LICENCIAMIENTO</span>
                  <span className="text-amber-400 font-bold">ENTERPRISE</span>
                </div>
                <div className="text-xl font-bold font-mono text-amber-300">HMAC-SHA256</div>
                <p className="text-xs text-slate-400 font-mono">Firma criptográfica soberana en $BABYLON60_LICENSE_KEY.</p>
              </div>
            </div>

            {/* Quick Install Terminal */}
            <div className="glass-panel p-6 font-mono space-y-3">
              <div className="flex justify-between items-center text-xs text-slate-400 border-b border-slate-800 pb-2">
                <span className="text-slate-200 font-bold">💻 INSTALACIÓN RÁPIDA & AUDITORÍA CLI</span>
                <span className="text-cyan-400 text-[11px]">VERSION 4.0.0</span>
              </div>
              <div className="bg-slate-950 p-4 rounded border border-slate-800 text-xs space-y-2 text-cyan-300">
                <div className="flex items-center gap-2">
                  <span className="text-slate-500"># Instalar paquete firmado desde PyPI</span>
                </div>
                <code>pip install babylon60</code>

                <div className="flex items-center gap-2 pt-2">
                  <span className="text-slate-500"># Generar certificado de cumplimiento EU AI Act</span>
                </div>
                <code>babylon60-compliance --bundle artifact_bundle_v3 --format html --output cert.html</code>

                <div className="flex items-center gap-2 pt-2">
                  <span className="text-slate-500"># Generar llave de licencia enterprise</span>
                </div>
                <code>babylon60-license generate --owner "AcmeCorp" --tier enterprise --days 365</code>
              </div>
            </div>

            {/* Pricing Tiers Grid */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                Niveles de Licenciamiento Comercial (babylon60.com)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono">
                {/* Developer */}
                <div className="glass-panel p-6 space-y-4 border-slate-800 hover:border-slate-700">
                  <div className="text-xs text-cyan-400 font-bold">DEVELOPER / COMMUNITY</div>
                  <div className="text-3xl font-extrabold text-white">$0 <span className="text-xs font-normal text-slate-400">/ para siempre</span></div>
                  <p className="text-xs text-slate-400">Para investigadores y proyectos Open Source bajo licencia Apache-2.0 / MIT.</p>
                  <ul className="text-xs text-slate-300 space-y-2">
                    <li>✅ Acceso al Kernel Rust & Python API</li>
                    <li>✅ 25 Axiomas Z3 & Pruebas Lean 4</li>
                    <li>✅ SQLite BFT Ledger local</li>
                    <li>❌ Soporte SLAs Enterprise</li>
                  </ul>
                </div>

                {/* Professional */}
                <div className="glass-panel p-6 space-y-4 border-cyan-500/50 shadow-[0_0_20px_rgba(0,240,255,0.15)] relative overflow-hidden">
                  <div className="absolute top-3 right-3 px-2 py-0.5 bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 rounded text-[10px] font-bold">
                    RECOMENDADO
                  </div>
                  <div className="text-xs text-cyan-300 font-bold">PROFESSIONAL STARTUP</div>
                  <div className="text-3xl font-extrabold text-white">$499 <span className="text-xs font-normal text-slate-400">/ mes</span></div>
                  <p className="text-xs text-slate-400">Para startups desplegando agentes autónomos en producción.</p>
                  <ul className="text-xs text-slate-300 space-y-2">
                    <li>✅ Todo lo de Developer</li>
                    <li>✅ Certificador EU AI Act (HTML/JSON)</li>
                    <li>✅ Servidor MCP `babylon60-mcp`</li>
                    <li>✅ Firma HMAC Comercial</li>
                  </ul>
                  <button onClick={() => setActiveTab('license')} className="w-full py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 rounded text-cyan-300 text-xs font-bold transition-all">
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
                  <button onClick={() => setActiveTab('license')} className="w-full py-2 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 rounded text-emerald-300 text-xs font-bold transition-all">
                    CONTACTAR ENTERPRISE
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'compliance' && <ComplianceInspector />}
        {activeTab === 'license' && <LicensePortal />}
        {activeTab === 'axioms' && <AxiomMatrix />}
        {activeTab === 'ledger' && <LedgerInspector />}
        {activeTab === 'swarm' && <SwarmMonitor />}
      </main>

      {/* Status Footer */}
      <footer className="h-7 px-6 bg-[#030507] border-t border-[var(--border-cyan)] flex items-center justify-between text-[11px] font-mono text-slate-500 z-50">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            BABYLON60.COM ONLINE
          </span>
          <span>RELEASE: v4.0.0</span>
          <span>STATUS: 21 AGENTS PASS</span>
        </div>
        <div>
          <span>ISO/IEC EU AI Act Article 9–14 Certified</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
